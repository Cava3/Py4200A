# SMU

- [x] Generic request
- [x] `*IDN?` - Get identifying data from the Keithley
- [x] `*OPT?` - Get list of equipped cards' names
- [x] `*RST` - Set instruments to default
- [x] `SP` - IDK but allows to check for data ready ? Probably ?
- [x] `DE` - # Select page "Channel Definition"
- [x] `CH` - Full SMU definition
- [x] `VM` - Define as voltmeter only
- [x] `VS` - Define as volt source
- [x] `SS` - # Select page "Source Setup"
- [x] `DT` - Delay measurement during sweep (to counter the capacitive effect)
- [ ] `FS` and `RT` - Alternative sweep settings
- [x] `HT` - Delay between steps before starting the sweep
- [x] `SC` - Constant voltage value (VS only)
- [x] `ST` - Cut or keep power after test
- [x] `VC` and `IC` - Constant voltage/intensity value
- [x] `VL` and `IL` - Sweep list values
- [x] `VP` and `IP` - Step settings
- [x] `VR` and `IR` - Sweep function
- [x] `SM` - # Select page "Measurement setup"
- [x] `DM` - Select between table and graph display mode
- [ ] `IN` - Set time between measurements for time-based measurements
- [x] `LI` - Select measurements to be shown in table display mode
- [ ] `NR` - Amount of measurements for time-based measurements
- [x] `WT` - Wait after constant source power before stepping
- [x] `XN` - Set X axis measurements to display
- [x] `XT` - Set X axis to display time
- [x] `YA` and `YB` - Set Y1 and Y2 measurements to display
- [x] `MD` - # Select page "Measurement control"
- [x] `ME` - Run test
- [ ] `GT` - Loads data or program
- [ ] `SV` - Save data or program
- [x] No page required
- [x] `MP` - Map a channel to a SMU, VS or VM
- [ ] `SR` - Set source range
- [x] `US` - # Select page "User Mode" (real time ?)
- [x] `DI` and `DV` - Define as current/voltage source
- [x] `DS` - Set output value for voltage source
- [x] `TI` and `TV` - Trigger a measurement of wanted value
- [ ] `AC` - Calibrate a channel
- [x] `BC` - Clear buffer
- [x] `DO` - Get time readings ? Maybe ? Idk ?
- [x] `EC` - Exit if compliance reached (saturation)
- [ ] `EM` - Switch to 4145 emulation mode
- [x] `IT` - SMU integration time (noisy, medium, quiet)
- [x] `RD` - Get readings, available in real time
- [x] `RG` - Set current rangewhen measuring
- [x] `RI` and `RV` - Set real-time intensity/voltage output
- [x] `RS` - Float precision (0-7)

# PMU-RPM

## Standard PMU commands

- [x] `:PMU:ABORT` - Abort the current PMU test
- [ ] `:PMU:CONNECTION:COMP` - Set PMU connection compensation
- [x] `:PMU:DATA:COUNT?` - Query the number of data points available
- [x] `:PMU:DATA:GET` - Get measurement data from the PMU
- [x] `:PMU:EXECUTE` - Execute a configured PMU test
- [x] `:PMU:INIT` - Initialize the PMU
- [x] `:PMU:LLEC:CONFIGURE` - Configure load-line effect compensation (LLEC)
- [x] `:PMU:LOAD` - Set device real impedance
- [ ] `:PMU:MEASURE:CONNECTION:COMP` - Set current connexion compensation
- [x] `:PMU:MEASURE:MODE` - Set measurement mode (discrete / average, waveforme / spot)
- [x] `:PMU:MEASURE:PIV` - Set what measurements to save for a channel in pulse IV mode.
- [ ] `:PMU:MEASURE:RANGE` - Set measurement range
- [x] `:PMU:OUTPUT:STATE` - Enable or disable PMU output
- [x] `:PMU:PULSE:BURST:COUNT` - Set number of pulses in a burst
- [x] `:PMU:PULSE:TIMES` - Set pulse timing (period, width, rise, fall, delay)
- [x] `:PMU:PULSE:TRAIN` - Sets base and aplitude voltage for a "constant" pulse
- [x] `:PMU:RETAIN:CONFIG` - Retain or clear configuration after test
- [x] `:PMU:RPM:CONFIGURE` - Configure RPM mode (SMU, CVU, etc.)
- [x] `:PMU:SAMPLE:RATE` - Set the waveform sample rate
- [ ] `:PMU:SOURCE:RANGE` - Set the source voltage range
- [ ] `:PMU:STEP:DC` - Configure a DC step sweep
- [ ] `:PMU:STEP:PULSE:AMPLITUDE` - Configure pulse amplitude step sweep
- [ ] `:PMU:STEP:PULSE:BASE` - Configure pulse base step sweep
- [ ] `:PMU:SWEEP:DC` - Configure a DC sweep
- [ ] `:PMU:SWEEP:PULSE:AMPLITUDE` - Configure pulse amplitude sweep
- [ ] `:PMU:SWEEP:PULSE:BASE` - Configure pulse base sweep
- [ ] `:PMU:TEST:STATUS?` - Query current test status
- [ ] `:PMU:TIMES:PIV` - Set timing for post-pulse I-V measurement
- [ ] `:PMU:TIMES:WAVEFORM` - Set waveform timing parameters

## Segment Arb commands

- [ ] `:PMU:SARB:SEQ:MEAS:START` - Set segment arb measurement start point
- [ ] `:PMU:SARB:SEQ:MEAS:START:ADD` - Append measurement start point to sequence
- [ ] `:PMU:SARB:SEQ:MEAS:STOP` - Set segment arb measurement stop point
- [ ] `:PMU:SARB:SEQ:MEAS:STOP:ADD` - Append measurement stop point to sequence
- [ ] `:PMU:SARB:SEQ:MEAS:TYPE` - Set measurement type for segment arb
- [ ] `:PMU:SARB:SEQ:MEAS:TYPE:ADD` - Append measurement type to sequence
- [ ] `:PMU:SARB:SEQ:SSR` - Set segment shape and rate for first segment
- [ ] `:PMU:SARB:SEQ:SSR:ADD` - Append segment shape and rate to sequence
- [ ] `:PMU:SARB:SEQ:STARTV` - Set segment start voltage
- [ ] `:PMU:SARB:SEQ:STARTV:ADD` - Append segment start voltage to sequence
- [ ] `:PMU:SARB:SEQ:STOPV` - Set segment stop voltage
- [ ] `:PMU:SARB:SEQ:STOPV:ADD` - Append segment stop voltage to sequence
- [ ] `:PMU:SARB:SEQ:TIME` - Set segment time
- [ ] `:PMU:SARB:SEQ:TIME:ADD` - Append segment time to sequence
- [ ] `:PMU:SARB:SEQ:TRIG` - Set segment trigger
- [ ] `:PMU:SARB:SEQ:TRIG:ADD` - Append segment trigger to sequence
- [ ] `:PMU:SARB:WFM:SEQ:LIST` - Define waveform sequence list
- [ ] `:PMU:SARB:WFM:SEQ:LIST:ADD` - Append waveform to sequence list

