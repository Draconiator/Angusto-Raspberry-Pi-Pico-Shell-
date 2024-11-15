import uos
import micropython
import time
import machine
import gc
from devman import DeviceManager

current_directory = "/"
led_pin = machine.Pin(25, machine.Pin.OUT)
devman = DeviceManager()

# Version upgrade to reflect major changes
VERSION = "0.10.1"

def error_flash(severity="minor"):
    if severity == "critical":
        flashes = 3
        duration = 0.5
    elif severity == "minor":
        flashes = 5
        duration = 0.1
    else:  # default/normal error
        flashes = 5
        duration = 0.1
        
    for _ in range(flashes):
        led_pin.value(1)
        time.sleep(duration)
        led_pin.value(0)
        time.sleep(duration)
        
def print_working_directory():
    print(f"Current working directory: {current_directory}")

def print_directory_contents(directory=None):
    if directory is None:
        directory = current_directory

    print(f"\nContents of {directory}:")

    try:
        contents = uos.listdir(directory)
        directories = [name for name in contents if uos.stat(directory + "/" + name)[0] & 0o170000 == 0o040000]
        files = [name for name in contents if uos.stat(directory + "/" + name)[0] & 0o170000 == 0o100000]
        
        directories.sort()
        files.sort()

        # Print directories with formatting
        for name in directories:
            print(f"[DIR]  {name:30}")

        # Print files with formatting
        for name in files:
            full_path = directory + "/" + name
            stats = uos.stat(full_path)
            print(f"[FILE] {name:30} ({stats[6]:8,} bytes)")

    except Exception as e:
        error_flash("critical")
        print(f"Error reading directory contents: {e}")

def print_storage_usage():
    try:
        vfs_info = uos.statvfs("/")
        block_size = vfs_info[0]
        total_blocks = vfs_info[2]
        free_blocks = vfs_info[3]

        total_bytes = block_size * total_blocks
        used_bytes = block_size * (total_blocks - free_blocks)
        remaining_bytes = block_size * free_blocks

        total_mb = total_bytes / (1024 * 1024)
        used_mb = used_bytes / (1024 * 1024)
        remaining_mb = remaining_bytes / (1024 * 1024)

        print("\nStorage usage:")
        print(f"Total space:  {total_mb:.2f} MB")
        print(f"Used space:   {used_mb:.2f} MB")
        print(f"Free space:   {remaining_mb:.2f} MB")
    except Exception as e:
        error_flash("critical")
        print(f"Error retrieving storage information: {e}")

def make_directory(arguments):
    if not arguments:
        error_flash("minor")
        print("Invalid command: mkdir requires a directory name")
        return
    directory_name = arguments[0]
    try:
        uos.mkdir(current_directory + "/" + directory_name)
        print(f"Directory '{directory_name}' created successfully.")
    except OSError as e:
        error_flash("minor")
        print(f"Error creating directory '{directory_name}': {e}")

def remove_directory(arguments):
    if not arguments:
        error_flash("minor")
        print("Invalid command: rmdir requires a directory name")
        return
    directory_name = arguments[0]
    try:
        uos.rmdir(current_directory + "/" + directory_name)
        print(f"Directory '{directory_name}' removed successfully.")
    except OSError as e:
        error_flash("minor")
        print(f"Error removing directory '{directory_name}': {e}")

def change_directory(arguments):
    global current_directory
    if not arguments:
        error_flash("minor")
        print("Invalid command: cd requires a directory name")
        return
    new_directory = arguments[0]

    try:
        # Added relative path handling
        if not new_directory.startswith("/"):
            new_directory = current_directory + "/" + new_directory

        uos.chdir(new_directory)
        current_directory = uos.getcwd()
    except OSError as e:
        error_flash("minor")
        print(f"Error changing directory to '{new_directory}': {e}")

def delete_file(arguments):
    if not arguments:
        error_flash("minor")
        print("Invalid command: delete requires a filename")
        return
    filename = arguments[0]
    try:
        full_path = current_directory + "/" + filename
        uos.remove(full_path)
        print(f"File '{filename}' deleted successfully.")
    except OSError as e:
        if e.args[0] == 2:
            print(f"File not found: {filename}")
        else:
            print(f"Error deleting file '{filename}': {e}")
    except Exception as e:
        print(f"Unexpected error deleting file '{filename}': {e}")

def welcome_msg():
    print(f"*            Angusto v{VERSION}          ")
    print(f"* A small shell for the Raspberry Pi Pico")
    print(f"*  (c) Draconiator, ChatGPT, and Claude")
    
