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
ki4200.test_mode = py4200A.consts.RPMMode.PMU

#> Init PMU
ki4200.initPMU()
ki4200.pmu_measure_mode = py4200A.consts.PMUMeasureMode.SPOT_MEAN_DISCRETE

#> Getting the RPMs
source = ki4200.getRPM(12)
source.activated = True
gate   = ki4200.getRPM(11)
gate.activated = True

#> Configure pulse times
period: float = 1e-3
width:  float = 500e-6
riset:  float = 100e-9
fallt:  float = 100e-9

source.setPulseTimes(period, width, riset, fallt)
gate.setPulseTimes(period, width, riset, fallt)

#> Gate steps through VGS values (outer loop)
gate.setPulseStep(py4200A.consts.PMUPulseMode.AMPLITUDE, start=0, stop=5, step=1, constant_v=0)
gate.setMeasurePIV(acquire_high=True, acquire_low=False)

#> Source sweeps VDS values (inner loop) — TH records when each pulse was taken
source.setPulseSweep(py4200A.consts.PMUPulseMode.AMPLITUDE, start=0, stop=10, step=0.1, dual_sweep=False, constant_v=0)
source.setMeasurePIV(acquire_high=True, acquire_low=False)

#> Run and wait for test
print("Starting test.")
t_start: float = time.time()
ki4200.runTest()
ki4200.waitForTestEnd()

#> Collect results — shape: (num_gate_steps, num_source_steps)
#  X axis: source.th_measurement — timestamp of each pulse's high-level sample
#  Y axis: source.ih_measurement — drain current at high level
result: py4200A.results.BlobDependent = ki4200.makeDependentFrom(
    data=source.ih_measurement,
    params=[gate.vh_measurement, source.th_measurement],
)

ki4200.disconnect()
print(f"Done. ({time.time() - t_start:.1f}s)")

#> Plot IH vs TH, one curve per gate VH value
colors: list[str] = ["red", "green", "blue", "magenta", "orange", "cyan"]
vgt_values  = result.parameters[gate.vh_measurement.name]
time_values = result.parameters[source.th_measurement.name]

fig, ax = plt.subplots()
for i, vgt in enumerate(vgt_values):
    ax.plot(time_values, result.value[i, :], color=colors[i % len(colors)], label=f"Vgate = {vgt:.1f} V")

ax.set_xlabel("Time (s)")
ax.set_ylabel("Idrain (A)")
ax.legend()
plt.tight_layout()
plt.show()
