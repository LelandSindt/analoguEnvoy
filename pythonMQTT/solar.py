#!/usr/bin/python -u
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO

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


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("homeassistant/sensor/envoy_2022xxxxxxxx_current_power_consumption/state")
    client.subscribe("homeassistant/sensor/envoy_2022xxxxxxxx_current_power_production/state")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    if msg.topic == "homeassistant/sensor/envoy_2022xxxxxxxx_current_power_consumption/state":
      consume.start(translate(clamp(int(msg.payload),0,9000), 0, 9000, 0, 100))
    if msg.topic == "homeassistant/sensor/envoy_2022xxxxxxxx_current_power_production/state":
      produce.start(translate(clamp(int(msg.payload),0,9000), 0, 9000, 0, 100))

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(25, GPIO.OUT)
consume = GPIO.PWM(25, 50)
consume.start(50)
GPIO.setup(18, GPIO.OUT)
produce = GPIO.PWM(18, 50)
produce.start(50)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("192.168.1.50", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
