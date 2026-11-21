/*
  Radar ultrason - Firmware Arduino (Uno / Nano)
  HC-SR04 : VCC=5V, GND=GND, Trig=D9, Echo=D10
  SG90 (optionnel) : signal=D6, VCC=5V, GND=GND
  Format série (9600 baud) : "angle,distance_cm\n"   (distance = -1 si hors portée)
*/
#include <Servo.h>

const int  TRIG_PIN  = 9;
const int  ECHO_PIN  = 10;
const int  SERVO_PIN = 6;
const bool RADAR_MODE = false;   // true = balayage 0-180° avec servo
const int  STEP_DEG   = 3;       // pas du balayage
const unsigned long TIMEOUT_US = 25000UL; // ~4 m max

Servo servo;
int angle = 90;
int dir = 1;

float mesureDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long t = pulseIn(ECHO_PIN, HIGH, TIMEOUT_US);
  if (t == 0) return -1;                 // pas d'écho
  float d = (t * 0.034) / 2.0;           // d = (t * 0.034) / 2
  if (d < 2 || d > 400) return -1;       // hors specs HC-SR04
  return d;
}

void setup() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  Serial.begin(9600);
  if (RADAR_MODE) {
    servo.attach(SERVO_PIN);
    angle = 0;
    servo.write(angle);
    delay(500);
  }
}

void loop() {
  if (RADAR_MODE) {
    servo.write(angle);
    delay(40);                           // temps de stabilisation du servo
  }

  float d = mesureDistance();
  Serial.print(angle);
  Serial.print(",");
  Serial.println(d, 1);

  if (RADAR_MODE) {
    angle += dir * STEP_DEG;
    if (angle >= 180) { angle = 180; dir = -1; }
    if (angle <= 0)   { angle = 0;   dir = 1; }
  } else {
    delay(50);                           // ~20 mesures/s
  }
}
