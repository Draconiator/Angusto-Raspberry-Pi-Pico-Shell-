import time
import machine
import json
import gc

# Constants
VERSION = "1.8"
CONFIG_FILE = "config.json"

# Load configuration
def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            print("Loading config file...")
            return json.load(f)
    except:
        # Default configuration
        print("Configuration not found. Loading defaults...")
        return {
            "LED_PIN": 25,
            "BOOT_DELAY": 3,
            "MAIN_SCRIPT": "Angusto.py"
        }

# Initialize configuration
config = load_config()

# Initialize hardware
led_pin = machine.Pin(config["LED_PIN"], machine.Pin.OUT)

def blink_led(times, on_time=0.1, off_time=0.1):
    for _ in range(times):
        led_pin.value(1)
        time.sleep(on_time)
        led_pin.value(0)
        time.sleep(off_time)

def power_light():
    print(f"Bootloader {VERSION} (C) Draconiator, Claude and ChatGPT")
    blink_led(3, 0.5, 0.5)  # Three longer blinks
    time.sleep(1)

def load_and_run_script(script_name):
    try:
        print(f"Attempting to load {script_name}")
        with open(script_name, 'r') as script_file:
            script_content = script_file.read()
        print(f"Script loaded: {script_name}")
        print("Executing script content:")
        led_pin.value(1)
        exec(script_content, {'__name__': '__main__'})
    except OSError as e:
        print(f"Error accessing script '{script_name}': {e}")
        return False
    except Exception as e:
        print(f"Error running script '{script_name}': {e}")
        return False
    return True

def main():
    power_light()
    print("Bootloader is running")
    print(f"Waiting {config['BOOT_DELAY']} seconds before loading main script...")
    
    # Simple countdown without input check
    for i in range(config['BOOT_DELAY'], 0, -1):
        print(f"Loading in {i} seconds...")
        blink_led(1, 0.1, 0.1)
        time.sleep(0.9)  # Adjust to make each iteration close to 1 second

    print(f"Loading {config['MAIN_SCRIPT']}...")
    if load_and_run_script(config['MAIN_SCRIPT']):
        print("Main script execution completed.")
    else:
        print("Failed to run main script. Entering idle loop.")
    
    print("Bootloader main function completed")

if __name__ == "__main__":
    gc.enable()  # Enable garbage collection
    main()
    print("Script execution completed. Entering idle loop.")
    while True:
        led_pin.toggle()
        time.sleep(1)