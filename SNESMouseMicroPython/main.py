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

startup_flag = False

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
        global startup_flag
        if self.mouse.get_state() is Mouse.DEVICE_IDLE:
            print("idle")
            set_led_color(255, 0, 0)
            if(startup_flag):
                self.mouse.start_advertising()
            return
        elif self.mouse.get_state() is Mouse.DEVICE_ADVERTISING:
            print("advertising")
            startup_flag = True
            set_led_color(0, 0, 255)
            return
        elif self.mouse.get_state() is Mouse.DEVICE_CONNECTED:
            print("connected")
            set_led_color(0, 255, 0)
            return
        else:
            return

    def advertise(self):
        self.mouse.start_advertising()

    def stop_advertise(self):
        self.mouse.stop_advertising()

    def read_snes_device(self, prev_latch_state):
        """
        Reads 32 bits from the SNES controller port:
        - First 16 bits: button states (controller or mouse)
        - Second 16 bits: mouse movement (if mouse)
        Returns: (is_mouse, button_bits, movement_bits, new_latch_state)
        Only reads when a positive edge (0->1) is detected on latch.
        """
        bits = []

        latch_now = self.snes_latch.value()
        if prev_latch_state == 0 and latch_now == 1:
            # Positive edge detected

            # Do NOT wait for latch pulse to end (fully non-blocking)
            # Protocol: Wait 6us after latch goes high before first clock
            time.sleep_us(6)

            # --- First 16 cycles: button states ---
            bits.append(self.snes_data.value())
            for _ in range(15):
                while self.snes_clk.value() == 1:
                    pass
                while self.snes_clk.value() == 0:
                    pass
                bits.append(self.snes_data.value())

            button_bits = bits.copy()

            # --- Second 16 cycles: mouse movement ---
            time.sleep_ms(3)  # 2.5ms rounded up for safety

            move_bits = []
            for _ in range(16):
                while self.snes_clk.value() == 1:
                    pass
                while self.snes_clk.value() == 0:
                    pass
                move_bits.append(self.snes_data.value())

            is_mouse = (button_bits[15] == 0)
            return is_mouse, button_bits, move_bits, latch_now
        else:
            # No positive edge, nothing to read
            return None, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], None, latch_now

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
        prev_latch_state = self.snes_latch.value()
        if self.mouse.get_state() is Mouse.DEVICE_IDLE:
            self.mouse.start_advertising()
        while True:
            # self.test()
            is_mouse, button_bits, move_bits, prev_latch_state = self.read_snes_device(prev_latch_state)
            # self.mouse.notify_hid_report()
            if not is_mouse:
                # SNES controller detected, add your controller handling code here
                # print("Controller")
                # Print button bits as a table with SNES button names
                button_names = [
                    "B", "Y", "s", "S", "^", "v", "<", ">",
                    "A", "X", "L", "R", "-", "-", "-", "I"
                ]
                print("| " + " | ".join(button_names) + " |")
                print("|" + "|".join("---" for _ in button_names) + "|")
                print("| " + " | ".join(str(bit) for bit in button_bits) + " |")
                print("=" * (1 + len(button_names) * 4))
                continue

            else:
                # print("Mouse")
                self.x, self.y, left, right = self.parse_snes_mouse(button_bits, move_bits)

                # If the variables changed do something depending on the device state
                if (self.x != self.prev_x) or (self.y != self.prev_y):
                    self.prev_x = self.x
                    self.prev_y = self.y

                    # if self.mouse.get_state() is Mouse.DEVICE_CONNECTED:
                    #     self.mouse.set_axes(self.x, self.y)
                    #     self.mouse.set_buttons(left, right)
                    #     self.mouse.notify_hid_report()
                    # elif self.mouse.get_state() is Mouse.DEVICE_IDLE:
                    #     self.mouse.start_advertising()
                    #     i = 10
                    #     while i > 0 and self.mouse.get_state() is Mouse.DEVICE_ADVERTISING:
                    #         time.sleep(3)
                    #         i -= 1
                    #     if self.mouse.get_state() is Mouse.DEVICE_ADVERTISING:
                    #         self.mouse.stop_advertising()

    # Only for test
    def stop(self):
        self.mouse.stop()

    # Test routine
    def test(self):
        self.mouse.set_battery_level(50)
        self.mouse.notify_battery_level()

        for i in range(30):
            self.mouse.set_axes(100,100)
            self.mouse.set_buttons()
            try:
                self.mouse.notify_hid_report()
            except:
                print("Error notifying HID report")

            time.sleep_ms(500)

            self.mouse.set_axes(100,-100)
            self.mouse.set_buttons()
            try:
                self.mouse.notify_hid_report()
            except:
                print("Error notifying HID report")
            time.sleep_ms(500)

            self.mouse.set_axes(-100,-100)
            self.mouse.set_buttons()
            try:
                self.mouse.notify_hid_report()
            except:
                print("Error notifying HID report")
            time.sleep_ms(500)

            self.mouse.set_axes(-100,100)
            self.mouse.set_buttons()
            try:
                self.mouse.notify_hid_report()
            except:
                print("Error notifying HID report")
            time.sleep_ms(500)

        self.mouse.set_axes(0,0)
        self.mouse.set_buttons()
        try:
            self.mouse.notify_hid_report()
        except:
            print("Error notifying HID report")

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