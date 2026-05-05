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

#> Time-domain sampling parameters
NR = 50          # readings per gate step
ki4200.nr       = NR
ki4200.wt       = 0.0   # no wait before first sample
ki4200.interval = 0.01  # 10 ms between samples

#> Getting the SMUs
gate  = ki4200.getSMU(2)
drain = ki4200.getSMU(3)

#> Configure gate: step through VGS values (outer loop)
gate.setupSMU("VGT", "IGT", py4200A.consts.SourceType.VOLT, py4200A.consts.SourceFunction.STEP)
gate.setStepFunction(start=0, stop=5, step=1, compliance=0.1)
# gate.voltage_measurement.order = 1 (outer), steps = 6

#> Configure drain: constant VDS, measure current + time (inner loop)
drain.setupSMU("VSRC", "ISRC", py4200A.consts.SourceType.VOLT, py4200A.consts.SourceFunction.CONSTANT)
drain.setConstantSourceValue(vds=1.0, compliance=1e-3)

# setConstantSourceValue does not configure time_measurement — do it manually
drain.time_measurement.steps = NR
drain.time_measurement.order = 0  # innermost loop

#> Configure the display
ki4200.display.displayGraph(x=drain.time_measurement, y1=drain.current_measurement)

#> Run and wait for test
print("Starting test.")
t_start = time.time()
ki4200.runTest()
ki4200.waitForTestEnd()

#> Collect results as a BlobDependent — shape: (num_gate_steps, NR)
result: py4200A.results.BlobDependent = ki4200.makeDependentFrom(
    data=drain.current_measurement,
    params=[gate.voltage_measurement, drain.time_measurement],
)

print(f"Done. ({time.time() - t_start:.1f}s)")

ki4200.disconnect()

#> Plot ISRC vs time, one curve per VGT value
vgt_values  = result.parameters[gate.voltage_measurement.name]
time_values = result.parameters[drain.time_measurement.name]

fig, ax = plt.subplots()
colors: list[str] = ["red", "green", "blue", "magenta", "orange", "cyan"]
for i, vgt in enumerate(vgt_values):
    ax.plot(time_values, result.value[i, :], color=colors[i % len(colors)], label=f"Vgate = {vgt:.1f} V")

ax.set_xlabel("Time (s)")
ax.set_ylabel("Idrain (A)")
ax.legend()
plt.tight_layout()
plt.show()