def notepad(arguments):
    if len(arguments) > 1:
        error_flash()
        print("Invalid command: notepad only accepts an optional filename argument.")
        return

    filename = "notepad.txt" if not arguments else arguments[0]
    undo_stack = []

    try:
        if uos.path.exists(filename):
            with open(filename, "r") as file:
                contents = file.readlines()
            print(f"Loaded contents from '{filename}'")
        else:
            contents = []
            print(f"Creating new file: {filename}")

        print("Enter text for the notepad. Type 'exit' on a new line to save and exit.")
        print("Use 'undo' to undo the last added line.")
        print("To edit an existing line, type the line number followed by the new content.")
        
        line_number = len(contents)
        while True:
            user_input = input(f"{line_number + 1}: ").strip()
            
            if user_input.lower() == "exit":
                break
            elif user_input.lower() == "undo":
                if undo_stack:
                    removed_line = undo_stack.pop()
                    contents.pop()
                    print(f"Removed last added line: {removed_line}")
                    line_number -= 1
                else:
                    print("No lines to undo.")
            elif user_input.isdigit():
                edit_line = int(user_input) - 1
                if 0 <= edit_line < len(contents):
                    new_content = input(f"Enter new content for line {edit_line + 1}: ")
                    contents[edit_line] = new_content + "\n"
                else:
                    print("Invalid line number.")
            else:
                undo_stack.append(user_input)
                contents.append(user_input + "\n")
                line_number += 1

        print("\nUpdated contents of the file:")
        for idx, line in enumerate(contents, start=1):
            print(f"{idx}: {line}", end="")

        with open(filename, "w") as file:
            file.writelines(contents)

        print(f"\nNotepad contents saved to '{filename}'")

    except Exception as e:
        error_flash()
        print(f"Unexpected error in notepad: {e}")

def microshell_help(command=None):
    if command:
        if command[0] in command_functions:
            print(f"Help for '{command[0]}':")
            if command[0] == "ls":
                print(f"ls [directory]      : List files within the current or specified directory")
            elif command[0] == "cd":
                print(f"cd <directory>      : Change the current directory (supports relative paths)")
            elif command[0] == "temp":
                print(f"temp                : Display the current CPU temperature")
            # Add more detailed descriptions for each command
        else:
            print(f"No help available for command '{command[0]}'.")
    else:
        print(f"Available commands:")
        print(f"ls [directory]      : List files within the current or specified directory")
        print(f"cd <directory>      : Change the current directory")
        print(f"pwd                 : Print the current working directory")
        print(f"delete/del <filename>: Delete a file")
        print(f"mkdir <dirname>     : Create a new directory")
        print(f"rmdir <dirname>     : Remove an existing directory")
        print(f"notepad [filename]  : Open a simple text editor (type 'exit' to save and exit)")
        print(f"cp <source> <dest>  : Copy a file")
        print(f"mv <source> <dest>  : Move a file")
        print(f"run <script.py>     : Execute a Python script (add '--dry-run' for preview)")
        print(f"cat <filename>      : Display the contents of a file")
        print(f"memory              : Display memory usage information")
        print(f"reboot              : Reboot the Raspberry Pi Pico")
        print(f"temp                : Display the current CPU temperature")
        print(f"about               : Information about Angusto")

def run_script(arguments):
    if not arguments:
        error_flash("minor")
        print("Invalid command: run requires a script name - correct usage 'run script.py'")
        return

    dry_run = '--dry-run' in arguments
    script_name = arguments[0]

    try:
        with open(script_name, 'r') as script_file:
            script_content = script_file.read()
        
        if dry_run:
            print(f"Dry run: {script_name}")
            print(script_content)
        else:
            print(f"Executing script: {script_name}")
            exec(script_content)
    except Exception as e:
        error_flash("critical")
        print(f"Error executing script '{script_name}': {e}")

def copy_file(arguments):
    if len(arguments) != 2:
        error_flash("minor")
        print("Invalid command: cp requires source and destination filenames")
        return
    source, destination = arguments
    try:
        with open(source, 'rb') as src, open(destination, 'wb') as dst:
            dst.write(src.read())
        print(f"File '{source}' copied to '{destination}' successfully.")
    except Exception as e:
        error_flash("minor")
        print(f"Error copying file: {e}")

def move_file(arguments):
    if len(arguments) != 2:
        error_flash("minor")
        print("Invalid command: mv requires source and destination filenames")
        return
    source, destination = arguments
    try:
        uos.rename(source, destination)
        print(f"File '{source}' moved to '{destination}' successfully.")
    except Exception as e:
        error_flash("minor")
        print(f"Error moving file: {e}")

def cat_file(arguments):
    if not arguments:
        error_flash("minor")
        print("Invalid command: cat requires a filename")
        return
    filename = arguments[0]
    try:
        with open(filename, 'r') as file:
            print(file.read())
    except Exception as e:
        error_flash("minor")
        print(f"Error reading file '{filename}': {e}")

