# Copy this file to config.py on the ESP32 and fill in your own values.
# config.py is git-ignored so Wi-Fi passwords and endpoints never reach GitHub.

WIFI_SSID = "your-wifi-name"
WIFI_PASSWORD = "your-wifi-password"

# WebSocket URL printed by `sam deploy` (cloud/template.yaml), e.g.
# wss://abc123.execute-api.us-west-2.amazonaws.com/dev  (keep ?role=device at the end)
WS_URL = "wss://example.execute-api.us-west-2.amazonaws.com/dev?role=device"

PATIENT_ID = "bed-01"      # one ESP32 per patient / bed
SEND_INTERVAL_S = 5        # how often a reading is sent

DHT22_PIN = 14             # DHT22 data pin
I2C_SCL_PIN = 22           # MAX30100 pulse oximeter (optional)
I2C_SDA_PIN = 21
STATUS_LED_PIN = 2         # on-board LED: on = connected
