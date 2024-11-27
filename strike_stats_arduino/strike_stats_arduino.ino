#include <ArduinoBLE.h>
#include <Arduino_LSM6DS3.h>

#define IMU_SERVICE_UUID "119"
#define SPEED_CHARACTERISTIC_UUID   "77777777-7777-7777-7777-a77777777777"
#define FORCE_CHARACTERISTIC_UUID   "77777777-7777-7777-7777-b77777777777"

#define MOTION_ACCEL_THRESHOLD 8
#define FORCE_CLEANSE_THRESHOLD 5
#define ACCEL_CLEANSE_THRESHOLD 0.9
#define MOTION_SUSTAIN 200

#define G_VALUE 9.80665
#define AX_INCR 5
#define AY_INCR 0.8
#define AZ_INCR 0.3

// Analog Input for Force Sensitive Resistor
const int fsrPin = A0;          // FSR connected to A0 pin
const float V_in = 5.0;         // Input voltage
const float R_M = 10000.0;      // fixed resistor = 10k Ohm

enum State {
  STATIC,
  MOTION
};

State currentState = STATIC;
State previousState = STATIC;

float currentMaxSpeed = 0.0;
float currentMaxForce = 0.0;
float ax, ay, az, gx, gy, gz, az_raw, vx, vy, vz;

BLEService imuService(IMU_SERVICE_UUID);
BLEFloatCharacteristic speedCharacteristic(SPEED_CHARACTERISTIC_UUID, BLERead | BLENotify);
BLEFloatCharacteristic forceCharacteristic(FORCE_CHARACTERISTIC_UUID, BLERead | BLENotify);

const int ledPin = LED_BUILTIN;
bool send_flag = false;

void sendData();
void resetPunch();

void setup() {
  Serial.begin(9600);
  // while (!Serial);

  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);

  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }

  Serial.print("Gyroscope sample rate = ");
  Serial.print(IMU.gyroscopeSampleRate());
  Serial.println(" Hz");
  Serial.print("Accelerometer sample rate = ");
  Serial.print(IMU.accelerationSampleRate());
  Serial.println(" Hz");

  if (!BLE.begin()) {
    Serial.println("Starting BLE failed!");
    while (1);
  }

  BLE.setLocalName("Smart Boxing Gloves");
  BLE.setAdvertisedService(imuService);

  imuService.addCharacteristic(speedCharacteristic);
  imuService.addCharacteristic(forceCharacteristic);

  BLE.addService(imuService);

  speedCharacteristic.writeValue(0.0f);
  forceCharacteristic.writeValue(0.0f);

  BLE.advertise();

  Serial.println("BLE Services Launched");
}

void loop() {
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Connected to central: ");
    Serial.println(central.address());
    digitalWrite(ledPin, HIGH);

    resetPunch();
    unsigned long startTime = millis(), endTime, motion_start_time;

    while (central.connected()) {
      int sensorValue = analogRead(fsrPin);
      float V_out = (sensorValue * V_in) / 1023.0;
      float R_FSR = R_M * (V_in - V_out) / V_out;
      float force = 196.4092 * V_out * V_out;

      if (IMU.accelerationAvailable() && IMU.gyroscopeAvailable()) {
        IMU.readAcceleration(ax, ay, az_raw);
      }

      // remove az shift
      az = az_raw - 1.f;

      if (ax < ACCEL_CLEANSE_THRESHOLD)
        ax = 0;
      if (ay < ACCEL_CLEANSE_THRESHOLD)
        ay = 0;
      if (az < ACCEL_CLEANSE_THRESHOLD)
        az = 0;

      ax = AX_INCR * ax;
      ay = AY_INCR * ay;
      az = AZ_INCR * az;


      // Serial.print("IMU: ax=");
      // Serial.print(ax);
      // Serial.print(", ay=");
      // Serial.print(ay);
      // Serial.print(", az=");
      // Serial.println(az);


      // Cleanse Data
      if (force < FORCE_CLEANSE_THRESHOLD)
        force = 0;

      float accelMagnitude = sqrt(ax * ax + ay * ay + az * az);
      
      // Detect punch
      if (accelMagnitude > MOTION_ACCEL_THRESHOLD) {
        currentState = MOTION;
        if (previousState == STATIC) {
          Serial.println("Punch detected!");
          currentMaxSpeed = 0.0;
          currentMaxForce = 0.0;
          vx = 0.0f;
          vy = 0.0f;
          vz = 0.0f;
        }
      } else {
        currentState = STATIC;
      }
      delay(10);
      endTime = millis();

      float time_delay = (float)((endTime - startTime) / 1000.f);

      startTime = millis();

      if (currentState == MOTION) {
        motion_start_time = millis();
        send_flag = false;

        vx += ax * time_delay * G_VALUE;
        vy += ay * time_delay * G_VALUE;
        vz += az * time_delay * G_VALUE;

        float speed = sqrt(vx * vx + vy * vy + vz * vz);
        if (speed > currentMaxSpeed) {
          currentMaxSpeed = speed;
        }

        if (force > currentMaxForce) {
          currentMaxForce = force;
        }

        Serial.print("Speed: ");
        Serial.print(speed);
        Serial.print(" m/s, Force: ");
        Serial.print(force);
        Serial.println(" N");
      }

      // End of one punch
      if (currentState == STATIC && previousState == MOTION) {
        send_flag = true;
      }

      // Avoid sending multiple packages within one punch
      if (send_flag && millis() - motion_start_time >= MOTION_SUSTAIN) {
        Serial.print("Punch Info: ");
        Serial.print("Max Speed: ");
        Serial.print(currentMaxSpeed);
        Serial.print(" m/s, Max Force: ");
        Serial.print(currentMaxForce);
        Serial.println(" N");

        sendData();
        send_flag = false;

        currentMaxSpeed = 0.0;
        currentMaxForce = 0.0;
      }


      previousState = currentState;
    }

    Serial.print("Disconnected from central: ");
    Serial.println(central.address());
    digitalWrite(ledPin, LOW);
  }
}

void sendData() {
  speedCharacteristic.writeValue(currentMaxSpeed);
  forceCharacteristic.writeValue(currentMaxForce);
}

void resetPunch() {
  currentMaxSpeed = 0.0;
  currentMaxForce = 0.0;

  Serial.println("Punch data has been reset.");
}
