#include <GxEPD2_3C.h>
#include <Fonts/FreeMonoBold9pt7b.h>
#include <Fonts/FreeMonoBold12pt7b.h>
#include <WiFi.h>
#include <string.h>
#include <esp_sleep.h>

#include "secrets.h"

// XIAO ESP32C3 pin assignments for e-paper display.
// SPI default pins on XIAO ESP32C3:
//   SCK  = D8  / GPIO8
//   MOSI = D10 / GPIO10
//
// E-paper wiring:
//   EPD VCC  -> 3V3
//   EPD GND  -> GND
//   EPD DIN  -> D10 / MOSI
//   EPD CLK  -> D8  / SCK
//   EPD CS   -> D3
//   EPD DC   -> D2
//   EPD RST  -> D1
//   EPD BUSY -> D0
constexpr int EPD_CS   = D3;
constexpr int EPD_DC   = D2;
constexpr int EPD_RST  = D1;
constexpr int EPD_BUSY = D0;

constexpr int EPD_WIDTH = 122;
constexpr int EPD_HEIGHT = 250;
constexpr int EPD_BYTES_PER_PLANE = ((EPD_WIDTH + 7) / 8) * EPD_HEIGHT;
constexpr int EPD_IMAGE_BYTES = EPD_BYTES_PER_PLANE * 2;

constexpr unsigned long WIFI_TIMEOUT_MS = 45000;
constexpr unsigned long HTTP_BODY_TIMEOUT_MS = 15000;

// Deep sleep duration: 12 hours in microseconds.
constexpr uint64_t SLEEP_DURATION_US = 12ULL * 60ULL * 60ULL * 1000000ULL;

uint8_t blackPlane[EPD_BYTES_PER_PLANE];
uint8_t redPlane[EPD_BYTES_PER_PLANE];
uint8_t imageBytes[EPD_IMAGE_BYTES];

GxEPD2_3C<GxEPD2_213_Z98c, GxEPD2_213_Z98c::HEIGHT> display(
  GxEPD2_213_Z98c(EPD_CS, EPD_DC, EPD_RST, EPD_BUSY)
);

bool readHttpBody(WiFiClient& client, uint8_t* buffer, int expectedBytes) {
  bool headerEnded = false;
  int matched = 0;
  int bytesRead = 0;
  const char marker[] = "\r\n\r\n";
  unsigned long lastRead = millis();

  while (millis() - lastRead < HTTP_BODY_TIMEOUT_MS && bytesRead < expectedBytes) {
    while (client.available() && bytesRead < expectedBytes) {
      char c = client.read();
      lastRead = millis();

      if (!headerEnded) {
        if (c == marker[matched]) {
          matched++;
          if (matched == 4) {
            headerEnded = true;
          }
        } else {
          matched = (c == marker[0]) ? 1 : 0;
        }
      } else {
        buffer[bytesRead++] = static_cast<uint8_t>(c);
      }
    }

    delay(1);
  }

  Serial.print("image bytes read: ");
  Serial.print(bytesRead);
  Serial.print(" / ");
  Serial.println(expectedBytes);

  return bytesRead == expectedBytes;
}

bool fetchDisplayImage() {
  WiFiClient client;

  Serial.println("Connecting to image API...");

  if (!client.connect(IMAGE_HOST, IMAGE_PORT)) {
    Serial.println("image api connect failed");
    return false;
  }

  client.print(String("GET ") + IMAGE_PATH + " HTTP/1.1\r\n");
  client.print(String("Host: ") + IMAGE_HOST + "\r\n");
  client.print("Connection: close\r\n\r\n");

  String statusLine = client.readStringUntil('\n');
  statusLine.trim();

  Serial.print("HTTP status: ");
  Serial.println(statusLine);

  if (!statusLine.startsWith("HTTP/1.1 200") &&
      !statusLine.startsWith("HTTP/1.0 200")) {
    Serial.println("HTTP status not OK");
    client.stop();
    return false;
  }

  bool ok = readHttpBody(client, imageBytes, EPD_IMAGE_BYTES);
  client.stop();

  if (!ok) {
    Serial.println("image read failed");
    return false;
  }

  memcpy(blackPlane, imageBytes, EPD_BYTES_PER_PLANE);
  memcpy(redPlane, imageBytes + EPD_BYTES_PER_PLANE, EPD_BYTES_PER_PLANE);

  return true;
}

