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

#> Init PMU and test mode
ki4200.initPMU()
ki4200.pmu_measure_mode = py4200A.consts.PMUMeasureMode.SPOT_MEAN_DISCRETE

#> Getting the RPMs
source = ki4200.getRPM(12)
gate   = ki4200.getRPM(11)

#> Configure pulse times
# Constraints: period 60ns-1s, width > 0.5*(riset+fallt), etc.
period: float = 1e-3
width: float  = 500e-6
riset: float  = 100e-9
fallt: float  = 100e-9

source.setPulseTimes(period, width, riset, fallt)
gate.setPulseTimes(period, width, riset, fallt)

#> Configure sweep and step
# Gate steps from 0 to 5V
gate.setPulseStep(py4200A.consts.PMUPulseMode.AMPLITUDE, start=0, stop=5, step=1, constant_v=0)
gate.setMeasurePIV(acquire_high=True, acquire_low=False)

# Source sweeps from 0 to 10V (within default 10V span)
source.setPulseSweep(py4200A.consts.PMUPulseMode.AMPLITUDE, start=0, stop=15, step=0.1, dual_sweep=False, constant_v=0)
source.setMeasurePIV(acquire_high=True, acquire_low=False)
source.source_range = py4200A.consts.PMUSourceRange.V40

#> Run and wait for test
print("Starting test.")
t_start: float = time.time()
ki4200.runTest()
ki4200.waitForTestEnd()

#> Collect results as a BlobDependent
result: py4200A.results.BlobDependent = ki4200.makeDependentFrom(
    data=source.ih_measurement,
    params=[source.vh_measurement, gate.vh_measurement],
)

ki4200.disconnect()
print(f"Done. ({time.time() - t_start:.1f}s)")

#> Plot ISRC vs VSRC, one curve per VGT value
colors: list[str] = ["red", "green", "blue", "magenta", "yellow", "cyan"]
vgt_values = result.parameters[gate.vh_measurement.name]
vsrc_values = result.parameters[source.vh_measurement.name]

fig, ax = plt.subplots()
for i, vgt in enumerate(vgt_values):
    ax.plot(vsrc_values, result.value[i, :], color=colors[i % len(colors)], label=f"Gate V = {vgt:.2f} V")

ax.set_xlabel("Source Voltage (V)")
ax.set_ylabel("Source Current (A)")
ax.legend()
plt.tight_layout()
plt.show()
