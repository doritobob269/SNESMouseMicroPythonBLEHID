import time
from machine import SoftSPI, Pin
import tinypico as TinyPICO
import micropython
from dotstar import DotStar

global color_index
global dotstar
global TinyPico
spi = SoftSPI(sck=Pin( TinyPICO.DOTSTAR_CLK ), mosi=Pin( TinyPICO.DOTSTAR_DATA ), miso=Pin( TinyPICO.SPI_MISO) )
dotstar = DotStar(spi, 1, brightness = 0.5 ) # Just one DotStar, half brightness
color_index = 0
TinyPICO.set_dotstar_power( True )

def led_blink():
    global color_index
    global dotstar
    global TinyPico
    # Get the R,G,B values of the next colour
    r,g,b = TinyPICO.dotstar_color_wheel( color_index )
    # Set the colour on the dotstar
    dotstar[0] = ( r, g, b, 0.5)
    # Increase the wheel index
    color_index += 1
    # Sleep for 20ms so the colour cycle isn't too fast
    #time.sleep_ms(20)

while True:
    # pycom.rgbled(0xFF0000)  # Red
    led_blink()
    time.sleep_ms(10)
    # pycom.rgbled(0x00FF00)  # Green
    # time.sleep(1)
    # pycom.rgbled(0x0000FF)  # Blue
    # time.sleep(1)