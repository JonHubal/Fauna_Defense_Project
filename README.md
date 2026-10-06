Readme

The initial idea is to set up a visual detection for hostile fauna and deploy defense mechanisms for positive identification.  Defense would time out after X delay, while negative detection does NOT trigger a reaction.

The plan is to train the model/camera to identify good and bad fauna.  Configure the Arduino to trigger the motor for "dangerous" fauna and to use Claude for everything because I don't remember anything about how to do any of this.

##Python code slide 83

Labels.txt
0 Background
1 Dangerous
2 Safe

Keras model slide92

The first bottleneck was that the link for TeachableMachine isn't in the slides.  Found it in browser history.
add images, record, train model THEN save it.
download/Tensorflow/Keras

Got the motor built and working on the Arduino with a simple program.

Next bottleneck is there are no instructions for getting a model working with the Arduino.  Just "Claude can help".  To be fair, Claude DID help eventually and it worked the first time, but if it didn't work, troubleshooting would have been extremely difficult.

Changes to the initial idea: The motor turned VERY slowly and the notes warn not to try speeding it up, so my initial plan of using the motor to deploy confetti to scare off Dangerous fauna turned into a visual warning.



If I hadn't been using my personal laptop the entire class so far or if I hadn't been the one to TRAIN the model from our previous in-class work, I wouldn't have been able to complete this assignment.  (I had the previous models saved and the TeachableMachine website in my browser History).

What I asked Claude:
How can I add activating an attached Arduino step motor to the existing code only for "dangerous" and make sure that it is inactive for "Safe"?  It should turn a complete 360 degrees in both directions.
