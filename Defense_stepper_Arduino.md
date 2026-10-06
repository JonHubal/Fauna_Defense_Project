# Fauna_Defense_Project
# For ISU computer class
/*
  defense_stepper

  Waits for a one-word command from the computer over USB, and turns the
  stepper one full revolution clockwise then one full revolution back when it
  receives "spin". Anything else is ignored, so the "Safe" label, which sends
  nothing at all, leaves the motor still.

  Wiring, matching wiring.png:
    Arduino pin 8  -> ULN2003 IN1
    Arduino pin 9  -> ULN2003 IN2
    Arduino pin 10 -> ULN2003 IN3
    Arduino pin 11 -> ULN2003 IN4
    External 5V supply -> ULN2003 power terminals (+ and -)
    Arduino GND -> the supply's - rail, so both share a ground
*/

#include <Stepper.h>

// The 28BYJ-48 has a 64:1 gearbox, so 2048 steps of the library's 4-step
// sequence make one complete turn of the shaft you can see.
const int STEPS_PER_REVOLUTION = 2048;

const int IN1 = 8;
const int IN2 = 9;
const int IN3 = 10;
const int IN4 = 11;

// The Stepper library wants the pins in the order IN1, IN3, IN2, IN4. That
// looks like a typo but it is correct: it is what puts this motor's coils in
// the right firing order.
Stepper motor(STEPS_PER_REVOLUTION, IN1, IN3, IN2, IN4);

void setup() {
  // Must match BAUD_RATE in the Python script.
  Serial.begin(9600);

  // Revolutions per minute. The 28BYJ-48 stalls and buzzes much above 15,
  // so 10 is a safe, reliable speed. One turn takes about 6 seconds.
  motor.setSpeed(10);

  releaseCoils();
  Serial.println("ready");
}

void loop() {
  if (Serial.available() == 0) {
    return;
  }

  // Python sends the word followed by "\n", so read up to the newline.
  String command = Serial.readStringUntil('\n');
  command.trim();

  if (command == "spin") {
    Serial.println("dangerous: deploying");

    motor.step(STEPS_PER_REVOLUTION);   // 360 degrees clockwise
    motor.step(-STEPS_PER_REVOLUTION);  // 360 degrees back again

    // step() blocks until it finishes, so the board is deaf for about 12
    // seconds here. The cooldown on the Python side is longer than that.
    releaseCoils();
    Serial.println("done");
  } else if (command.length() > 0) {
    // Nothing to do. "Safe" never reaches us, but if you add other labels
    // later this tells you the word arrived and was not recognized.
    Serial.println("ignored: " + command);
  }
}

// Stepper leaves the last coil energized, which makes the motor and the driver
// board run hot while sitting still. Turning all four inputs off avoids that.
void releaseCoils() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}
