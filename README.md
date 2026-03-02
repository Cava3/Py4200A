# Py4200A

py4200A is a python library that provides support for controlling the Keithley Instrument 4200A SCS.  
The library is object oriented, to make it easy to use. It translates settings to instructions for KXCI.  

## Install

For now, you will have to manually add the code from this git repo to either your project, or to your python lib folder.  
Better installation instructions/executable will come later.

### Requirements
- **PyVISA**
- **PyVISA-py** (mandatory for now, support for @ivi as system default coming soon<sup>tm</sup>)
- **linux-gpib**

> [!IMPORTANT]
> You will need a GPIB backend if you want to use GPIB. I would recommend doing a proper [linux-gpib](https://github.com/coolshou/linux-gpib)
> installation beforehand. Make sure your installation of 'linux-gpib' works before opening an issue.
> You can use the `ibtest` tool installed with 'linux-gpib' to test GPIB connection (run as sudo)

### In your project
1. Navigate to your project's folder (`cd /path/to/your/project/`);
2. Download the library using `git clone git@github.com:Cava3/PyKI4200A-SCS.git` or the ZIP download button;
3. If using ZIP, extract in your project folder. You should see a 'Py4200A' folder appear;
4. Import the library in your program `import Py4200A` or `from Py4200A import *`

### As a library
1. Navigate to your python virtual env (or global) lib folder (`cd /path/to/your/python/venv/lib`);
2. Download the library using `git clone git@github.com:Cava3/PyKI4200A-SCS.git` or the ZIP download button;
3. If using ZIP, extract in your library folder. You should see a 'Py4200A' folder appear;
4. Import the library in your program `import Py4200A` or `from Py4200A import *`

## How to use
### KI 4200A Configuration
KXCI takes full controll of the intrument. This means it cannot run alongside other programs like Clarius on the Keithley.
1. Power on the Keithley 4200A SCS
2. Close Clarius, or any other software that is open
3. Open KCon -> KXCI Config
4. Choose your string delimiter, connection mode (GPIB or TCPIP), GPIB port, etc.
5. Close KCon
6. Start KXCI

### Wiring
#### GPIB
Using a GPIB to USB National Instrument cable (worth 1.5k€), you can just connect your computer to the Keithley. Your computer will make a new virtual GPIB interface you can use.
#### TCPIP
The Keithley documentation specifies that the TCPIP communcation for the 4200A cannot work by just wiring you PC's eth to the Keithley's. It is said that both devices have to be on the same network, equipped with a router of some kind.  
I have yet to confirm if the real requirement would just be to have a DHCP server on the PC, or maybe set a static IP. But I'm pretty sure this is not a real limitation.

> [!WARNING]
> In the Keithley's network settings, make sure that the connected network is in "Private" mode and not "Public" mode. In public mode, the Keithley will not accept incoming packets nor pings. You will need admin access though.

### Code
In Python, import the lib to use it. Here is an example of code to test if everything is working.
```py
from Py4200A import *

# INST_RESOURCE_STR = "TCPIP0::<ip>::<port>::SOCKET"
# INST_RESOURCE_STR = "GPIB0::<gpib_adress>::INSTR"
INST_RESOURCE_STR = "GPIB0::17::INSTR"

ki4200: KI4200A = KI4200A(INST_RESOURCE_STR)
print(ki4200.id)
print(" ".join(str(eq) for eq in ki4200.l_equipment))

ki4200.disconnect()
``` 
Explanation line by line :  
1. Import the `Py4200A` library
2. _
3. Example of TCPIP connection string. \<ip> : the Keithley's ip, \<port> the TCPIP port
4. Example of GPIB connection string. \<gpib_adress> : the GPIB adress you configured in KCon. Should be an natural integer.
5. In my case, I configured the GPIB port to 17.
6. _
7. Instanciate a new KI4200A object using the ressource string
8. Display the `id` dict, that contains the Brand name, Model, Serial number and Software Version
9.  Display the list of detected cards.
10. _
11. Disconnect the device. Not required as it auto-closes upon destruction, but good practice.

> [!WARNiNG]
> This script must be run as `sudo` to be able to access the GPIB0 interface

## Supported features
This list is non-exhaustive and lacks the different board types.

**KI4200**
- [x] Connection
- [x] Device informations
- [x] Boards list
- [x] Direct instruction query
- [ ] Run test

**SMU**
- [ ] Choose between voltage and amps
- [ ] Constant source
- [ ] Sweep source
- [ ] Step source
- [ ] Multimeter

**CVU**
- [ ] WIP

**Utils**
- [ ] Export results
- [ ] Save and load configs
- [ ] Display graph
- [ ] Import results and export multi-results


## Roadmap
- [x] Connection to KI4200A-SCS through PCIB or TCPIP
- [x] Perform basic instruction to get Model and SN from KXCI
- [x] Listing of all the boards available
- [ ] Correctly type the boards
- [ ] Send basic setting instructions to SMUs
- [ ] Allow test execution
- [ ] Basic result retrieval
- [ ] Analysis and plotting
- [ ] Util to export results to CSV, txt, raw binary
- [ ] Extended instruction set
- [ ] Util to save/export and load/import settings profiles
- [ ] Export to XLSX
- [ ] Full instruction dictionnary capabilities

## Contribute
If you are not a developer, or do not wish to publish code, feel free to open an issue. I will review
and get to work on it as soon as possible. Please understand that it may take some time though, as I
am currently the only maintainer and have other things to do in life.  
Feel free to open pull request. I will review each one, making sure it is properly documented, properly
commented, and really brings something to the table. Check existing file for documentation example.
Typing and using PyLint in "strict" mode will also be required  
Garbage AI-generated spaghetti code (also know as "*vibe coding*") will be rejected. I have nothing against
good and proper usage of AI tools though. Simply keep your code relevant and readable.

## See also
[instrcom.py](./src/instrcomms.py) - Sample file from Tektronix under[a very permissive license](https://www.tek.com/sample-license)  
[linux-gpib](https://github.com/coolshou/linux-gpib) - GPIB driver I'm using on my Linux (Ubuntu) laptop.  
[PyGPIB] -  
[PyGPIB-py] -  
