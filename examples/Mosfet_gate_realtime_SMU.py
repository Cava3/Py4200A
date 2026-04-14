from py4200A import realtime
import numpy as np
import time
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

#> Connecting to the Keithley
# INST_RESOURCE_STR = "TCPIP0::192.0.2.0::1225::SOCKET"
INST_RESOURCE_STR = "GPIB0::17::INSTR"

rt: realtime.RT_KI4200A = realtime.RT_KI4200A(INST_RESOURCE_STR)

#> Getting the SMUs
source = rt.getSMU(3)
gate   = rt.getSMU(2)
unused = rt.getSMU(1)
unused.deactivate()

#> Define sweep ranges (matching programmedTest.py)
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
