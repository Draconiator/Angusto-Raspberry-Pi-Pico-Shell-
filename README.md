Angusto Shell System for Raspberry Pi Pico

Version 0.10.0

System Components:

    Main Boot System (main.py)
    Configuration (config.json)
    Device Manager (devman.py)
    Shell Interface (Angusto.py)

Key Features:

    File system operations
    Device management
    System monitoring
    Text editing capabilities (notepad mentioned in example)

Available Commands:

File System Operations:
Command	Description
ls [directory]	List contents of current or specified directory
cd <directory>	Change current directory (supports relative paths)
pwd	Print current working directory
mkdir <dirname>	Create new directory
rmdir <dirname>	Remove existing directory
delete/del <filename>	Delete a file
cp <source> <dest>	Copy a file
mv <source> <dest>	Move a file
cat <filename>	Display file contents

Device Management:
Command	Description
device register <name> <pin> <mode> [pull]	Register a new device (modes: in, out, adc, pwm)
device control <name> <value>	Control device state (digital: 0/1, PWM: 0-100%)
device read <name>	Read device state or value
device list	List all registered devices

System Operations:
Command	Description
memory	Display memory usage
temp	Show CPU temperature
reboot	Restart the Pico
run <script.py> [--dry-run]	Execute Python script
help [command]	Display help information

Example Usage:

Basic File Operations:

pico:/> ls
pico:/> mkdir test
pico:/> cd test
pico:/test> notepad example.txt  # Editor example, may vary
pico:/test> cat example.txt

Device Control:

pico:/> device register led 15 out
pico:/> device control led 1
pico:/> device register sensor 26 adc
pico:/> device read sensor

Important Notes:

    Reserved Pin 25: Onboard LED
    Reserved Pin 4: Internal temperature sensor
    ADC pins available: 26, 27, 28
    Default PWM frequency: 1kHz

Error Handling:

    Minor Errors: 3 quick LED flashes
    Critical Errors: 3 longer LED flashes
    Default Errors: 5 quick LED flashes

Recovery Procedures:

    Check LED error patterns for diagnosis
    Use memory command to verify resource availability
    Use reboot command if system becomes unresponsive
    Edit config.json to extend boot delay if needed
