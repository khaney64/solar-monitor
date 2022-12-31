# The goal of this project was to create a device to gather solar strength information in various locations on my property 
# to determine where to potentially place some solar panels.
# A custom circuit using an INA219 High Side DC Current Sensor to measure voltage and current of a 6 Volt, 2 Watt solar panel
# across a resistor load.  The cicuit is attached to a Raspberry Pi zero I2C bus.  An optional I2C display can be used to display
# voltage, power, pi temperature and wifi signal strength.
# The data is captured and sent to influxdb, and graphed with grafana.
#
# a battery pack was used to provide at least a days worth of power so the device could be left outside in various locations.
#
# This code runs on the Raspberry Pi, and connects to the INA219 High Side DC Current Sensor on the I2C bus.
#
# package requirements:
# ina219 - sudo pip install pi-ina219
# influxdb_client - sudo pip install influxdb-client
# I2C_LCD_driver.py package (included here)
#
# hardware:
# ina219 - https://www.adafruit.com/product/904
# Voltaic Systems 6V 2W solar panel - https://www.adafruit.com/product/5366
# Hammer Header Male solderless Connector - https://www.adafruit.com/product/3662
# a few resistors or trim pot to disipate up to 2 Watts of power at peak
# connectors/wires to connect to the I2C bus and power on the Pi's GPIO.
#
# .influxdb config file should contain the following information to connect to the influx db:
# {
#    "url": "http://<your host>:<your port>",
#    "bucket": "<the influxdb bucket to put data in",
#    "org": "<your organization id>",
#    "token": "<your server token"
# }
#
# program requires at least on input, the location, which is used as the location tag in influxdb
# optional parameters:
# - display (second), defaults ot false, and will send results to a  
#
# to confirm i2c devices are connected - should ad least see the i2c, and optionally, the display.
# Note that the I2C_LCD_driver.py has the address for the INA219 hard coded (current x3F) - change it if necessary.
# sudo i2cdetect -y 1

#!/usr/bin/env python
from ina219 import INA219
from ina219 import DeviceRangeError
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import I2C_LCD_driver
import time
import time
import logging
import sys
import subprocess
import re
import json

SHUNT_OHMS = 0.1

MaxVoltage = 0.0
MaxShunt = 0.0
MaxCurrent = 0.0
MaxPower = 0.0
MaxTemperature = 0.0

class Data:
    def __init__(self, voltage, shunt, current, power, temperature, signal):
        self.voltage = voltage
        self.shunt = shunt
        self.current = current
        self.power = power
        self.temperature = temperature
        self.signal = signal

def piTemp():
    try:
        tempraw = subprocess.run(['vcgencmd', 'measure_temp'], stdout=subprocess.PIPE).stdout.decode('utf-8').split("=")
        temp = re.sub(r'[^0-9.]', '', tempraw[1])
        return float(temp)
    except Exception as e:
        print("Error getting temp\n%s" % e)
        return 0.0

def signalStrength():
    try:
        # iw wlan0 station dump | grep signal
        cmd = ['iw', 'wlan0', 'station', 'dump']
        iw = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        cmd = ['grep', 'signal']
        grep = subprocess.Popen(cmd, stdin=iw.stdout, stdout=subprocess.PIPE,
                                encoding='utf-8')
        iw.stdout.close()
        output, _ = grep.communicate()
        grep.stdout.close()
        decibels = int(output.split(":")[1].split(" ")[2])
        return decibels
    except Exception as e:
        return 0

def read():
    global MaxVoltage
    global MaxShunt
    global MaxCurrent
    global MaxPower
    global MaxTemperature

    ina = INA219(SHUNT_OHMS, address=0x40, busnum=1, log_level=logging.ERROR)
    try:
        ina.configure(ina.RANGE_16V, ina.GAIN_1_40MV)
    except Exception as e:
        print(f"Exception configuring ina {e}")
        return None

    voltage = ina.voltage()
    if voltage > MaxVoltage:
        MaxVoltage = voltage
    print("Bus Voltage: %.3f V" % voltage)
    try:
        current = ina.current()
        power = ina.power()
        shunt = ina.shunt_voltage()
        if shunt > MaxShunt:
            MaxShunt = shunt
        if current > MaxCurrent:
            MaxCurrent = current
        if power > MaxPower:
            MaxPower = power
        print("Bus Current: %.3f mA" % current)
        print("Power: %.3f mW" % power)
        print("Shunt voltage: %.3f mV" % shunt)

        temperature = piTemp()
        if temperature > MaxTemperature:
            MaxTemperature = temperature
        print("Pi Temperature: %.3f C" % temperature)

        signal = signalStrength()
        print("Signal Strength: %2d dBm\n" % signal)

        data = Data(voltage, shunt, current, power, temperature, signal)
        return data

    except DeviceRangeError as e:
        # Current out of device range with specified shunt resistor
        print(e)

