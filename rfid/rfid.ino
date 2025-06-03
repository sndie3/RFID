/*
 * RFID RC522 Module Connection to Arduino Uno:
 * VCC  → 3.3V
 * RST  → Pin 9
 * GND  → GND
 * MISO → Pin 12 (automatically handled by SPI library)
 * MOSI → Pin 11 (automatically handled by SPI library)
 * SCK  → Pin 13 (automatically handled by SPI library)
 * SDA  → Pin 10
 */

#include <SPI.h>
#include <MFRC522.h>

#define RST_PIN         9
#define SS_PIN          10
#define BUZZER_PIN      8  // Optional: Connect a buzzer for audio feedback
#define LED_GREEN       7  // Optional: Green LED for success
#define LED_RED         6  // Optional: Red LED for error/denied

MFRC522 mfrc522(SS_PIN, RST_PIN);

String lastCardID = "";
unsigned long lastReadTime = 0;
const unsigned long READ_DELAY = 2000; // 2 seconds between same card reads

void setup() {
  Serial.begin(9600);
  while (!Serial);
  
  SPI.begin();
  mfrc522.PCD_Init();
  
  // Initialize optional components
  if (BUZZER_PIN > 0) pinMode(BUZZER_PIN, OUTPUT);
  if (LED_GREEN > 0) pinMode(LED_GREEN, OUTPUT);
  if (LED_RED > 0) pinMode(LED_RED, OUTPUT);
  
  // Test LEDs on startup
  if (LED_GREEN > 0 && LED_RED > 0) {
    digitalWrite(LED_GREEN, HIGH);
    digitalWrite(LED_RED, HIGH);
    delay(500);
    digitalWrite(LED_GREEN, LOW);
    digitalWrite(LED_RED, LOW);
  }
  
  Serial.println("RFID System Ready");
  Serial.println("Waiting for cards...");
  
  // Verify if the RFID reader is properly connected
  byte v = mfrc522.PCD_ReadRegister(mfrc522.VersionReg);
  if (v == 0x00 || v == 0xFF) {
    Serial.println("WARNING: Communication failure, is the MFRC522 properly connected?");
    // Blink red LED if connection failed
    if (LED_RED > 0) {
      for (int i = 0; i < 5; i++) {
        digitalWrite(LED_RED, HIGH);
        delay(200);
        digitalWrite(LED_RED, LOW);
        delay(200);
      }
    }
  } else {
    Serial.print("MFRC522 Software Version: 0x");
    Serial.println(v, HEX);
    if (v == 0x91) {
      Serial.println("= v1.0");
    } else if (v == 0x92) {
      Serial.println("= v2.0");
    } else {
      Serial.println("= (unknown)");
    }
    
    // Success beep
    if (BUZZER_PIN > 0) {
      tone(BUZZER_PIN, 1000, 200);
    }
    if (LED_GREEN > 0) {
      digitalWrite(LED_GREEN, HIGH);
      delay(1000);
      digitalWrite(LED_GREEN, LOW);
    }
  }
}

void loop() {
  // Reset the loop if no new card present on the sensor/reader
  if (!mfrc522.PICC_IsNewCardPresent()) {
    return;
  }

  // Select one of the cards
  if (!mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  // Get card UID
  String cardID = getCardID();
  
  // Check if it's the same card read recently (debounce)
  unsigned long currentTime = millis();
  if (cardID == lastCardID && (currentTime - lastReadTime) < READ_DELAY) {
    mfrc522.PICC_HaltA();
    return;
  }
  
  // Update last read info
  lastCardID = cardID;
  lastReadTime = currentTime;
  
  // Send card ID to Python application via Serial
  Serial.println(cardID);
  
  // Visual/Audio feedback
  cardDetectedFeedback();
  
  // Halt PICC
  mfrc522.PICC_HaltA();
  
  // Stop encryption on PCD
  mfrc522.PCD_StopCrypto1();
}

String getCardID() {
  String cardID = "";
  
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) {
      cardID += "0";
    }
    cardID += String(mfrc522.uid.uidByte[i], HEX);
  }
  
  cardID.toUpperCase();
  return cardID;
}

void cardDetectedFeedback() {
  // Beep sound
  if (BUZZER_PIN > 0) {
    tone(BUZZER_PIN, 800, 100);
    delay(150);
    tone(BUZZER_PIN, 1000, 100);
  }
  
  // Flash green LED
  if (LED_GREEN > 0) {
    digitalWrite(LED_GREEN, HIGH);
    delay(200);
    digitalWrite(LED_GREEN, LOW);
  }
}

// Function to handle serial commands from Python (optional)
void handleSerialCommands() {
  if (Serial.available()) {
    String command = Serial.readString();
    command.trim();
    
    if (command == "STATUS") {
      Serial.println("RFID_READY");
    } else if (command == "RESET") {
      lastCardID = "";
      lastReadTime = 0;
      Serial.println("RESET_OK");
    } else if (command == "TEST_BEEP") {
      if (BUZZER_PIN > 0) {
        tone(BUZZER_PIN, 1000, 500);
      }
      Serial.println("BEEP_OK");
    } else if (command == "TEST_LED_GREEN") {
      if (LED_GREEN > 0) {
        digitalWrite(LED_GREEN, HIGH);
        delay(1000);
        digitalWrite(LED_GREEN, LOW);
      }
      Serial.println("LED_GREEN_OK");
    } else if (command == "TEST_LED_RED") {
      if (LED_RED > 0) {
        digitalWrite(LED_RED, HIGH);
        delay(1000);
        digitalWrite(LED_RED, LOW);
      }
      Serial.println("LED_RED_OK");
    }
  }
}

// Optional: Function to format card ID with separators
String formatCardID(String cardID) {
  String formatted = "";
  for (int i = 0; i < cardID.length(); i += 2) {
    if (i > 0) formatted += ":";
    formatted += cardID.substring(i, i + 2);
  }
  return formatted;
}

// Optional: Function to validate card format
bool isValidCard() {
  // Check if card type is supported
  MFRC522::PICC_Type piccType = mfrc522.PICC_GetType(mfrc522.uid.sak);
  
  // Most common card types
  return (piccType == MFRC522::PICC_TYPE_MIFARE_MINI ||
          piccType == MFRC522::PICC_TYPE_MIFARE_1K ||
          piccType == MFRC522::PICC_TYPE_MIFARE_4K ||
          piccType == MFRC522::PICC_TYPE_MIFARE_UL ||
          piccType == MFRC522::PICC_TYPE_ISO_14443_4);
}