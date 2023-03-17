#!/usr/bin/python

## Todo
# dynamically find produciton/consumption entries
# handle expired tokens... ?quit and let systemd restart the script?

import requests
import time 
import RPi.GPIO as GPIO
import json

requests.packages.urllib3.disable_warnings() 

config = {'envoy' : 'envoy.local'}

with open("settings.json", "r") as jsonfile:
   configFile = json.load(jsonfile)
   print("Read config successful")

config.update(configFile)

#https://stackoverflow.com/questions/1969240/mapping-a-range-of-values-to-another
def translate(sensor_val, in_from, in_to, out_from, out_to):
    out_range = out_to - out_from
    in_range = in_to - in_from
    in_val = sensor_val - in_from
    val=(float(in_val)/in_range)*out_range
    out_val = out_from+val
    return out_val

#https://stackoverflow.com/questions/5996881/how-to-limit-a-number-to-be-within-a-specified-range-python
def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)

headers = {'Accept': 'application/json'}
data = 'user[email]=' + config['username'] + '&user[password]=' + config['password']

session = requests.post('https://enlighten.enphaseenergy.com/login/login.json', headers=headers, data=data)

headers = {'cookie': '_enlighten_4_session=' + session.json()['session_id']}

token = requests.get('https://enlighten.enphaseenergy.com/entrez-auth-token?serial_num=' + config['serial'], headers=headers )

headers = {'Accept': 'application/json', 'Authorization': 'Bearer ' + token.json()['token']}

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(25, GPIO.OUT)
consume = GPIO.PWM(25, 50)
consume.start(50)
GPIO.setup(18, GPIO.OUT)
produce = GPIO.PWM(18, 50)
produce.start(50)

while True:
  try:
    production = requests.get('https://envoy.local/production.json', headers=headers, verify=False)
    # make sure that the 0nth element is the right thing to do here... itterate?
    print('Production: ' + str(production.json()['production'][0]['wNow']) + ' W Consumption: ' + str(production.json()['consumption'][0]['wNow']) + ' W')
    produce.start(translate(clamp(production.json()['production'][0]['wNow'],0,9000),0,9000,0,100))
    consume.start(translate(clamp(production.json()['consumption'][0]['wNow'],0,9000),0,9000,0,100))
  except:
    print('...')
  time.sleep(30)





