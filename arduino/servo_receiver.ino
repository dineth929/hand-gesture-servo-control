#include <Servo.h>
Servo motor;

void setup() {
  Serial.begin(9600);
  motor.attach(3);
}
void loop() {
  if (Serial.available() > 0) {
    int angle = Serial.read();
    motor.write(180-angle);
    // use angle here, e.g. servo.write(angle);
  }
}
