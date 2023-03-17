
import os
import ipaddress
import wifi
import socketpool
import ssl
import adafruit_requests
import json
import time
import adafruit_ntp
import rtc
import supervisor
import pwmio
import board

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

production = pwmio.PWMOut(board.GP6, frequency=5000, duty_cycle=0)
consumption = pwmio.PWMOut(board.GP7, frequency=5000, duty_cycle=0)

print()
print("Connecting to WiFi")

#  connect to your SSID
wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))

print("Connected to WiFi")

#  prints MAC address to REPL
print("My MAC addr:", [hex(i) for i in wifi.radio.mac_address])

#  prints IP address to REPL
print("My IP address is", wifi.radio.ipv4_address)

pool = socketpool.SocketPool(wifi.radio)
ntp = adafruit_ntp.NTP(pool, tz_offset=0)
rtc.RTC().datetime = ntp.datetime

print("The time is", time.time())

sslContext = ssl.create_default_context() 
requests = adafruit_requests.Session(pool, sslContext)

sslContext.load_verify_locations(cadata="")
requestsInsecure = adafruit_requests.Session(pool, sslContext)

headers = {'Accept': 'application/json'}
data = 'user[email]=' + os.getenv('ENLIGHTEN_USERNAME') + '&user[password]=' + os.getenv('ENLIGHTEN_PASSWORD')

session = requests.post('https://enlighten.enphaseenergy.com/login/login.json', headers=headers, data=data)

#print(session.json())

headers = {'cookie': '_enlighten_4_session=' + session.json()['session_id']}

token = requests.get('https://enlighten.enphaseenergy.com/entrez-auth-token?serial_num=' + os.getenv('ENLIGHTEN_SERIAL'), headers=headers )

#print(token.json())

headers = {'Accept': 'application/json', 'Authorization': 'Bearer ' + token.json()['token']}

while True:
  if token.json()['expires_at'] < time.time():
    supervisor.reload() 
  try:
    production = requestsInsecure.get('https://envoy.local/production.json', headers=headers) 
    #print(production.json())
    print('Production: ' + str(production.json()['production'][0]['wNow']) + ' W Consumption: ' + str(production.json()['consumption'][0]['wNow']) + ' W')
    production.duty_cycle = translate(clamp(production.json()['production'][0]['wNow'],0,9000),0,9000,0,100)
    consumption.duty_cycle = translate(clamp(production.json()['consumption'][0]['wNow'],0,9000),0,9000,0,100)
  except:
    print('...')
  time.sleep(120)

