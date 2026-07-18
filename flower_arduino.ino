#include <Servo.h>
#include <math.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

Servo baseServo; Servo lowerServo; Servo upperServo; Servo headServo;
float t = 0.0;

int currentState = 0; 
int lastDrawnState = -1; 

const int BASE_CENTER = 90; const int LOWER_CENTER = 90; 
const int UPPER_CENTER = 60; const int HEAD_CENTER = 90;

unsigned long lastBlink = 0; 
bool blinking = false;
bool lastBlinking = false; 

void drawFace(int state, bool blink) {
  display.clearDisplay();
  
  if (blink && state != 3) {
    display.drawLine(35, 28, 50, 28, SSD1306_WHITE);
    display.drawLine(78, 28, 93, 28, SSD1306_WHITE);
  } else {
    if (state == 0) { 
      display.fillCircle(42, 28, 6, SSD1306_WHITE); 
      display.fillCircle(86, 28, 6, SSD1306_WHITE);
    } else if (state == 1) { 
      display.fillCircle(42, 28, 9, SSD1306_WHITE); 
      display.fillCircle(86, 28, 9, SSD1306_WHITE);
    } else if (state == 2) { 
      display.fillCircle(42, 26, 6, SSD1306_WHITE); 
      display.fillCircle(86, 26, 6, SSD1306_WHITE);
    } else if (state == 3) { 
      display.drawLine(35, 22, 50, 31, SSD1306_WHITE); 
      display.drawLine(78, 31, 93, 22, SSD1306_WHITE);
    }
  }

  if (state == 0) {
    display.drawLine(54, 45, 74, 45, SSD1306_WHITE);
  } else if (state == 1) {
    display.drawCircle(64, 45, 4, SSD1306_WHITE);
  } else if (state == 2) {
    display.fillRoundRect(44, 40, 40, 12, 6, SSD1306_WHITE); 
  } else if (state == 3) {
    display.drawLine(54, 48, 64, 42, SSD1306_WHITE); 
    display.drawLine(64, 42, 74, 48, SSD1306_WHITE);
  }

  display.display();
}

void setup() {
  Serial.begin(9600);
  Wire.begin();
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { while (1); }
  
  baseServo.attach(11); lowerServo.attach(10);
  upperServo.attach(9); headServo.attach(6);
  
  drawFace(currentState, false);
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == 'I') currentState = 0;
    if (cmd == 'L') currentState = 1;
    if (cmd == 'H') currentState = 2;
    if (cmd == 'S') currentState = 3;
  }

  unsigned long now = millis();
  if (currentState == 0 || currentState == 1) {
    if (!blinking && now - lastBlink > 4000) { 
      blinking = true; 
      lastBlink = now; 
    }
    if (blinking && now - lastBlink > 180) { 
      blinking = false; 
      lastBlink = now; 
    }
  } else {
    blinking = false; 
  }

  if (currentState != lastDrawnState || blinking != lastBlinking) {
    drawFace(currentState, blinking);
    lastDrawnState = currentState;
    lastBlinking = blinking;
  }

  int base = BASE_CENTER, lower = LOWER_CENTER, upper = UPPER_CENTER, head = HEAD_CENTER;
  
  if (currentState == 0) { 
    base = BASE_CENTER + 15 * sin(t); 
    lower = LOWER_CENTER + 15 * sin(t + 0.5);
    upper = UPPER_CENTER + 15 * sin(t + 1.0); 
    head = HEAD_CENTER + 15 * sin(t + 1.5);
    t += 0.04;
  } else if (currentState == 1) { 
    lower = LOWER_CENTER - 15; 
    upper = UPPER_CENTER + 15; 
    head = HEAD_CENTER - 15; 
  } else if (currentState == 2) { 
    lower = LOWER_CENTER + 20; 
    upper = UPPER_CENTER + 20; 
    head = HEAD_CENTER + 15 * sin(t * 3.5); 
    t += 0.05;
  } else if (currentState == 3) { 
    base = BASE_CENTER + 5 * sin(t);
    lower = LOWER_CENTER - 20 + 5 * sin(t + 0.5); 
    upper = max(0, UPPER_CENTER - 20) + 5 * sin(t + 1.0); 
    head = HEAD_CENTER + 20 + 5 * sin(t + 1.5); 
    t += 0.02; 
  }

  baseServo.write(base); lowerServo.write(lower);
  upperServo.write(upper); headServo.write(head);
  delay(20);
}