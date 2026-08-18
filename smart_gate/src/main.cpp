#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ESP32Servo.h>

// ─── WiFi credentials ────────────────────────────────────────────────────────
const char* WIFI_SSID     = "Malak";
const char* WIFI_PASSWORD = "Mk143200";

// ─── Pin definitions ─────────────────────────────────────────────────────────
#define SERVO_PIN    15
#define LED_GREEN    32   // authorized user
#define LED_RED      33   // gate closed / deniedpi
#define LED_YELLOW   25   // new visitor being registered

// ─── Gate angles ─────────────────────────────────────────────────────────────
#define ANGLE_OPEN   90
#define ANGLE_CLOSED  0

// ─── Gate open duration (ms) ─────────────────────────────────────────────────
#define GATE_OPEN_MS 10000

// ─── Objects ─────────────────────────────────────────────────────────────────
Servo     gateServo;
WebServer server(80);

bool gateOpen = false;

// ─── LED helpers ─────────────────────────────────────────────────────────────
void ledsOff() {
    digitalWrite(LED_GREEN,  LOW);
    digitalWrite(LED_RED,    LOW);
    digitalWrite(LED_YELLOW, LOW);
}

void setClosed() {
    gateOpen = false;
    gateServo.write(ANGLE_CLOSED);
    ledsOff();
    digitalWrite(LED_RED, HIGH);
    Serial.println(">> Gate CLOSED  - Red LED ON");
}

void setOpenAuthorized() {
    gateOpen = true;
    gateServo.write(ANGLE_OPEN);
    ledsOff();
    digitalWrite(LED_GREEN, HIGH);
    Serial.println(">> Gate OPEN    - Green LED ON  (authorized user)");
}

void setOpenNewVisitor() {
    gateOpen = true;
    gateServo.write(ANGLE_OPEN);
    ledsOff();
    digitalWrite(LED_YELLOW, HIGH);
    Serial.println(">> Gate OPEN    - Yellow LED ON (new visitor registered)");
}

// ─── HTTP handlers ───────────────────────────────────────────────────────────
void handleRoot() {
    server.send(200, "text/plain", "ESP32 Smart Gate Running");
}

// Called when plate is already in the database (registered user)
void handleOpen() {
    Serial.println("[/open] Authorized user → opening gate");
    setOpenAuthorized();
    server.send(200, "text/plain", "Gate Opened - Authorized");
    delay(GATE_OPEN_MS);
    setClosed();
}

// Called when new visitor is registered and spot is available
void handleOpenNew() {
    Serial.println("[/open_new] New visitor registered → opening gate");
    setOpenNewVisitor();
    server.send(200, "text/plain", "Gate Opened - New Visitor");
    delay(GATE_OPEN_MS);
    setClosed();
}

void handleStatus() {
    server.send(200, "text/plain", gateOpen ? "OPEN" : "CLOSED");
}

void handleNotFound() {
    server.send(404, "text/plain", "Not Found");
}

// ─── Setup ───────────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    Serial.println("\n=== Smart Gate System Booting ===");

    pinMode(LED_GREEN,  OUTPUT);
    pinMode(LED_RED,    OUTPUT);
    pinMode(LED_YELLOW, OUTPUT);

    ESP32PWM::allocateTimer(0);
    gateServo.setPeriodHertz(50);
    gateServo.attach(SERVO_PIN, 500, 2400);

    setClosed();

    Serial.printf("Connecting to WiFi: %s\n", WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println();
    Serial.println("WiFi Connected!");
    Serial.print("ESP32 IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.println("Copy this IP into smart_gate.py → ESP32_IP");

    server.on("/",         handleRoot);
    server.on("/open",     handleOpen);
    server.on("/open_new", handleOpenNew);
    server.on("/status",   handleStatus);
    server.onNotFound(handleNotFound);

    server.begin();
    Serial.println("Web Server started on port 80");
    Serial.println("=================================\n");
}

// ─── Loop ────────────────────────────────────────────────────────────────────
void loop() {
    server.handleClient();
}
