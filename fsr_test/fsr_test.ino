const int fsrPin = A0;
const float V_in = 5.0;
const float R_M = 10000.0;

void setup() {
  Serial.begin(9600);
}

void loop() {
  int sensorValue = analogRead(fsrPin);
  float V_out = (sensorValue * V_in) / 1023.0;

  float R_FSR = R_M * (V_in - V_out) / V_out;

  Serial.print("V_out = ");
  Serial.print(V_out);
  Serial.print(" V, ");
  Serial.print("R_FSR = ");
  Serial.print(R_FSR);
  Serial.println(" ohms");

  delay(100);
}
