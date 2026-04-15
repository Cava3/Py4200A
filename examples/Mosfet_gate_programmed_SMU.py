import py4200A
from py4200A import KI4200A
import time
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

#> Connecting to the Keithley
# INST_RESOURCE_STR = "TCPIP0::192.0.2.0::1225::SOCKET"
INST_RESOURCE_STR = "GPIB0::17::INSTR"

ki4200: KI4200A = KI4200A(INST_RESOURCE_STR)
ki4200.reset()
ki4200.test_mode = py4200A.consts.RPMMode.SMU

#> Getting the SMUs
source = ki4200.getSMU(3)
gate   = ki4200.getSMU(2)
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
ki4200.runTest()
ki4200.waitForTestEnd()

#> Collect results as a BlobDependent
result: py4200A.results.BlobDependent = ki4200.makeDependentFrom(
    data=source.current_measurement,
    params=[source.voltage_measurement, gate.voltage_measurement],
)

print(f"Done. ({time.time() - t_start:.1f}s)")

ki4200.disconnect()

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
