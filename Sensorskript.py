import os
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import serial
import time
import struct

# Pfad zur seriellen Schnittstelle (Raspberry Pi 5)
SERIAL_PORT = "/dev/ttyAMA0"
BAUD_RATE = 9600

# Befehl zum Anfordern der CO2-Konzentration
REQUEST_CO2 = b'\xFF\x01\x86\x00\x00\x00\x00\x00\x79'

# API SchlÃ¼ssel auslesen
load_dotenv()
API_KEY = os.getenv('API_KEY')

# Device-ID festlegen
sensor_id = "sesnorvls1"

# Standard-Intervall
interval = 120

# URL der API
url = "https://victorious-field-0cd4c7903.4.azurestaticapps.net/api/sensor/sensor-data"

def read_co2():
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            ser.write(REQUEST_CO2)
            response = ser.read(9)

            if len(response) == 9 and response[0] == 0xFF and response[1] == 0x86:
                high_byte = response[2]
                low_byte = response[3]
                co2 = (high_byte << 8) + low_byte
                print(f"COâ-Konzentration: {co2} ppm")
                return co2
            else:
                print("Fehler beim Lesen der Daten.")
                return None
    except serial.SerialException as e:
        print(f"Fehler beim Zugriff auf die serielle Schnittstelle: {e}")
    except Exception as e:
        print(f"Unerwarteter Fehler: {e}")
     
       
        
def fetch_interval_from_api():
    new_interval = response_json.get("interval")
    if new_interval:
        interval = int(new_interval)
        print(f"Intervall aktualisiert auf: {interval} Sekunden")
    return interval
    
    
def validate_data(temperature, humidity):
    if not (-50 <= temperature <= 100):
        raise ValueError(f"Unrealistische Temperatur erkannt: {temperature:.2f} Â°C")
    if not (0 <= humidity <= 100):
        raise ValueError(f"Unrealistische Luftfeuchtigkeit erkannt: {humidity}%")


while True:
    try:
        # Temperatur auslesen und in Grad Celsius umwandeln
        with open('/sys/bus/iio/devices/iio:device0/in_temp_input', 'r') as file:
            raw_temp = file.read().strip()
            temperature = float(raw_temp) / 1000
            print(f"Die Temperatur betrÃ¤gt: {temperature:.2f} Â°C")

        # Luftfeuchtigkeit auslesen und Prozentwert berechnen
        with open('/sys/bus/iio/devices/iio:device0/in_humidityrelative_input', 'r') as file:
            raw_humidity = file.read().strip()
            humidity = int(raw_humidity) // 1000
            print(f"Die Luftfeuchtigkeit betrÃ¤gt: {humidity}%")

        co2 = read_co2()
        
        # Werte validieren
        validate_data(temperature, humidity)
        
        # Daten vorbereiten
        data = {
            "temperature": temperature,
            "humidity": humidity,
            "sensor_id": sensor_id,
            "timestamp": (datetime.utcnow() + timedelta(hours=0)).isoformat(),
            "co2": co2,
            
        }

        # PATCH-Anfrage senden
        headers = {
            'sensor-api-key': API_KEY,
            'Content-Type': 'application/json',
        }
        response = requests.patch(url, json=data, headers=headers)
        response.raise_for_status()
        

        # Antwort auslesen und JSON-Daten prÃ¼fen
        if response.headers.get('Content-Type') == 'application/json':
            response_json = response.json()
        else:
            response_json = {}

        # Antwort ausgeben
        print("Daten erfolgreich gesendet! Antwort:")
        print(response_json)

        # Intervall aus der Response auslesen
        interval = fetch_interval_from_api()
        print(f"Neues Intervall: {interval} Sekunden")
        print(data)

        # Wartezeit basierend auf dem neuen Intervall
        time.sleep(interval)

    except ValueError as e:
        print(f"UngÃ¼ltige Sensordaten: {e}")
        time.sleep(5) 
    except FileNotFoundError as e:
        print(f"Datei nicht gefunden: {e}")
        break
    except requests.exceptions.RequestException as e:
        print(f"HTTP-Anfrage fehlgeschlagen: {e}")
        time.sleep(5)
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
        time.sleep(5)
