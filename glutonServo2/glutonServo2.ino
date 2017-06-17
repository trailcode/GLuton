/*************************************************** 
  This is an example for our Adafruit 16-channel PWM & Servo driver
  Servo test - this will drive 16 servos, one after the other

  Pick one up today in the adafruit shop!
  ------> http://www.adafruit.com/products/815

  These displays use I2C to communicate, 2 pins are required to  
  interface. For Arduino UNOs, thats SCL -> Analog 5, SDA -> Analog 4

  Adafruit invests time and resources providing this open source code, 
  please support Adafruit and open-source hardware by purchasing 
  products from Adafruit!

  Written by Limor Fried/Ladyada for Adafruit Industries.  
  BSD license, all text above must be included in any redistribution
 ****************************************************/

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// called this way, it uses the default address 0x40
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();
// you can also call it with a different address you want
//Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x41);

// Depending on your servo make, the pulse width min and max may vary, you 
// want these to be as small/large as possible without hitting the hard stop
// for max range. You'll have to tweak them as necessary to match the servos you
// have!
#define SERVOMIN  150 // this is the 'minimum' pulse length count (out of 4096)
#define SERVOMAX  600 // this is the 'maximum' pulse length count (out of 4096)

// our servo # counter
uint8_t servonum = 0;

void setup() {
  Serial.begin(115200);

  delay(100);
  
  Serial.println("16 channel Servo test!");

  pwm.begin();
  
  pwm.setPWMFreq(60);  // Analog servos run at ~60 Hz updates

  //pwm.setPWMFreq(1600);  // This is the maximum PWM frequency

  // if you want to really speed stuff up, you can go into 'fast 400khz I2C' mode
  // some i2c devices dont like this so much so if you're sharing the bus, watch
  // out for this!
//#ifdef TWBR    
  // save I2C bitrate
  //uint8_t twbrbackup = TWBR;
  // must be changed after calling Wire.begin() (inside pwm.begin())
  //TWBR = 12; // upgrade to 400KHz!
//#endif

  yield();
}

#define uint uint16_t

void loop() {
  // Drive each servo one at a time
  /*
  Serial.println(servonum);
  for (uint16_t pulselen = SERVOMIN; pulselen < SERVOMAX; pulselen++) {
    pwm.setPWM(servonum, 0, pulselen);
  }

  delay(500);
  for (uint16_t pulselen = SERVOMAX; pulselen > SERVOMIN; pulselen--) {
    pwm.setPWM(servonum, 0, pulselen);
  }
  */
  //Serial.println("fsfdf");
  // send data only when you receive data:
        if (Serial.available() > 0) {
                // read the incoming byte:
                int command = Serial.parseInt();
                Serial.println(command);
                if(command == 1)
                {
                  int servo = Serial.parseInt();
                  int value = Serial.parseInt();
                  pwm.setPin(servo, value);
                  delay(1);
                  
                }
                else if(command == 2)
                {
                  delay(Serial.parseInt());
                  Serial.println("=");
                }
                else if(command == 3)
                {
                  int pin = Serial.parseInt();

                  Serial.println(analogRead(pin));
                  //Serial.println(128);
                  
                }
                //int incomingByte1 = Serial.read();

                

                // say what you got:
                /*
                Serial.print("servo: ");
                Serial.print(servo);
                Serial.print(" value: ");
                Serial.println(value);
                
                yield();
                //*/
                //Serial.print(" ");
                //Serial.println(incomingByte1);
        }

  /*
  for(uint i = 0; i < 13; ++i)
  {
    setServo(i, sin(f));
    //setServo(i, 0);
  }

  f += 0.1;

  delay(50);

  servonum ++;
  if (servonum > 0) servonum = 0;
  */
}
