#include "max6675.h" 
#include <Arduino.h>
#include "HX711.h"
#include "SPI.h"
#include "SD.h"


const int LOADCELL_DOUT_PIN = 3;
const int LOADCELL_SCK_PIN = 2;
double tim=0, ClockSerial=0, Pressure=0, ClockSd=0;
int TempAmbiente = 23; // °C
float FatorCorrecao1 = 0; float FatorCorrecao2 = 0; float FatorCorrecao3 = 0;
int thermoDO2 = 4; int thermoDO3 = 15; // DO =SO ; SCK = CLK; 
int thermoCS2 = 5; int thermoCS3 = 16;
int thermoCLK2 = 6; int thermoCLK3 =17;
const int chipSelect = 10;
File myFile;
HX711 scale;

//MAX6675 thermocouple1(thermoCLK1, thermoCS1, thermoDO1);
MAX6675 thermocouple2(thermoCLK2, thermoCS2, thermoDO2);
MAX6675 thermocouple3(thermoCLK3, thermoCS3, thermoDO3);

void setup() {
  Serial.begin(57600);
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(-22.3);
  scale.tare(); 
  pinMode(OUTPUT,19);
  pinMode(OUTPUT,8);
  digitalWrite(8,LOW);
  
  //FatorCorrecao1 = thermocouple1.readCelsius()-TempAmbiente;
  FatorCorrecao2 = thermocouple2.readCelsius()-TempAmbiente;
  FatorCorrecao3 = thermocouple3.readCelsius()-TempAmbiente;
  if(!SD.begin(chipSelect)) {
    Serial.println("Initialization failed!");
    //while (1);
  }else{Serial.println("Sd funcionando");
}
}
void loop() {
  String txt = ".txt";
  static int b;
  static bool count = true;
  static double T=0,Force=0;

  ClockSerial=millis();
  ClockSd=millis();
  static int  HoldValue2=0,HoldValue3=0,key=0,Pressure=0;//HoldValue1=0,
  Pressure=analogRead(0)*2;
  Force=scale.get_units()*9.78363/1000;
  if(millis()- tim>220){
   //HoldValue1= thermocouple1.readCelsius()-FatorCorrecao1; //Corpo
   HoldValue2 = thermocouple2.readCelsius()-FatorCorrecao2;  //Cabecote
   HoldValue3 = thermocouple3.readCelsius()-FatorCorrecao3;  //Bocal
   tim=millis();
   }
  
  if(digitalRead(19)==HIGH){
  if (count) {
    for (int a = 0; a < 50; a++) {
      if (SD.exists(String(a) + txt)) {
        b = a;
      }
    }
  }
  myFile = SD.open(String(b + 1) + txt, FILE_WRITE);
  if (myFile) {
    if (count) {
      myFile.println("Pressure Force Cabeçote Bocal   Clock    millis");
      count = false;
    }
    myFile.print("   ");
    myFile.print(Pressure);
    myFile.print("        ");
    myFile.print(Force,4);
    myFile.print("    ");
//    myFile.print(HoldValue1);
//    myFile.print("      ");
    myFile.print(HoldValue2);
    myFile.print("     ");
    myFile.print(HoldValue3);
    myFile.print("    ");
    ClockSd=millis()-ClockSd;
    myFile.print(ClockSd);
    myFile.print("     ");
    myFile.println(millis());
    myFile.close();
      if(millis()-T>1000){
      T=millis();
      digitalWrite(8,!digitalRead(8));
    }
    }
 }
  else{
   digitalWrite(8,LOW);
   //Serial.print(key);
   //Serial.print(",");
   //Serial.print(Pressure);
   //Serial.print(",");
   Serial.print(Force,4);
   //Serial.print(",");
   //Serial.print(HoldValue1);
   Serial.print(" , ");
   Serial.print(HoldValue2);
   Serial.print(" , ");
   Serial.println(HoldValue3);
   //Serial.print(" , ");
   ClockSerial=millis()-ClockSerial;
   //Serial.println(ClockSerial);
   delay(100);
   }
}