def display_memory_usage(arguments=None):
    gc.collect()
    free_mem = gc.mem_free()
    alloc_mem = gc.mem_alloc()
    total_mem = free_mem + alloc_mem
    print(f"Memory Usage:")
    print(f"Free:      {free_mem:,} bytes")
    print(f"Allocated: {alloc_mem:,} bytes")
    print(f"Total:     {total_mem:,} bytes")
    print(f"Used:      {alloc_mem / total_mem:.2%}")

def reboot_pico(arguments=None):
    print("Rebooting Raspberry Pi Pico...You may need to reconnect.")
    time.sleep(1)
    machine.reset()
    
def check_temperature(arguments=None):
    sensor_temp = machine.ADC(4)
    conversion_factor = 3.3 / (65535)
    reading = sensor_temp.read_u16() * conversion_factor
    temperature = 27 - (reading - 0.706)/0.001721
    print(f"Current CPU temperature: {temperature:.2f}°C")    

def register_device(arguments):
    if len(arguments) < 3:
        print("Usage: device register <name> <pin> <mode> [pull]")
        print("Modes: in, out, adc, pwm")
        print("Pull (optional): up, down")
        return
        
    name, pin, mode = arguments[:3]
    pull = arguments[3] if len(arguments) > 3 else None
    
    try:
        pin_num = int(pin)
        device_manager.register_pin(pin_num, name, mode, pull)
        print(f"Registered device '{name}' on pin {pin_num}")
    except Exception as e:
        print(f"Error registering device: {e}")

def control_device(arguments):
    if len(arguments) < 2:
        print("Usage: device control <name> <value>")
        return
        
    name, value = arguments[:2]
    try:
        if name in device_manager.pwm_pins:
            # Handle PWM value (0-100%)
            duty = int(float(value) * 65535 / 100)
            device_manager.set_pwm(name, duty)
        else:
            # Handle digital value (0 or 1)
            device_manager.set_pin(name, int(value))
        print(f"Set device '{name}' to {value}")
    except Exception as e:
        print(f"Error controlling device: {e}")

def read_device(arguments):
    if not arguments:
        print("Usage: device read <name>")
        return
        
    name = arguments[0]
    try:
        if name in device_manager.adc_pins:
            value = device_manager.read_adc(name)
            voltage = value * 3.3 / 65535
            print(f"ADC '{name}' reading: {value} ({voltage:.2f}V)")
        else:
            value = device_manager.read_pin(name)
            print(f"Digital pin '{name}' reading: {value}")
    except Exception as e:
        print(f"Error reading device: {e}")

def list_devices(arguments=None):
    device_manager.list_devices()
    
command_functions = {
    "ls": print_directory_contents,
    "cd": change_directory,
    "pwd": print_working_directory,
    "delete": delete_file,
    "del": delete_file,
    "mkdir": make_directory,
    "rmdir": remove_directory,
    "help": microshell_help,
    "notepad": notepad,
    "about": welcome_msg,
    "cp": copy_file,
    "mv": move_file,
    "run": run_script,
    "cat": cat_file,
    "memory": display_memory_usage,
    "reboot": reboot_pico,
    "temp": check_temperature,
    "device": {    
        "register": register_device,
        "control": control_device,
        "read": read_device,
        "list": list_devices
    }
}

def idle_flash_callback(t):
    """Timer callback that creates a brief flash followed by an off period."""
    led_pin.value(1)  # Turn LED on
    time.sleep(0.1)   # Brief flash duration
    led_pin.value(0)  # Turn LED off

def main():
    led_pin.value(0)
    welcome_msg()
    print_storage_usage()
    
    # Start a timer for the idle flash - 5000ms = 5 seconds
    idle_timer = machine.Timer()
    idle_timer.init(period=5000, mode=machine.Timer.PERIODIC, 
                   callback=idle_flash_callback)
    
    while True:
        user_input = input(f"pico:{current_directory}> ")
        tokens = user_input.split()

        if not tokens:
            continue

        command = tokens[0].lower()
        arguments = tokens[1:]

        if command in command_functions:
            led_pin.value(1)  # Turn on LED during command execution
            if isinstance(command_functions[command], dict):
                if len(arguments) > 0 and arguments[0] in command_functions[command]:
                    command_functions[command][arguments[0]](arguments[1:])
                else:
                    print(f"Invalid subcommand for '{command}'. Available subcommands:")
                    for subcommand in command_functions[command].keys():
                        print(f"  {subcommand}")
            else:
                command_functions[command](arguments)
            led_pin.value(0)  # Return to idle state
        else:
            error_flash("minor")
            print(f"Invalid command: {command}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        led_pin.value(0)  # Ensure LED is off when exiting
        print("\nExiting...")