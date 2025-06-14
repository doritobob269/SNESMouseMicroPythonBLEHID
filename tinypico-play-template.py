# TinyPICO Play Shield MicroPython Starting Template
# 2019 Seon Rozenblum
#
# Project home:
#   https://github.com/TinyPICO
#
# 2019-July-20 - v1.0 - Initial Release

"""
`tinypico play` - MicroPython TinyPICO Play Shield Template
===========================================================

* Author(s): Seon Rozenblum
"""

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/TinyPICO/tinypico-micropython"

# Import required libraries
import tinypico as TinyPICO
import micropython
from machine import I2C, Pin, SoftSPI
from dotstar import DotStar
import time

# Hardware Pin Assignments

# Buttons
BUT_1 = Pin( 26, Pin.IN )
BUT_2 = Pin( 27, Pin.IN )
BUT_3 = Pin( 15, Pin.IN )
BUT_4 = Pin( 14, Pin.IN )

# Light  Sensor
LIGHT_SENS = Pin( 32, Pin.IN )

# Speaker
SPEAKER = Pin( 25, Pin.OUT )

# Blue LED
LED = Pin( 4, Pin.OUT )

# Setup

# Turn off the power to the DotStar

# Create a colour wheel index int

spi = SoftSPI(sck=Pin( TinyPICO.DOTSTAR_CLK ), mosi=Pin( TinyPICO.DOTSTAR_DATA ), miso=Pin( TinyPICO.SPI_MISO) ) 
dotstar = DotStar(spi, 1, brightness = 0.1 ) # Just one DotStar, half brightness
color_index = 0
TinyPICO.set_dotstar_power( True )

# Rainbow colours on the Dotstar
while True:
    # Get the R,G,B values of the next colour
    r,g,b = TinyPICO.dotstar_color_wheel( color_index )
    # Set the colour on the dotstar
    dotstar[0] = ( r, g, b, 0.1)
    # Increase the wheel index
    color_index += 1
    # Sleep for 20ms so the colour cycle isn't too fast
    time.sleep_ms(20)

# Configure I2C for controlling anything on the I2C bus
# Software I2C only for this example but the next version of MicroPython for the ESP32 supports hardware I2C too
#i2c = I2C(scl=Pin(22), sda=Pin(21))

# Example initialisers for the  OLED and IMU

# Initialise the LIS3HD 3-Axis IC
# imu = lis3dh.LIS3DH_I2C(i2c)

# Initialise the OLED screen
# oled = ssd1306.SSD1306_I2C(128, 64, i2c)
