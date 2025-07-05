import time
from machine import SoftSPI, Pin
import tinypico as TinyPICO
import micropython
from dotstar import DotStar
from hid_services import Mouse

# --- GPIO Pin Definitions ---
CLK_PIN = 25      # Example: GPIO5 for SNES clock
DATA_PIN = 26    # Example: GPIO23 for SNES data
LATCH_PIN = 27   # Example: GPIO18 for SNES latch

class Device:
    def __init__(self):
        # Define state
        self.x = 0
        self.y = 0

        self.prev_x = 0
        self.prev_y = 0

        # SNES mouse pins
        self.snes_clk = Pin(CLK_PIN, Pin.IN)
        self.snes_data = Pin(DATA_PIN, Pin.IN)
        self.snes_latch = Pin(LATCH_PIN, Pin.IN)

        # Create our device
        self.mouse = Mouse("SNES Mouse BLE")
        # Set a callback function to catch changes of device state
        self.mouse.set_state_change_callback(self.mouse_state_callback)
        # Start our device
        self.mouse.start()

    # Function that catches device status events
    def mouse_state_callback(self):
        if self.mouse.get_state() is Mouse.DEVICE_IDLE:
            return
        elif self.mouse.get_state() is Mouse.DEVICE_ADVERTISING:
            return
        elif self.mouse.get_state() is Mouse.DEVICE_CONNECTED:
            return
        else:
            return

    def advertise(self):
        self.mouse.start_advertising()

    def stop_advertise(self):
        self.mouse.stop_advertising()

    def read_snes_device(self):
        """
        Reads 32 bits from the SNES controller port:
        - First 16 bits: button states (controller or mouse)
        - Second 16 bits: mouse movement (if mouse)
        Returns: (is_mouse, button_bits, movement_bits)
        """
        bits = []

        # Wait for latch pulse (positive going)
        while self.snes_latch.value() == 0:
            #pass
            break
        while self.snes_latch.value() == 1:
            #pass
            break  # Latch pulse ended

        # Protocol: Wait 6us after latch falls before first clock
        time.sleep_us(6)

        # --- First 16 cycles: button states ---
        # Sample first bit immediately (should be valid after latch)
        bits.append(self.snes_data.value())
        for _ in range(15):
            # Wait for clock to go low (falling edge)
            while self.snes_clk.value() == 1:
                #pass
                break
            # Wait for clock to go high (rising edge)
            while self.snes_clk.value() == 0:
                #pass
                break
            # Sample data just after rising edge
            bits.append(self.snes_data.value())

        button_bits = bits.copy()

        # --- Second 16 cycles: mouse movement ---
        # Protocol: There is a ~2.5ms pause before the next 16 clocks
        time.sleep_ms(3)  # 2.5ms rounded up for safety

        move_bits = []
        for _ in range(16):
            # Wait for clock to go low (falling edge)
            while self.snes_clk.value() == 1:
                #pass
                break
            # Wait for clock to go high (rising edge)
            while self.snes_clk.value() == 0:
                #pass
                break
            # Sample data just after rising edge
            move_bits.append(self.snes_data.value())

        # Mouse detection: bit 15 (index 15) of first 16 bits is LOW for mouse, HIGH for controller
        is_mouse = (button_bits[15] == 0)
        return is_mouse, button_bits, move_bits

    def parse_snes_mouse(self, button_bits, move_bits):
        # All bits are active low (0 = active)
        button_bits = [0 if b else 1 for b in button_bits]
        move_bits = [0 if b else 1 for b in move_bits]

        # Mouse buttons: left (cycle 9), right (cycle 10)
        left_button = not button_bits[8]   # Active low
        right_button = not button_bits[9]  # Active low

        # Mouse movement (cycles 17-32)
        y_dir = move_bits[0]
        y_motion = (move_bits[1]<<6) | (move_bits[2]<<5) | (move_bits[3]<<4) | (move_bits[4]<<3) | (move_bits[5]<<2) | (move_bits[6]<<1) | move_bits[7]
        x_dir = move_bits[8]
        x_motion = (move_bits[9]<<6) | (move_bits[10]<<5) | (move_bits[11]<<4) | (move_bits[12]<<3) | (move_bits[13]<<2) | (move_bits[14]<<1) | move_bits[15]
        y = y_motion if y_dir else -y_motion
        x = x_motion if x_dir else -x_motion

        return x, y, left_button, right_button

    # Main loop
    def start(self):
        while True:
            self.check_connection_state()
            is_mouse, button_bits, move_bits = self.read_snes_device()
            if not is_mouse:
                # SNES controller detected, add your controller handling code here
                continue

            self.x, self.y, left, right = self.parse_snes_mouse(button_bits, move_bits)

            # If the variables changed do something depending on the device state
            if (self.x != self.prev_x) or (self.y != self.prev_y):
                self.prev_x = self.x
                self.prev_y = self.y

                if self.mouse.get_state() is Mouse.DEVICE_CONNECTED:
                    self.mouse.set_axes(self.x, self.y)
                    self.mouse.set_buttons(left, right)
                    self.mouse.notify_hid_report()
                elif self.mouse.get_state() is Mouse.DEVICE_IDLE:
                    self.mouse.start_advertising()
                    i = 10
                    while i > 0 and self.mouse.get_state() is Mouse.DEVICE_ADVERTISING:
                        time.sleep(3)
                        i -= 1
                    if self.mouse.get_state() is Mouse.DEVICE_ADVERTISING:
                        self.mouse.stop_advertising()

    def check_connection_state(self):
        if self.mouse.get_state() is Mouse.DEVICE_CONNECTED:
            set_led_color(0, 255, 0)  # Set LED to green when connected
            time.sleep_ms(20)
        else:
            set_led_color(255, 0, 0)  # Set LED to red when not connected
            time.sleep_ms(20)

    # Only for test
    def stop(self):
        self.mouse.stop()

    # Test routine
    def test(self):
        self.mouse.set_battery_level(50)
        self.mouse.notify_battery_level()

        for i in range(30):
            self.mouse.set_axes(100,100)
            self.mouse.set_buttons(1)
            self.mouse.notify_hid_report()
            time.sleep_ms(500)

            self.mouse.set_axes(100,-100)
            self.mouse.set_buttons()
            self.mouse.notify_hid_report()
            time.sleep_ms(500)

            self.mouse.set_axes(-100,-100)
            self.mouse.set_buttons(b2=1)
            self.mouse.notify_hid_report()
            time.sleep_ms(500)

            self.mouse.set_axes(-100,100)
            self.mouse.set_buttons()
            self.mouse.notify_hid_report()
            time.sleep_ms(500)

        self.mouse.set_axes(0,0)
        self.mouse.set_buttons()
        self.mouse.notify_hid_report()

        self.mouse.set_battery_level(100)
        self.mouse.notify_battery_level()


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

def set_led_color(r, g, b):
    global TinyPico
    global dotstar
    # r,g,b = TinyPICO.dotstar_color_wheel( led_color )
    # Set the colour on the dotstar
    dotstar[0] = ( r, g, b, 0.5)

while True:
    d = Device()
    # led_blink()
    # set_led_color(0, 255, 0)
    # time.sleep_ms(10)
    # time.sleep(1)
    d.start()