def write(config, location, data):
    url = config['url']
    bucket = config['bucket']
    org = config['org']
    token = config['token']

    client = influxdb_client.InfluxDBClient(
      url=url,
      token=token,
      org=org
    )

    points = []

    write_api = client.write_api(write_options=SYNCHRONOUS)
    p = influxdb_client.Point(location).tag("location", location).tag("measurement","bus_voltage").tag("units","Volt").field("value", data.voltage)
    points.append(p)
    p = influxdb_client.Point(location).tag("location", location).tag("measurement","shunt_voltage").tag("units","mVolt").field("value", data.shunt)
    points.append(p)
    p = influxdb_client.Point(location).tag("location", location).tag("measurement","bus_current").tag("units","mAmp").field("value", data.current)
    points.append(p)
    p = influxdb_client.Point(location).tag("location", location).tag("measurement","power").tag("units","mWatt").field("value", data.power)
    points.append(p)
    p = influxdb_client.Point(location).tag("location", location).tag("measurement","temperature").tag("units","Celcius").field("value", data.temperature)
    points.append(p)
    p = influxdb_client.Point(location).tag("location", location).tag("measurement","signal_strength").tag("units","dBm").field("value", float(data.signal))
    points.append(p)

    write_api.write(bucket=bucket, org=org, record=points)
#    print(f"Wrote {len(points)} points")

def write_with_retry(config, location, data, tries, delay):
    attempts = 0
    success = False
    while not success and attempts < tries:
        try:
           attempts = attempts + 1
           signal = signalStrength() 
           write(config, location, data)  
           success = True 
           break;
        except Exception as e:
           print(f"Write failed, attempt {attempts} of {tries} waiting {delay} ({signal} dBm)")
           time.sleep(delay)
    if not success:
        print(f"data lost after {tries} retries")    

def display(data):
    mylcd = I2C_LCD_driver.lcd()
    mylcd.lcd_clear()
    mylcd.backlight(0)
    mylcd.lcd_display_string("%.3f V %.3f mW" % (data.voltage, data.power), 1)
#    mylcd.lcd_display_string("%.3f mA" % (data.current), 2)
    mylcd.lcd_display_string("%.1f C   %2d dBm" % (data.temperature, data.signal), 2)

def display_off():
    mylcd = I2C_LCD_driver.lcd()
    mylcd.lcd_clear()

if __name__ == "__main__":
    useDisplay = False
    delay = 30
    if (len(sys.argv) < 2):
      print("usage\n monitor location [display=False] [delay=30]")
      exit()

    if (len(sys.argv) > 2):
        useDisplay = eval(sys.argv[2])
        print(f"useDisplay = {useDisplay}")
    if (len(sys.argv) > 3):
        delay = int(sys.argv[3])
        print(f"delay = {delay}")

    try:
        with open('.influxdb','r') as influx_config_file:
            influx_config = json.load(influx_config_file)
        print('found username file')
    except FileNotFoundError:
        print('did not find .influxdb file')
        exit()
    print(influx_config)
    print(f"Writing to influx server {influx_config['url']}, bucket {influx_config['bucket']}")

    try:
        while True:
            data = read()
            if data: 
                write_with_retry(influx_config, sys.argv[1], data, 5, 3)
                if useDisplay:
                    display(data)
            time.sleep(delay)    
    except KeyboardInterrupt:
        print("\nMax Voltage: %.3f V" % MaxVoltage)
        print("Max Shunt: %.3f mV" % MaxShunt)
        print("Max Current: %.3f mA" % MaxCurrent)
        print("Max Power: %.3f mW" % MaxPower)
