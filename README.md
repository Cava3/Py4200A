# Py4200A

> [!NOTE]
> This project is not complete yet, work in progress.  
> Basic SMU controlling is already supported, but no pulse mode available (PMU/RPM not existing yet)

py4200A is a python library that provides support for controlling the Keithley Instrument 4200A SCS.  
The library is object oriented, to make it easy to use. It translates settings to instructions for KXCI.  
Made in collaboration with the USAL (University of SALamanca) in Salamanca, Spain.

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
In Python, import the lib to use it. You can choose to either manually control the device in real time, or pre-programm it to run with settings.  
Using pre-programmed (normal) mode, performance is way better than realtime manual control. The below examples are doing the exact same gate test on a MOSFET type component :
- Component : HEF4007UBP
- Ground : pin 7 (Vss)
- Gate : pin 6 (G)
- Source : pin 8 (D)

Results :
- Normal mode : 101.2s
- Realtime mode : 408.9s

Normal mode is ~4 times faster for this test.

> [!WARNING]
> This script must be run with root privilege to be able to access the GPIB0 interface

#### Normal (pre-programmed)
```py
import py4200A
from py4200A import KI4200A
import time

#> Connecting to the Keithley
# INST_RESOURCE_STR = "TCPIP0::192.0.2.0::1225::SOCKET"
INST_RESOURCE_STR = "GPIB0::17::INSTR"

ki4200: KI4200A = KI4200A(INST_RESOURCE_STR)
ki4200.reset()

#> Getting the SMUs
source = ki4200.getSMU(3)
gate = ki4200.getSMU(2)
unused = ki4200.getSMU(1)
unused.deactivate()

#> Configure the SMUs
gate.setupSMU("VGT", "IGT", py4200A.consts.SourceType.VOLT, py4200A.consts.SourceFunction.STEP)
gate.setStepFunction(start=0, stop=5, step=1, compliance=0.1)

source.setupSMU("VSRC", "ISRC", py4200A.consts.SourceType.VOLT, py4200A.consts.SourceFunction.SWEEP)
source.setSweepFunction(py4200A.consts.SweepType.LINEAR, start=0, stop=15, step=0.1, compliance=0.05)

#> Configure the display
ki4200.display.displayGraph(x=source.voltage_measurement, y1=source.current_measurement) # x= time, y1 = gateV, y2 = srcV

#> Run and wait for test
print("Starting test.")
t_start = time.time()
ki4200.runSmuTest()
ki4200.waitForDataReady()

#> Collect results as a BlobDependent
result: py4200A.results.BlobDependent = ki4200.makeDependentFrom(
    data=source.current_measurement,
    params=[source.voltage_measurement, gate.voltage_measurement],
)

print(f"Done. ({time.time() - t_start:.1f}s)")

ki4200.disconnect()
``` 
You can display (plot) the graph on your computer by adding these few lines :
```py
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

#> Plot ISRC vs VSRC, one curve per VGT value
colors: list[str] = ["red", "green", "blue", "magenta", "yellow", "cyan"]
vgt_values = result.parameters["VGT"]
vsrc_values = result.parameters["VSRC"]

fig, ax = plt.subplots()
for i, vgt in enumerate(vgt_values):
    ax.plot(vsrc_values, result.value[i, :], color=colors[i % len(colors)], label=f"Gate = {vgt:.2f} V")

ax.set_xlabel("Vsource (V)")
ax.set_ylabel("Isource (A)")
ax.legend()
plt.tight_layout()
plt.show()
```

#### Realtime
```py
from py4200A import realtime
import numpy as np
import time

#> Connecting to the Keithley
# INST_RESOURCE_STR = "TCPIP0::192.0.2.0::1225::SOCKET"
INST_RESOURCE_STR = "GPIB0::17::INSTR"

rt: realtime.RT_KI4200A = realtime.RT_KI4200A(INST_RESOURCE_STR)

#> Getting the SMUs
source = rt.getSMU(3)
gate   = rt.getSMU(2)
unused = rt.getSMU(1)
unused.deactivate()
rt.userMode()

#> Define sweep ranges
vgt_values  = np.linspace(0, 5,  6)    # 0, 1, 2, 3, 4, 5 V
vsrc_values = np.linspace(0, 15, 151)  # 0 to 15 V, step 0.1 V
results     = np.zeros((len(vgt_values), len(vsrc_values)))

#> Run the sweep
print("Starting test.")
t_start = time.time()
for i, vgt in enumerate(vgt_values):
    gate.setVoltageOutput(float(vgt), compliance=0.1)
    for j, vsrc in enumerate(vsrc_values):
        source.setVoltageOutput(float(vsrc), compliance=0.05)
        results[i, j] = source.measure_current()
print(f"Done. ({time.time() - t_start:.1f}s)")

rt.disconnect()
```
You can display (plot) the graph on your computer by adding these few lines :
```py
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

#> Plot ISRC vs VSRC, one curve per VGT value
colors: list[str] = ["red", "green", "blue", "magenta", "yellow", "cyan"]

fig, ax = plt.subplots()
for i, vgt in enumerate(vgt_values):
    ax.plot(vsrc_values, results[i, :], color=colors[i % len(colors)], label=f"Gate = {vgt:.2f} V")

ax.set_xlabel("Vsource (V)")
ax.set_ylabel("Isource (A)")
ax.legend()
plt.tight_layout()
plt.show()

```

## Roadmap
- [x] Connection to KI4200A-SCS through PCIB or TCPIP
- [x] Perform basic instruction to get Model and SN from KXCI
- [x] Listing of all the boards available
- [x] Correctly type the boards
- [x] Send basic setting instructions to SMUs
- [x] Allow test execution
- [x] Basic result retrieval
- [x] Analysis and plotting
- [ ] PMU RMP commands
- [ ] Publish on PyPi
- [ ] Matlab wrapper
- [ ] Util to export results to CSV, txt, raw binary
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
[USAL] -