#include <DHT.h>
#include <ESP8266WiFi.h>
#include <ThingSpeak.h>

#define DHT_PIN 2
#define DHT_TYPE DHT11
DHT dht(DHT_PIN, DHT_TYPE);

#define IR_PIN 4
#define TRIG_PIN 12
#define ECHO_PIN 14
#define LED_PIN 5  

long trainCount = 0;
bool trainDetected = false;

const char* ssid = "realme7";
const char* password = "1234567890";

unsigned long channelID = 2834764;
const char* writeAPIKey = "6R1M4NA5U41GE1FN";

WiFiClient client;

void setup(){
  Serial.begin(115200);

  WiFi.begin(ssid, password);
  while(WiFi.status() != WL_CONNECTED){
    delay(1000);
    Serial.println("Connecting to Wifi ...");
  }
  Serial.println("Connected to Wifi");

  ThingSpeak.begin(client);

  dht.begin();

  pinMode(IR_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);      
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
}

long measureDistance(){
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH);
  long distance = duration * 0.034 / 2;
  return distance;
}

void loop(){
  float hum = dht.readHumidity();
  float temp = dht.readTemperature();
  if(isnan(hum) || isnan(temp)){
    Serial.println("Failed to read from DHT sensor!");
    return;
  }
  
  int IR = digitalRead(IR_PIN);
  long dist = measureDistance();


  if(dist >= 0 && dist < 10){
    if(!trainDetected){
      trainCount++;
      trainDetected = true;
      Serial.println("Train detected and Counted!");
    }
  } else if (dist > 15){
      trainDetected = false;
  }
  

  Serial.println("IR Sensor: ");
  if( IR == HIGH ){
    Serial.println("Object is not detected ");
    digitalWrite(LED_PIN, LOW); 
  }
  else{
    Serial.println("ALERT: Object Detected");
    digitalWrite(LED_PIN, HIGH);
    Serial.println("Stopping distance: 1000m");
    Serial.println("Time for stop: 25.23s");
  }
  
  Serial.print("Temperature: ");
  Serial.print(temp);
  Serial.print(" C, Humidity: ");
  Serial.print(hum);
  Serial.println(" %");

  Serial.print("Distance: ");
  Serial.print(dist);
  Serial.println(" cm");
  Serial.print("Train count: ");
  Serial.println(trainCount);

  ThingSpeak.setField(1, IR);
  ThingSpeak.setField(2, dist);
  ThingSpeak.setField(3, temp);
  ThingSpeak.setField(4, hum);
  ThingSpeak.setField(5, trainCount);
  ThingSpeak.writeFields(channelID, writeAPIKey);

  delay(2000);
}