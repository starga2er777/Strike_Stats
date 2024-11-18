#include <ArduinoBLE.h>
#include <Arduino_LSM6DS3.h>

BLEService imuService("119");

// Characteristics
BLEFloatCharacteristic gxCharacteristic("77777777-7777-7777-7777-a77777777777", BLERead | BLEWrite);
BLEFloatCharacteristic gyCharacteristic("77777777-7777-7777-7777-b77777777777", BLERead | BLEWrite);
BLEFloatCharacteristic gzCharacteristic("77777777-7777-7777-7777-c77777777777", BLERead | BLEWrite);

BLEFloatCharacteristic axCharacteristic("77777777-7777-7777-7777-d77777777777", BLERead | BLEWrite);
BLEFloatCharacteristic ayCharacteristic("77777777-7777-7777-7777-e77777777777", BLERead | BLEWrite);
BLEFloatCharacteristic azCharacteristic("77777777-7777-7777-7777-f77777777777", BLERead | BLEWrite);

BLEFloatCharacteristic forceCharacteristic("77777777-7777-7777-7777-77777777777f", BLERead | BLEWrite);
BLEUnsignedIntCharacteristic communicationCharacteristic("77777777-7777-7777-7777-777777777777", BLERead | BLEWrite);

// Analog Inputs
const int fsrPin = A0;
const float V_in = 5.0;
const float R_M = 10000.0;

void setup()
{
  // Serial.begin(9600);
  // while (!Serial);

  if (!IMU.begin())
  {
    Serial.println("Failed to initialize IMU!");
  }

  Serial.print("Gyroscope sample rate = ");
  Serial.print(IMU.gyroscopeSampleRate());
  Serial.println(" Hz\n");
  Serial.print("Accelerometer sample rate = ");
  Serial.print(IMU.accelerationSampleRate());
  Serial.println(" Hz\n");

  // BLE initialization
  if (!BLE.begin())
  {
    Serial.println("Starting BLE failed!");
    while (1)
      ;
  }

  // set advertised local name and service UUID:
  BLE.setLocalName("Smart Boxing Gloves");
  BLE.setAdvertisedService(imuService);

  // add the characteristic to the service
  imuService.addCharacteristic(gxCharacteristic);
  imuService.addCharacteristic(gyCharacteristic);
  imuService.addCharacteristic(gzCharacteristic);
  imuService.addCharacteristic(axCharacteristic);
  imuService.addCharacteristic(ayCharacteristic);
  imuService.addCharacteristic(azCharacteristic);
  imuService.addCharacteristic(forceCharacteristic);
  imuService.addCharacteristic(communicationCharacteristic);

  // add service
  BLE.addService(imuService);

  // set the initial value for the characteristics:
  gxCharacteristic.writeValue(0.0f);
  gyCharacteristic.writeValue(0.0f);
  gzCharacteristic.writeValue(0.0f);
  axCharacteristic.writeValue(0.0f);
  ayCharacteristic.writeValue(0.0f);
  azCharacteristic.writeValue(0.0f);
  forceCharacteristic.writeValue(0.0f);
  communicationCharacteristic.writeValue(0);

  // start advertising
  BLE.advertise();

  Serial.println("BLE Services Launched");
}

void loop()
{
  // listen for BLE peripherals to connect:
  BLEDevice central = BLE.central();
  float gx, gy, gz;
  float ax, ay, az;
  float V_out, R_FSR;

  // if a central is connected to peripheral:
  if (central)
  {
    Serial.print("Connected to central: ");
    digitalWrite(LED_BUILTIN, HIGH);

    Serial.println(central.address());

    // while the central is still connected to peripheral:
    while (central.connected())
    {

      int sensorValue = analogRead(fsrPin);
      V_out = (sensorValue * V_in) / 1023.0;
      R_FSR = R_M * (V_in - V_out) / V_out;

      if (IMU.gyroscopeAvailable() && IMU.accelerationAvailable())
      {
        digitalWrite(LED_BUILTIN, HIGH);
        IMU.readAcceleration(ax, ay, az);
        IMU.readGyroscope(gx, gy, gz);
      }

      gxCharacteristic.writeValue(gx);
      gyCharacteristic.writeValue(gy);
      gzCharacteristic.writeValue(gz);

      axCharacteristic.writeValue(ax);
      ayCharacteristic.writeValue(ay);
      azCharacteristic.writeValue(az);

      forceCharacteristic.writeValue(R_FSR);
      communicationCharacteristic.writeValue(1);
      
      delay(50);
    }

    // when the central disconnects, print it out:
    Serial.print("Disconnected from central: ");
    Serial.println(central.address());
    digitalWrite(LED_BUILTIN, LOW);
  }
}