# HangarBuddy

This code controls an AC/DC relay attached to a Raspberry Pi
with a heater plugged in.

It is designed to have a radio of some sort attached that recieves commands and sends responses or alerts.

## Features

1. Extensibility
1. Hangar environment monitoring
1. Continuous vaporized gas monitoring and alerting
1. Status display
1. Rich text commands and responses

## Acknowledgements

This project started as a fork of piWarmer by Maria DeGrazia.
[https://github.com/mdegrazia/piWarmer](https://github.com/mdegrazia/piWarmer)

I want to extend my many thanks to Maria for starting such an amazing project!

The light sensor code is derived from Ada Fruit's samples.
The temperature code is heavily based on the SunFounder sample code.
The ANALOG gas sensor code is also derived from SunFounder sample code.

## Disclaimer

**HangarBuddy is to be used at your own risk.** It is an
experimental device.

## Commands

The commands are not case sensitive.

| SMS Message | Action                                        |
|-------------|-----------------------------------------------|
| ON          | Turn the Relay/Heater on                      |
| OFF         | Turn the Relay/Heater off                     |
| STATUS      | Return status of the Relay/Heater (on or off) |
| HELP        | Return the list of commands.                  |
| SHUTDOWN    | Shutdown the Pi                               |

## Setup

You will need to modify the HangarBuddy.config file to match your installation.
This file includes a list of phone numbers that are authorized to issue
commands. The file also includes a phone number that any alerts will be sent to.

The basic install process (from scratch):

- Image a micro-SD card using the Raspberry Pi Imager. Keep the user name as `Pi`. You may optionally setup your wifi network name and password.
- In the Pi user directory, make a directory name `src`, navigate into it, then clone the Hangar Buddy repo
- In `/home/user/pi/src/HangarBuddy`, you will need to run and activate a "Python Virtual Environment"
- `python -m venv venv`
- `source ./venv/bin/activate`
- `pip install meshtastic`
- IF you are using an older version of Raspberry Pi OS and NOT using a PI 5: `pip install RPi.GPIO`
- For Pi5 & Bookworm: ``
- `pip install smbus`
- `pip install pyserial`

You will also need to enable some system settings:

- `sudo raspi-config`
- Enable I2C, SPI, 1 Wire Serial, and the Serial interface

## Wiring

**Note**: There are two pin numbering conventions for the Raspberry Pi: Pi numbering and board numbering.

For instance GPIO25 is also known as physical pin 22.

[Raspberry Pi Pin Reference](https://learn.sparkfun.com/tutorials/raspberry-gpio/gpio-pinout)

### Relay

| Wire Color | RPi Pin   | Relay Pin |
|------------|-----------|-----------|
| Red        | GPIO25/22 | "+"       |
| Black      | GND       | "-"       |

#### Meshtastic & Meshcore Devices

**NOTE** : Make sure the antenna is attached before powering on.
**NOTE** : The Raspberry Pi 4C seems VERY picky about the USB cable used to connect a Heltec device. Try multiple cables.

| Wire Color | RPi Pin | Relay Pin |
|------------|---------|-----------|
| Black      | USB-A   | USB-C     |

### MQ2 Gas Sensor

| Wire Color | RPi Pin   | MQ2 Pin |
|------------|-----------|---------|
| white      | 3V        | Vcc     |
| Black      | GND       | GND     |
| Gray       | GP26 / 31 | DO      |

### Temp Sensor

Note that the temperature sensor probably was delivered with a pig-tail harness.

| Wire Color | RPi Pin     | DS18B20 Pin |
|------------|-------------|-------------|
| Black      | GND         | GND         |
| Red        | +5V         | VCC         |
| Yellow     | GPIO 04 / 7 | IN          |

## Light Sensor

**NOTE**: If you have the IO hat installed on the Pi, then you
can use the duplicate SDA/SLC connectors on the set screw
side **AND** the connector pin side.

| Wire Color | RPi Pin | TSL2591 Pin |
|------------|---------|-------------|
| Red        | +3VC    | VCC         |
| Black      | GND     | GND         |
| White      | SDA/03  | SDA         |
| Gray       | SLC/05  | SLC         |

### Status Display

#### Additional Work

You may need to make to "Y" pig tails to support the additional
i2c device. These would split the SDAI and SCLI lines.

**NOTE**: If you do not intend on using both the light sensor AND the display, then you will not not to make pigtails.

| Wire Color | RPi Pin | SF1602 Pin |
|------------|---------|------------|
| Red        | +5V     | VCC        |
| Black      | GND     | GND        |
| White      | SDA     | SDA        |
| Gray       | SCL     | SCL        |

## Additional Links And Setup Notes

### Enable Analog-To-Digital Converter For The MQ-2 Gas Sensor

To do this, you need to enable I2C and 1-Wire using `raspi-config`

```bash
sudo raspi-config
```

- Select Option 5 `Interfacing Options`

- Select Option `P5 I2C` and enable
- Select Option `P7 1-Wire` and enable
- Save changes, exit `raspi-config` and reboot your Raspberry Pi

#### Enable the temperature sensor

Modprobe two modules for the temperature sensor:

```bash
sudo modprobe w1-gpio
sudo modprobe w1-therm
```

## Pairing Meshcore

You will want two meshcore devices.

I suggest using the following 3D printed cases: [Heltec V4 Case](https://www.printables.com/model/1460642-3d-printed-enclosure-for-heltec-v4gps)

The first will be a "Companion USB" that will attach to the Hangar Buddy.

The second will probably be a "Companion Bluetooth" that will be conncted to your phone.

The flasher can be obtained at [flasher.meshcore.co.uk](https://flasher.meshcore.co.uk/)

Make sure both devices are running the same version number of the Meshcore firmware.

You will need to pair the two devices using "adverts". Exact instructions can be found on the Meshcore site.

1. Use [Meshcore App](https://meshcore.liamcottle.net/) to:
    1. Name the device
    1. Set region and bandwidth
    1. Send an advert from the device that will be used for the Hangar Buddy.
1. Use the Mesh Core app on your phone to:
    1. Connect by Bluetooth
    2. Name the device
    3. Send back an advert.
1. Use the Web App to send a direct message from the Hangar Buddy device to your phone paired device.

If you are unable to send messages between the devices, consult the Meshcore documentation, Reddit, or others.

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

- [ ] [Raspberry Pi W, case, and IO pins](https://www.amazon.com/Raspberry-Starter-Power-Supply-Premium/dp/B0748MBFTS/ref=sr_1_3?s=electronics&ie=UTF8&qid=1512070820&sr=1-3&keywords=raspberry+pi+zero+pins)
- [ ] [Adafruit GSM board, SMA edition](https://www.amazon.com/gp/product/B011P07916/ref=oh_aui_detailpage_o02_s00?ie=UTF8&psc=1)
- [ ] [Adafruit 1S Lipo W/ JST connector](https://www.amazon.com/Battery-Packs-Lithium-Polymer-1200mAh/dp/B00J2QET64/ref=sr_1_5?ie=UTF8&qid=1512070675&sr=8-5&keywords=adafruit+lipo)
- [ ] [MicroUSB to USB adapter](https://www.amazon.com/Ksmile%C2%AE-Female-Adapter-SamSung-tablets/dp/B01C6032G0/ref=sr_1_1?dd=tLyVcVfk00xcTUme6zjHhQ%2C%2C&ddc_refnmnt=pfod&ie=UTF8&qid=1512071097&sr=8-1&keywords=micro+usb+adapter&refinements=p_97%3A11292772011)
- [ ] [USB to TTL/Serial adapter](https://www.amazon.com/gp/product/B00QT7LQ88/ref=oh_aui_detailpage_o01_s00?ie=UTF8&psc=1)
- [ ] [Ting GSM Sim Card](https://www.amazon.com/gp/product/B013LKL5IQ/ref=oh_aui_detailpage_o02_s00?ie=UTF8&psc=1)
- [ ] [Iot Power Relay](https://www.amazon.com/gp/product/B00WV7GMA2/ref=oh_aui_detailpage_o01_s01?ie=UTF8&psc=1)
- [ ] [Experimentation board with wires](https://www.amazon.com/gp/product/B01LYN4J3B/ref=oh_aui_detailpage_o08_s00?ie=UTF8&psc=1)

#### Antenna

You will need an antenna, and two options have been tried. One is a small
antenna that will work if the device is near a window or your hangar has good
reception. The 7dbi (high gain) antenna option should be used if reception is an
issue

- [ ] [Adafruit GSM Quadband Antenna](https://www.amazon.com/gp/product/B00N4Y2C4G/ref=oh_aui_detailpage_o08_s00?ie=UTF8&psc=1)
- [ ] [High gain antenna](https://www.amazon.com/gp/product/B01M9F08JR/ref=oh_aui_detailpage_o00_s01?ie=UTF8&psc=1)
- [ ] [Case for Sim800C](https://www.thingiverse.com/thing:5012982)

### For Optional Gas Sensor

- [ ] [Additional wires for breadboard](https://www.amazon.com/gp/product/B072L1XMJR/ref=oh_aui_detailpage_o05_s00?ie=UTF8&psc=1)
- [ ] [SunFounder MQ-2 sensor](https://www.amazon.com/gp/product/B013G8A76E/ref=oh_aui_detailpage_o01_s00?ie=UTF8&psc=1)
- [ ] [SunFounder Analog To Digital Converter](https://www.amazon.com/gp/product/B072J2VCMH/ref=oh_aui_detailpage_o05_s01?ie=UTF8&psc=1)

### For Optional Temperature Sensor

- [ ] [SunFounder Temperature Sensor](https://www.amazon.com/gp/product/B013GB27HS/ref=oh_aui_detailpage_o00_s00?ie=UTF8&psc=1)

### For Optional Light Sensor

- [ ] [Adafruit Light Sensor](https://www.amazon.com/gp/product/B00XW2OFWW/ref=oh_aui_detailpage_o00_s00?ie=UTF8&psc=1)

### For Optional Status Display

- [ ] [SunFounder 1602 LCD](https://www.amazon.com/gp/product/B01E6N19YC/ref=oh_aui_detailpage_o01_s00?ie=UTF8&psc=1)

### Adapters

Depending on the version of Raspberry Pi you are using, you may need an adapter. While not required, it is helpful for setup and trouble shooting to have a monitor.

The Raspberry Pi zero has a mini HDMI port.
The R-Pi 4 and 5 both use micro-HDMI.

## Device Reference

### MQ-2 Sensor

[https://tutorials-raspberrypi.com/configure-and-read-out-the-raspberry-pi-gas-sensor-mq-x/](https://tutorials-raspberrypi.com/configure-and-read-out-the-raspberry-pi-gas-sensor-mq-x/)
[http://www.learningaboutelectronics.com/Articles/MQ-2-smoke-sensor-circuit-with-raspberry-pi.php](http://www.learningaboutelectronics.com/Articles/MQ-2-smoke-sensor-circuit-with-raspberry-pi.php)

### Sunfounder Temp Sensor

[https://www.sunfounder.com/learn/Sensor-Kit-v1-0-for-Raspberry-Pi/lesson-17-ds18b20-temperature-sensor-sensor-kit-v1-0-for-pi.html](https://www.sunfounder.com/learn/Sensor-Kit-v1-0-for-Raspberry-Pi/lesson-17-ds18b20-temperature-sensor-sensor-kit-v1-0-for-pi.html)

## Installation

### OS Image

1. Use Raspberry Pi Imager
1. Choose your device
1. 64bit, Trixie based
1. `hangarbuddy` as custom host name
1. The username  `pi` with password `raspberry` are traditional, but easily guessed
1. Use Wifi for setting up.
1. Enable SSH to help setup and remote in. Use password protection. You do not need "Raspberry Pi Connect"

### First Boot

1. Update (To make sure the raspi-config tool is the latest version)
1. Open a PowerShell or command terminal.
1. `ssh pi@hangarbuddy`
1. Use the password `raspberry`. Accept the fingerprint.
1. `sudo raspi-config`
1. System Options:
    1. Setup wifi if not working yet
    1. boot -> Console Text console
    1. Autologin -> Yes
1. Interface options:
    1. SPI -> Enable
    1. I2C -> Enable
    1. Serial
        1. Allow login: no
        1. Allow serial: yes
    1. TURN OFF 1 wire serial
1. Advanced options:
    1. Expand Filesystem
1. "Finish"
1. `sudo reboot now`
1. Wait for a few minutes, then log back in using the `ssh` command
1. `sudo apt update`
1. `sudo apt upgrade`
1. `lsusb` - Check to see if a "Silicon Labs CP210x UART Bridge" or "Espressif Systems heltec_wifi_lora_32 v4 (16 MB FLASH, 2 MB PSRAM)" is shown.
1. `python --version`. Should be at least 3.13.5

### Source Code

1. Log in to your rasperry pi as the `pi` user.
1. `mkdir src`
1. `cd src`
1. `git clone https://github.com/JohnMarzulli/HangarBuddy/`
1. `cd HangarBuddy`
1. `python -m venv venv`
1. `source ./venv/bin/activate`
1. `pip install -r requirements.txt`
1. `sudo cp hangar_buddy.logrotate.conf /etc/logrotate.d/`
1. `sudo chown root /etc/logrotate.d/hangar_buddy.logrotate.conf`
1. `sudo cp hangar_buddy.service /etc/systemd/system/`
1. `sudo chown root /etc/systemd/system/hangar_buddy.service`
1. `sudo systemctl enable hangar_buddy.service`
1. `sudo reboot`

Once you reboot, the hangar_buddy service should be started automatically.  You can view any startup errors for the service in `/var/log/syslog`.

Running a Python file as a service: <https://gist.github.com/emxsys/a507f3cad928e66f6410e7ac28e2990f>
