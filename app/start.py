import machine
import esp32
from third_party import string
import network
import socket
import os
import utime
import ssl
from third_party import rsa
from umqtt.simple import MQTTClient
from ubinascii import b2a_base64
from machine import RTC, Pin
import ntptime
import ujson
import config
from app.alarm import Bell
from app.alarm import AlarmStateProcessor
from app.alarm import ZoneReading

class RealBell(Bell):

    bellPin = Pin(27, Pin.OUT)

    def switchOn(self):
        self.bellPin.on()
    def switchOff(self):
        self.bellPin.off()

class MqttAlarmStateProcessor(AlarmStateProcessor):

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
    
    def __init__(self, bell):
        self.mqttClient = None
        super().__init__(bell)

    def setMqttClient(self, client):
        self.mqttClient = client

    def publishAlarm(self):
        message = ujson.dumps(self.alarmStatus.export())
        print("Publishing alarm message "+str(message))
        self.sock.sendto(message.encode('utf-8'), ("192.168.0.255", 5935))
        mqtt_topic = '/devices/{}/{}'.format(config.google_cloud_config['device_id'], 'events')
        if (self.mqttClient is not None):
            self.mqttClient.publish(mqtt_topic.encode('utf-8'), message.encode('utf-8'))
    def publishState(self):
        message = ujson.dumps(self.alarmStatus.export())
        print("Publishing state message "+str(message))
        self.sock.sendto(message.encode('utf-8'), ("192.168.0.255", 5935))
        mqtt_topic = '/devices/{}/{}'.format(config.google_cloud_config['device_id'], 'state')
        if (self.mqttClient is not None):
            self.mqttClient.publish(mqtt_topic.encode('utf-8'), message.encode('utf-8'))


bell = RealBell()
mqttAlarmStateProcessor = MqttAlarmStateProcessor(bell)

sta_if = network.WLAN(network.STA_IF)
wdt = machine.WDT(timeout=60000)  # enable it with a timeout of 60s

p0 = Pin(35, Pin.IN, None)
p1 = Pin(34, Pin.IN, None)
p2 = Pin(39, Pin.IN, None)
p3 = Pin(36, Pin.IN, None)
p4 = Pin(16, Pin.IN, None)
p5 = Pin(17, Pin.IN, None)
p6 = Pin(18, Pin.IN, None)
p7 = Pin(19, Pin.IN, None)

zones = [p0, p1, p2, p3, p4, p5, p6, p7]
zoneTypes = ["NC", "NO", "NO", "NC", "NC", "NC", "NC", "NO"]
readings = []

def read_zones():
    l = []
    for zone, zoneType in zip(zones, zoneTypes):
        if (zone.value() == 1):
            if (zoneType == "NC"): 
                l.append(ZoneReading.TRIGGERED)
            else:
                l.append(ZoneReading.NORMAL)
        else:
            if (zoneType == "NC"): 
                l.append(ZoneReading.NORMAL)
            else:
                l.append(ZoneReading.TRIGGERED)
    return l

    
def on_message(topic, message):
    print((topic,message))
    topic = topic.decode('utf-8')
    message = message.decode('utf-8')
    if topic.endswith("/config"):
        o = ujson.loads(message)
        mqttAlarmStateProcessor.config(o)
    if topic.endswith("/commands"):
        print("do nothing")

def connect():
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(config.wifi_config['ssid'], config.wifi_config['password'])
        while not sta_if.isconnected():
            pass
    print('network config: {}'.format(sta_if.ifconfig()))

def set_time():
    ntptime.settime()
    tm = utime.localtime()
    tm = tm[0:3] + (0,) + tm[3:6] + (0,)
    machine.RTC().datetime(tm)
    print('current time: {}'.format(utime.localtime()))

def b42_urlsafe_encode(payload):
    return string.translate(b2a_base64(payload)[:-1].decode('utf-8'),{ ord('+'):'-', ord('/'):'_' })

def create_jwt(project_id, private_key, algorithm, token_ttl):
    print("Creating JWT...")
    private_key = rsa.PrivateKey(*private_key)

    # Epoch_offset is needed because micropython epoch is 2000-1-1 and unix is 1970-1-1. Adding 946684800 (30 years)
    epoch_offset = 946684800
    claims = {
            # The time that the token was issued at
            'iat': utime.time() + epoch_offset,
            # The time the token expires.isAlarmActive
            'exp': utime.time() + epoch_offset + token_ttl,
            # The audience field should always be set to the GCP project id.
            'aud': project_id
    }

    #This only supports RS256 at this time.
    header = { "alg": algorithm, "typ": "JWT" }
    content = b42_urlsafe_encode(ujson.dumps(header).encode('utf-8'))
    content = content + '.' + b42_urlsafe_encode(ujson.dumps(claims).encode('utf-8'))
    signature = b42_urlsafe_encode(rsa.sign(content,private_key,'SHA-256'))
    return content+ '.' + signature #signed JWT

def get_mqtt_client(project_id, cloud_region, registry_id, device_id, jwt):
    client_id = 'projects/{}/locations/{}/registries/{}/devices/{}'.format(project_id, cloud_region, registry_id, device_id)
    client = MQTTClient(client_id.encode('utf-8'),server=config.google_cloud_config['mqtt_bridge_hostname'],port=config.google_cloud_config['mqtt_bridge_port'],user=b'ignored',password=jwt.encode('utf-8'),ssl=True)
    client.set_callback(on_message)
    client.connect()
    client.subscribe('/devices/{}/config'.format(device_id), 1)
    client.subscribe('/devices/{}/commands/#'.format(device_id), 1)
    return client

def wait_for_readings_change():
    global readings
    i = 0
    lastReadings = readings
    readings = read_zones()
    while i < 100 and lastReadings == readings:
        utime.sleep_ms(10)
        i = i + 1
        lastReadings = readings
        readings = read_zones()
    return (lastReadings != readings)


connect()
#Need to be connected to the internet before setting the local RTC.
set_time()

jwt = create_jwt(config.google_cloud_config['project_id'], config.jwt_config['private_key'], config.jwt_config['algorithm'], config.jwt_config['token_ttl'])
client = get_mqtt_client(config.google_cloud_config['project_id'], config.google_cloud_config['cloud_region'], config.google_cloud_config['registry_id'], config.google_cloud_config['device_id'], jwt)
mqttAlarmStateProcessor.setMqttClient(client)

mainLoopCntr = 0

while True:
    wdt.feed()
    mainLoopCntr = mainLoopCntr + 1
    # if nothing has changed, blocks for 1 seconds and then returns false
    if wait_for_readings_change():
        mqttAlarmStateProcessor.handleZonesUpdate(readings)
        utime.sleep(10)  # Delay for 10 seconds. Prevent excessive updates if inputs are unstable
    if (mainLoopCntr % 600 == 0): # about each 10 minutes to prevent idle connection close for GCP IoT server
        mqttAlarmStateProcessor.publishState()
    
    mqttAlarmStateProcessor.handleTick()
    client.check_msg() # Check for new messages on subscription
    
