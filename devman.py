import machine
import time

class DeviceManager:
    def __init__(self):
        self.pins = {}
        self.adc_pins = {}
        self.pwm_pins = {}
        self.reserved_pins = {
            25: "LED",  # onboard LED
            4: "ADC_TEMP"  # internal temperature sensor
        }
        
    def register_pin(self, pin_num, name, mode="out", pull=None):
        """Register a GPIO pin with a given name and mode."""
        if pin_num in self.reserved_pins:
            raise ValueError(f"Pin {pin_num} is reserved for {self.reserved_pins[pin_num]}")
            
        if mode == "out":
            pin = machine.Pin(pin_num, machine.Pin.OUT)
        elif mode == "in":
            pull_mode = machine.Pin.PULL_UP if pull == "up" else machine.Pin.PULL_DOWN if pull == "down" else None
            pin = machine.Pin(pin_num, machine.Pin.IN, pull_mode)
        elif mode == "adc":
            if pin_num not in [26, 27, 28]:  # Pico's ADC pins
                raise ValueError(f"Pin {pin_num} is not an ADC pin")
            pin = machine.ADC(pin_num)
            self.adc_pins[name] = pin
            return
        elif mode == "pwm":
            pin = machine.Pin(pin_num)
            pwm = machine.PWM(pin)
            pwm.freq(1000)  # Default frequency 1kHz
            self.pwm_pins[name] = pwm
            return
            
        self.pins[name] = pin
        
    def set_pin(self, name, value):
        """Set a digital pin high or low."""
        if name in self.pins:
            self.pins[name].value(value)
        else:
            raise ValueError(f"Pin '{name}' not found")
            
    def read_pin(self, name):
        """Read the value of a digital pin."""
        if name in self.pins:
            return self.pins[name].value()
        else:
            raise ValueError(f"Pin '{name}' not found")
            
    def read_adc(self, name):
        """Read an analog value (0-65535)."""
        if name in self.adc_pins:
            return self.adc_pins[name].read_u16()
        else:
            raise ValueError(f"ADC '{name}' not found")
            
    def set_pwm(self, name, duty):
        """Set PWM duty cycle (0-65535)."""
        if name in self.pwm_pins:
            self.pwm_pins[name].duty_u16(duty)
        else:
            raise ValueError(f"PWM '{name}' not found")
            
    def set_pwm_freq(self, name, freq):
        """Set PWM frequency in Hz."""
        if name in self.pwm_pins:
            self.pwm_pins[name].freq(freq)
        else:
            raise ValueError(f"PWM '{name}' not found")
            
    def list_devices(self):
        """List all registered devices."""
        print("\nRegistered Devices:")
        if self.pins:
            print("\nDigital Pins:")
            for name, pin in self.pins.items():
                print(f"  {name}: GPIO {pin}")
        if self.adc_pins:
            print("\nADC Pins:")
            for name, pin in self.adc_pins.items():
                print(f"  {name}: ADC {pin}")
        if self.pwm_pins:
            print("\nPWM Pins:")
            for name, pin in self.pwm_pins.items():
                print(f"  {name}: PWM {pin}")
                
    def cleanup(self):
        """Clean up all pins."""
        for pwm in self.pwm_pins.values():
            pwm.deinit()
        self.pins.clear()
        self.adc_pins.clear()
        self.pwm_pins.clear()