# piWarmer

This is a Python scipt that controls an AC/DC relay attached to a Raspberry Pi
with a space heater plugged in. There is an adafruit GSM Board that receives
text messages using a Ting SIM card connected to the Raspberry Pi. When the Pi
receives a text messgae it will turn the AC/DC relay on or off accordingly, thus
powering the heater on or off. The following are a list of commands that can be
sent to the Pi that will control the heater:

## Acknowledgements

This version was based on
[https://github.com/mdegrazia/piWarmer](https://github.com/mdegrazia/piWarmer)

I want to extend my many thanks to Maria for starting such an amazing project

The light sensor code is from "arenadorn" and
[tsl2591](https://github.com/maxlklaxl/python-tsl2591/blob/master/tsl2591/read_tsl.py)

## Disclaimer

\***\*piWarmer is to be used at your own risk\**** This version of the code has
been modified to increase the reliability and safety of the device, but it is an
experimental device.

## Commands

The commands are not case sensitive.

| SMS Message | Action                                        |
| ----------- | --------------------------------------------- |
| ON          | Turn the Relay/Heater on                      |
| OFF         | Turn the Relay/Heater off                     |
| STATUS      | Return status of the Relay/Heater (on or off) |
| HELP        | Return the list of piWarmer commands.         |
| SHUTDOWN    | Shutdown the Pi                               |

## Setup

You will need to modify the piWarmer.config file to match your installation.
This file includes a list of phone numbers that are authorized to issue
commands. The file also includes a phone number that any alerts will be sent to.

For a complete set of installation instructions, visit
[https://github.com/mdegrazia/piWarmer/wiki](https://github.com/mdegrazia/piWarmer/wiki).

## Wiring

**Note**: GPIO25 is physical pin 22

### Relay

* Red wire from GPIO25 to Relay "+"
* Black wire from Relay "-" to GPIO GND

### Fona

#### Fona Serial/Modem Communication

* TTL Black to Fona "GND"
* TTL White to Fona "TX"
* TTL Green to Fona "RX"
* TTL Red to Fona "Vio"
* USB to Pi USB

#### Fona Status

* ORANGE Fona PS to GPIO23
* YELLOW Fona Key to GPIO GND
* GREEN Fona RI to GPIO24

#### Fona Power... Again

* USB power into the Fona mini-USB port

**Note**:GPIO23 is physical pin 16 **Note**:GPIO24 is physical pin 18

### MQ2 Gas Sensor / ADC

#### ADC

* Red F/M: VCC to GPIO 3V3
* Black ADC GND to GPIO GND
* White ADC SDA to GPIO SDAI
* Gray ADC SCL to GPIO SCLI
* White F/F ADC AIN0 to MQ2 White

#### MQ2

* Pigtail Connector into reciever
* Red to GPIO 3V3
* Black to GPIO GND
* Brown to GPIO 12

### Temp Sensor

* White plug into Temp Sensor
* Yellow to GPIO04
* Red to +5VO
* Black to GPIO GND

## Additional Links And Setup Notes

**The MQ-2 needs to be installed with an analog-to-digital converter** You
need to enable I2C using `raspi-config` You need to modprobe two modules for the
temperature sensor to work `w1-gpio` and `w1-therm`

## Materials List

All the parts listed are from Amazon

### Absolutely Required

This assumes you are building "from scratch" and need to buy a Raspberry Pi and
associate parts. I have picked a version of the Pi Zero that has Wireless, which
is good if you want to pull the code down directly onto the Pi

Any version of the Raspberry Pi should work for this project as long as it has
GPIO pins, and an I2C bus.

The LiPo battery is absolutely required and used directly by the GSM board.

A MicroUSB to USB adapter is required for the modem to connect into the Pi
Zero's ****only**** USB port.

* [ ] [Raspberry Pi W, case, and IO pins](https://www.amazon.com/Raspberry-Starter-Power-Supply-Premium/dp/B0748MBFTS/ref=sr_1_3?s=electronics&ie=UTF8&qid=1512070820&sr=1-3&keywords=raspberry+pi+zero+pins)
* [ ] [Adafruit GSM board, SMA edition](https://www.amazon.com/gp/product/B011P07916/ref=oh_aui_detailpage_o02_s00?ie=UTF8&psc=1)
* [ ] [Adafruit 1S Lipo W/ JST connector](https://www.amazon.com/Battery-Packs-Lithium-Polymer-1200mAh/dp/B00J2QET64/ref=sr_1_5?ie=UTF8&qid=1512070675&sr=8-5&keywords=adafruit+lipo)
* [ ] [MicroUSB to USB adapter](https://www.amazon.com/Ksmile%C2%AE-Female-Adapter-SamSung-tablets/dp/B01C6032G0/ref=sr_1_1?dd=tLyVcVfk00xcTUme6zjHhQ%2C%2C&ddc_refnmnt=pfod&ie=UTF8&qid=1512071097&sr=8-1&keywords=micro+usb+adapter&refinements=p_97%3A11292772011)
* [ ] [USB to TTL/Serial adapter](https://www.amazon.com/gp/product/B00QT7LQ88/ref=oh_aui_detailpage_o01_s00?ie=UTF8&psc=1)
* [ ] [Ting GSM Sim Card](https://www.amazon.com/gp/product/B013LKL5IQ/ref=oh_aui_detailpage_o02_s00?ie=UTF8&psc=1)
* [ ] [Iot Power Relay](https://www.amazon.com/gp/product/B00WV7GMA2/ref=oh_aui_detailpage_o01_s01?ie=UTF8&psc=1)
* [ ] [Experimentation board with wires](https://www.amazon.com/gp/product/B01LYN4J3B/ref=oh_aui_detailpage_o08_s00?ie=UTF8&psc=1)

#### Antenna

You will need an antenna, and two options have been tried. One is a small
antenna that will work if the device is near a window or your hangar has good
reception. The 7dbi (high gain) antenna option should be used if reception is an
issue

* [ ] [Adafruit GSM Quadband Antenna](https://www.amazon.com/gp/product/B00N4Y2C4G/ref=oh_aui_detailpage_o08_s00?ie=UTF8&psc=1)
* [ ] [High gain antenna](https://www.amazon.com/gp/product/B01M9F08JR/ref=oh_aui_detailpage_o00_s01?ie=UTF8&psc=1)

### For Optional Gas Sensor

* [ ] [Additional wires for breadboard](https://www.amazon.com/gp/product/B072L1XMJR/ref=oh_aui_detailpage_o05_s00?ie=UTF8&psc=1)
* [ ] [SunFounder MQ-2 sensor](https://www.amazon.com/gp/product/B013G8A76E/ref=oh_aui_detailpage_o01_s00?ie=UTF8&psc=1)
* [ ] [SunFounder Analog To Digital Converter](https://www.amazon.com/gp/product/B072J2VCMH/ref=oh_aui_detailpage_o05_s01?ie=UTF8&psc=1)

### For Optional Temperature Sensor

* [ ] [SunFounder Temperature Sensor](https://www.amazon.com/gp/product/B013GB27HS/ref=oh_aui_detailpage_o00_s00?ie=UTF8&psc=1)

### For Optional Light Sensor

** THIS CODE AND OPTION ARE NOT YET TESTED! **

* [ ] [Adafruit Light Sensor](https://www.amazon.com/gp/product/B00XW2OFWW/ref=oh_aui_detailpage_o00_s00?ie=UTF8&psc=1)

### Adapters

The Raspberry Pi zero uses a mini HDMI port for display. If you do not have an
adapter, you will need one. This is not required in the installation once the
device is "deployed". The USB hub makes coding and debugging on the PI possible
as it allows a keyboard, mouse, and the Fona modem to be connected
simultanously. When the piWarmer is "deployed" only the Fona will be plugged
into the USB port.

* [ ] [MiniHDMI to HDMI adapter](https://www.amazon.com/Adapter-VCE-Converter-Camcorder-Devices/dp/B01HYURR04/ref=sr_1_8?s=electronics&ie=UTF8&qid=1512070954&sr=1-8&keywords=mini+hdmi+adapter)
* [ ] [USB Hub](https://www.amazon.com/gp/product/B00XMD7KPU/ref=oh_aui_detailpage_o02_s00?ie=UTF8&psc=1)

## Device Reference

### MQ-2 Sensor

[https://tutorials-raspberrypi.com/configure-and-read-out-the-raspberry-pi-gas-sensor-mq-x/](https://tutorials-raspberrypi.com/configure-and-read-out-the-raspberry-pi-gas-sensor-mq-x/)
[http://www.learningaboutelectronics.com/Articles/MQ-2-smoke-sensor-circuit-with-raspberry-pi.php](http://www.learningaboutelectronics.com/Articles/MQ-2-smoke-sensor-circuit-with-raspberry-pi.php)

### Sunfounder Temp Sensor

[https://www.sunfounder.com/learn/Sensor-Kit-v1-0-for-Raspberry-Pi/lesson-17-ds18b20-temperature-sensor-sensor-kit-v1-0-for-pi.html](https://www.sunfounder.com/learn/Sensor-Kit-v1-0-for-Raspberry-Pi/lesson-17-ds18b20-temperature-sensor-sensor-kit-v1-0-for-pi.html)

### Adafruit Fona

[https://learn.adafruit.com/adafruit-fona-808-cellular-plus-gps-breakout?view=all](https://learn.adafruit.com/adafruit-fona-808-cellular-plus-gps-breakout?view=all)
[https://learn.adafruit.com/adafruit-fona-mini-gsm-gprs-cellular-phone-module?view=all](https://learn.adafruit.com/adafruit-fona-mini-gsm-gprs-cellular-phone-module?view=all)
[https://learn.adafruit.com/adafruit-fona-mini-gsm-gprs-cellular-phone-module/handy-commands](https://learn.adafruit.com/adafruit-fona-mini-gsm-gprs-cellular-phone-module/handy-commands)
[https://cdn-learn.adafruit.com/downloads/pdf/adafruit-fona-mini-gsm-gprs-cellular-phone-module.pdf](https://cdn-learn.adafruit.com/downloads/pdf/adafruit-fona-mini-gsm-gprs-cellular-phone-module.pdf)
