import os
import ipaddress
import wifi
import socketpool
import ssl
import adafruit_requests
import supervisor
import pwmio
import board
import time
import adafruit_minimqtt.adafruit_minimqtt as MQTT

#https://github.com/adafruit/Adafruit_CircuitPython_MiniMQTT/blob/main/examples/native_networking/minimqtt_adafruitio_native_networking.py

#https://stackoverflow.com/questions/1969240/mapping-a-range-of-values-to-another
def translate(sensor_val, in_from, in_to, out_from, out_to):
  out_range = out_to - out_from
  in_range = in_to - in_from
  in_val = sensor_val - in_from
  val=(float(in_val)/in_range)*out_range
  out_val = out_from+val
  return int(out_val)

#https://stackoverflow.com/questions/5996881/how-to-limit-a-number-to-be-within-a-specified-range-python
def clamp(n, minn, maxn):
  return max(min(maxn, n), minn)

def connect(mqtt_client, userdata, flags, rc):
  print("Connected to MQTT Broker!")
  print("Flags: {0}\n RC: {1}".format(flags, rc))

def subscribe(mqtt_client, userdata, topic, granted_qos):
  print("Subscribed to {0} with QOS level {1}".format(topic, granted_qos))

def message(client, topic, message):
  print("New message on topic {0}: {1}".format(topic, message))
  try:
    value = int(message)
  except:
    return
  if topic == "homeassistant/sensor/envoy_2022xxxxxxxx_current_power_production/state":
    productionPWM.duty_cycle = translate(clamp(value,0,9000),0,9000,0,65535)
  if topic == "homeassistant/sensor/envoy_2022xxxxxxxx_current_power_consumption/state":
    consumptionPWM.duty_cycle = translate(clamp(value,0,9000),0,9000,0,65535)

productionPWM   = pwmio.PWMOut(board.GP6, frequency=5000, duty_cycle=0)
consumptionPWM  = pwmio.PWMOut(board.GP7, frequency=5000, duty_cycle=0)

print()
print("Connecting to WiFi")
wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))

print("Connected to WiFi")
print("My MAC addr:", [hex(i) for i in wifi.radio.mac_address])

print("My IP address is", wifi.radio.ipv4_address)

pool = socketpool.SocketPool(wifi.radio)

mqtt_client = MQTT.MQTT(
    broker="192.168.1.50",
    socket_pool=pool,
    ssl_context=ssl.create_default_context(),
)

mqtt_client.on_connect = connect
mqtt_client.on_subscribe = subscribe
mqtt_client.on_message = message

topics = [("homeassistant/sensor/envoy_2022xxxxxxxx_current_power_production/state",0),("homeassistant/sensor/envoy_2022xxxxxxxx_current_power_consumption/state",0)]

try:
  mqtt_client.connect()
  mqtt_client.subscribe(topics)
except:
  supervisor.reload()

while True:
  try:
    mqtt_client.loop(timeout=1)
  except:
    supervisor.reload()
