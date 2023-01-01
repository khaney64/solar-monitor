# Raspberry Pi / INA219 Solar Monitor
The goal of this project was to create a device to gather solar strength information in various locations on my property to determine where to potentially place some solar panels.
A custom circuit using an INA219 High Side DC Current Sensor to measure voltage and current of a 6 Volt, 2 Watt solar panel across a resistor load.  The cicuit is attached to a Raspberry Pi zero I2C bus.  An optional I2C display can be used to display voltage, power, pi temperature and wifi signal strength.

The data is captured and sent to influxdb, and graphed with grafana.

A battery pack was used to provide at least a days worth of power so the device could be left outside in various locations.

This code runs on the Raspberry Pi, and connects to the INA219 High Side DC Current Sensor on the I2C bus.

**package requirements**:
ina219 - sudo pip install pi-ina219
influxdb_client - sudo pip install influxdb-client
I2C_LCD_driver.py package (included here)

**hardware**:
- [ina219](https://www.adafruit.com/product/904)
- [Voltaic Systems 6V 2W solar panel](https://www.adafruit.com/product/5366)
- [Hammer Header Male solderless Connector](https://www.adafruit.com/product/3662)
- a few resistors or trim pot to disipate up to 2 Watts of power at peak
- connectors/wires to connect to the I2C bus and power on the Pi's GPIO.

.influxdb config file should contain the following information to connect to the influx db:
>{
   "url": "http://<your host>:<your port>",
   "bucket": "<the influxdb bucket to put data in",
   "org": "<your organization id>",
   "token": "<your server token"
}

The program requires at least on input, the location, which is used as the location tag in influxdb
**optional parameters**:
- display (second), defaults ot false, and will send results to an I2C enabled lcd display
- delay (third), defaults to 30, how often to query the INA219 and sends results to influxdb

To confirm i2c devices are connected, run the following:
> sudo i2cdetect -y 1

You should ad least see the i2c, and optionally, the display.
Note that the I2C_LCD_driver.py has the address for the INA219 hard coded (current x3F) - change it if necessary.

Here is the assembled monitor:
![monitor](/screenshots/monitor-1.png)


Inside the monitor:
![inside](/screenshots/monitor-2.png)


RPI connections to GPIO, power and wifi usb dongle:
![rpi connections](/screenshots/monitor-3.png)


Yellow and Orange cables are Scl and Sda lines from RPI, to display and INA219
![i2c bus](/screenshots/monitor-4.png)


INA219 board (yes, I put the V+/V- connector on backwards!)
![ina219 top](/screenshots/monitor-5.png)


Bottom of the INA219, 3.3V, Ground, Sda and Scl to the RPI
![ina219 bottom](/screenshots/monitor-6.png)


Connector board to take solar panel + connector to the V+ on INA219,
V- from INA219 to an string of resistors in series (or a trimpot), either grounded.  The goal here was disipate about 250 mA at 6V peek.
The pot isn't rated for 2 Watts, it worked but got pretty hot.
Resistors should be a little beefier as well (note the discoloration on the right most resistor (it was getting warm!)
![power and load board](/screenshots/monitor-7.png)


[This](https://www.amazon.com/gp/product/B07JYYRT7T) Charmast 10400 mA portable charger gets me at least 12-15 hours of time on the pi-zero, so I can set it up outside the night before, and let it run through the day to gather data.
![portable charger](/screenshots/monitor-8.png)


I used Grafana to display my data, so I can compare various locations to see when they receive maximum sun.  I should be able to use this information to estimate what sort of power I could get from "real" solar panels.
![grafana displa](/screenshots/grafana.png)