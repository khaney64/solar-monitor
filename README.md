# solar-monitor
The goal of this project was to create a device to gather solar strength information in various locations on my property 
to determine where to potentially place some solar panels.
A custom circuit using an INA219 High Side DC Current Sensor to measure voltage and current of a 6 Volt, 2 Watt solar panel
across a resistor load.  The cicuit is attached to a Raspberry Pi zero I2C bus.  An optional I2C display can be used to display
voltage, power, pi temperature and wifi signal strength.
The data is captured and sent to influxdb, and graphed with grafana.

a battery pack was used to provide at least a days worth of power so the device could be left outside in various locations.

This code runs on the Raspberry Pi, and connects to the INA219 High Side DC Current Sensor on the I2C bus.

package requirements:
ina219 - sudo pip install pi-ina219
influxdb_client - sudo pip install influxdb-client
I2C_LCD_driver.py package (included here)

hardware:
ina219 - <a href="https://www.adafruit.com/product/904" /a>
Voltaic Systems 6V 2W solar panel - <a href="https://www.adafruit.com/product/5366" /a>
Hammer Header Male solderless Connector - <a href="https://www.adafruit.com/product/3662" /a>
a few resistors or trim pot to disipate up to 2 Watts of power at peak
connectors/wires to connect to the I2C bus and power on the Pi's GPIO.

.influxdb config file should contain the following information to connect to the influx db:
{
   "url": "http://<your host>:<your port>",
   "bucket": "<the influxdb bucket to put data in",
   "org": "<your organization id>",
   "token": "<your server token"
}

program requires at least on input, the location, which is used as the location tag in influxdb
optional parameters:
- display (second), defaults ot false, and will send results to an I2C enabled lcd display
- delay (third), defaults to 30, how often to query the INA219 and sends results to influxdb

to confirm i2c devices are connected - should ad least see the i2c, and optionally, the display.
Note that the I2C_LCD_driver.py has the address for the INA219 hard coded (current x3F) - change it if necessary.
sudo i2cdetect -y 1