bool fetchDisplayImageWithRetry() {
  bool fetched = fetchDisplayImage();

  if (!fetched) {
    Serial.println("image first fetch failed. retrying...");
    delay(1000);
    fetched = fetchDisplayImage();
  }

  if (!fetched) {
    Serial.println("image second fetch failed.");
  }

  return fetched;
}

void drawLines(const String& text) {
  display.setRotation(1);
  display.setFullWindow();

  display.firstPage();

  do {
    display.fillScreen(GxEPD_WHITE);

    display.setTextColor(GxEPD_BLACK);
    display.setFont(&FreeMonoBold9pt7b);

    int16_t y = 18;
    int lineStart = 0;

    while (lineStart < text.length() && y < 122) {
      int lineEnd = text.indexOf('\n', lineStart);

      if (lineEnd < 0) {
        lineEnd = text.length();
      }

      String line = text.substring(lineStart, lineEnd);

      if (line.length() > 26) {
        line = line.substring(0, 23) + "...";
      }

      display.setCursor(8, y);
      display.print(line);

      y += 20;
      lineStart = lineEnd + 1;
    }
  } while (display.nextPage());
}

void drawDisplayImage() {
  display.setRotation(2);
  display.setFullWindow();

  display.firstPage();

  do {
    display.fillScreen(GxEPD_WHITE);

    display.drawImage(
      blackPlane,
      redPlane,
      0,
      0,
      EPD_WIDTH,
      EPD_HEIGHT,
      false,
      false,
      false
    );
  } while (display.nextPage());
}
bool connectWiFiOnce(unsigned long timeoutMs) {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long started = millis();

  while (WiFi.status() != WL_CONNECTED &&
         millis() - started < timeoutMs) {
    Serial.print("Wi-Fi status: ");
    Serial.println(WiFi.status());
    delay(1000);
  }

  return WiFi.status() == WL_CONNECTED;
}

void connectWiFi() {
  WiFi.persistent(false);

  Serial.println("Preparing Wi-Fi.");

  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  delay(500);

  WiFi.disconnect(false);
  delay(500);

  Serial.print("Connecting to Wi-Fi SSID: ");
  Serial.println(WIFI_SSID);

  if (!connectWiFiOnce(30000)) {
    Serial.print("Wi-Fi first attempt failed. status: ");
    Serial.println(WiFi.status());

    WiFi.disconnect(false);
    delay(2000);

    Serial.println("Retrying Wi-Fi...");
    connectWiFiOnce(30000);
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("Wi-Fi connected. IP: ");
    Serial.println(WiFi.localIP());

    Serial.print("RSSI: ");
    Serial.println(WiFi.RSSI());
  } else {
    Serial.print("Wi-Fi connect failed. Final status: ");
    Serial.println(WiFi.status());
  }
}

void shutdownWiFi() {
  Serial.println("Shutting down Wi-Fi radio.");

  WiFi.disconnect(false);
  delay(300);

  WiFi.mode(WIFI_OFF);
  delay(300);
}


void sleepNow() {
  // Do not call display.hibernate() here.
  // On this e-paper setup it causes the screen to flash and turn white.

  shutdownWiFi();

  Serial.println("Entering deep sleep for 12 hours.");
  Serial.flush();
  delay(100);

  esp_sleep_enable_timer_wakeup(SLEEP_DURATION_US);
  esp_deep_sleep_start();
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("Booting XIAO ESP32C3 APOD display");

  SPI.begin();
  // If you want to specify SPI pins explicitly, use this instead:
  // SPI.begin(D8, -1, D10, EPD_CS);

  display.init(115200, true, 20, false);

  drawLines("connecting...");

  connectWiFi();

  if (WiFi.status() != WL_CONNECTED) {
    drawLines(String("wifi\nconnect failed\nstatus: ") + WiFi.status());
    sleepNow();
  }

  if (fetchDisplayImageWithRetry()) {
    drawDisplayImage();
  } else {
    drawLines("apod image\nfetch failed");
  }

  sleepNow();
}

void loop() {
  // Not used.
  // Deep sleep restarts execution from setup().
}
