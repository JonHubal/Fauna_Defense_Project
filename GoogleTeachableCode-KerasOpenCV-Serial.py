import os
import sys
import time

# Force TensorFlow to use the legacy Keras 2 engine.
# Teachable Machine exports Keras 2 models, which Keras 3 cannot load.
# This must be set before TensorFlow is imported.
os.environ["TF_USE_LEGACY_KERAS"] = "1"

# On macOS, pyarrow (pulled in through pandas) can crash TensorFlow on import
# with "mutex lock failed: Invalid argument". This code does not need pyarrow,
# so block it before TensorFlow loads.
sys.modules["pyarrow"] = None

import cv2
import numpy as np
import serial
from tf_keras.models import load_model

# Find the model and labels next to this script, whatever folder you run it from
HERE = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------------------
# Serial settings
# ----------------------------------------------------------------------

# Which message to send for each label in labels.txt. Keyed by the label's
# name, not its number, so re-training or reordering labels.txt cannot quietly
# aim the motor at the wrong class.
#
# "Dangerous"  -> "spin", and the Arduino turns the stepper one full turn each way
# "Safe"       -> not listed, so nothing is sent and the motor stays still
# "Background" -> not listed, so nothing is sent
MESSAGE_FOR_LABEL = {
    "Dangerous": "spin",
}

# Must match the Serial.begin() number in your Arduino sketch
BAUD_RATE = 9600

# Only act on a prediction the model is fairly sure about, so a blurry frame
# does not flip your device back and forth.
CONFIDENCE_THRESHOLD = 0.80

# The Readme's "defense times out after X delay". After firing, ignore new
# sightings for this long. It has to be longer than the motor takes to run,
# which is about 12 seconds for two turns at 10 RPM, or commands pile up in
# the Arduino's serial buffer while it is busy stepping.
TRIGGER_COOLDOWN_SECONDS = 15

# The port your board is plugged into. Find it in the Arduino IDE under
# Tools > Port. On macOS it looks like "/dev/cu.usbmodem14101", on Windows "COM3".
SERIAL_PORT = "COM3"

# Open the serial port. If it cannot be opened the program still runs, so you
# can test the camera and the model without hardware plugged in.
board = None
try:
    board = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    # Opening the port resets most Arduino boards. Give it time to restart,
    # otherwise the first messages are sent into the void.
    time.sleep(2)
    print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
except serial.SerialException as error:
    print(f"Could not open {SERIAL_PORT}: {error}")
    print("Check Tools > Port in the Arduino IDE, and close the Serial Monitor.")


def send(message):
    """Send one message to the board, followed by a newline."""
    if board is None:
        return
    board.write((message + "\n").encode())
    print(f"Sent: {message}")


# ----------------------------------------------------------------------
# Model, labels, and camera
# ----------------------------------------------------------------------

# Load the model directly using legacy Keras
model = load_model(os.path.join(HERE, "keras_model.h5"), compile=False)

# Load the labels. Each line looks like "0 Background", so keep only the name.
with open(os.path.join(HERE, "labels.txt"), "r") as f:
    class_names = [line.strip().split(" ", 1)[1] for line in f if line.strip()]

# CAMERA can be 0 or 1 based on default camera of your computer
camera = cv2.VideoCapture(0)
if not camera.isOpened():
    sys.exit("Could not open the camera. Try VideoCapture(1), or allow camera access "
             "for your terminal or VS Code in System Settings > Privacy & Security > Camera.")

print("Click the webcam window, then press Esc or q to quit (or Ctrl+C in the terminal).")

# Spinning the motor is a one-shot action, not an on/off state, so instead of
# remembering the last message we remember the earliest time we are allowed to
# fire again. Without this the program would trigger many times per second.
next_trigger_time = 0.0

while True:
    # Grab the webcamera's image.
    ret, frame = camera.read()
    if not ret:
        print("Could not read a frame from the camera.")
        break

    # Crop the center square, like Teachable Machine does, so the image is not squashed
    h, w = frame.shape[:2]
    size = min(h, w)
    top, left = (h - size) // 2, (w - size) // 2
    frame = frame[top:top + size, left:left + size]

    # Resize the square image to (224-height,224-width) pixels
    frame = cv2.resize(frame, (224, 224), interpolation=cv2.INTER_AREA)

    # Show the image in a window
    cv2.imshow("Webcam Image", frame)

    # OpenCV uses BGR color order, but the model was trained on RGB images
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Make the image a numpy array and reshape it to the model's input shape.
    image = np.asarray(image, dtype=np.float32).reshape(1, 224, 224, 3)

    # Normalize the image array to the range -1 to 1
    image = (image / 127.5) - 1

    # Predict. verbose=0 stops Keras from printing a progress bar every frame.
    prediction = model.predict(image, verbose=0)
    index = np.argmax(prediction[0])
    class_name = class_names[index]
    confidence_score = prediction[0][index]

    # Print prediction and confidence score
    print(f"Class: {class_name}   Confidence Score: {confidence_score * 100:.0f} %")

    # Decide what should be sent for this frame. "Safe", "Background", a label
    # we have no message for, or a guess we are not confident about all mean
    # send nothing, which leaves the motor still.
    message = None
    if confidence_score >= CONFIDENCE_THRESHOLD:
        message = MESSAGE_FOR_LABEL.get(class_name)

    # Fire, unless we are still inside the time out from the last sighting
    if message is not None:
        now = time.time()
        if now >= next_trigger_time:
            send(message)
            next_trigger_time = now + TRIGGER_COOLDOWN_SECONDS
        else:
            print(f"  (still timed out for {next_trigger_time - now:.0f} more seconds)")

    # Listen to the keyboard for presses. Esc key (27) or q to exit.
    # The webcam window must be selected (clicked) to receive key presses.
    # "& 0xFF" keeps only the key code, since macOS can add extra bits.
    key = cv2.waitKey(1) & 0xFF
    if key == 27 or key == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
if board is not None:
    board.close()
