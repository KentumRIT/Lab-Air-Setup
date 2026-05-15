# Current Loop Controller Calibration
## Materials
- NI-DAQ USB-6421, S/N 283489E
- 24V Power supply, model LYD1302405000
- Lab custom current loop interface
- Two twisted pairs of 24 AWG wire ~150 mm long
- A strand of 22 AWG wire ~80 mm long

## Setup
Current loop channels 1 and 2 were calibrated independently of one another. I originally tried to calibrate them together, but found significant 'cross-talk' between the channels. It seems that due to the DAQ's common analog ground reference, the current return paths for each XTR116 module aren't independent and therefore output current isn't independent either. To calibrate channel 1 of the current loop interface, I made the following connections with twisted pairs (every 2 rows starting from the top is a twisted cable pair):
| NI-DAQ Port | Current Loop Interface Port |
|-------------|-----------------------------|
| AO0         | AO FROM DAQ: 1+             |
| Gnd         | AO FROM DAQ: 1-             |
| AI0         | AI TO DAQ: V1               |
| AI8         | AI TO DAQ: GND              |

- On the current loop interface, the Curr Out: I1 pin was connected to the Curr In: I1 pin via the 22 AWG wire strand
- The DAQ was connected to the lab computer via USB-C
- The 24V power supply was connected to the current loop interface via barrel jack.
<br>

Below is an image of the wiring setup for channel 1:
![](Images/Setup/CurrentCalibration.jpg)

When testing channel 2, I moved the 22 AWG wire strand to connect the Curr Out: I2 pin to the Curr In: I1 pin and changed the twisted pair connections to:
| NI-DAQ Port | Current Loop Interface Port |
|-------------|-----------------------------|
| AO0         | AO FROM DAQ: 2+             |
| Gnd         | AO FROM DAQ: 2-             |
| AI0         | AI TO DAQ: V1               |
| AI8         | AI TO DAQ: GND              |

## Methods & Results
Within [CurrentControllerCalibration.py](src/CurrentControllerCalibration.py), I drove the current loop interface at increasing frequencies until significant deviation was detected on either current channel. In this way, I found a suitable frequency upper bound. This test was only done with channel 1, as the channels are expected to operate similarly enough for the upper bound to be shared between them. The following table shows tested frequencies and results:
| Frequency (kHz) | Notes                                                                                                                                                                                                                                                         |
|-----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 250             | 1 sample delay (~4 µs delay) between analog out and analog in signals. Keep in mind, the AI signal is already being shifted forward by 1 sample to account for the fact that AI samples before AO is finished setting, so this is effectively an ~8 µs delay. |
| 100             | No more delay, but there is still hysteresis in the signal                                                                                                                                                                                                    |
| 40              | No visible hysteresis                                             

<br>


With an upper bound of 40 kHz for sampling, I collected calibration data across a wide frequency spectrum with 20 trials per frequency, 5 wave periods per trial, and 200 samples per period. All data per frequency was lumped together to generate a linear regression fit to measured current in mA vs input voltage in V. The results are recorded in the following table:

| Frequency (kHz) | Channel 1 Slope | Channel 1 Standard error |
|-----------------|-----------------|--------------------------|
| 40              | 2.4995          | 2.324E-2                 |
| 10              | 2.4993          | 2.066E-2                 |
| 2.5             | 2.4992          | 1.983E-2                 |
| 0.625           | 2.4992          | 1.999E-2                 |
| 0.04            | 2.4992          | 2.044E-2                 |

<br>

While channel 1 error falls moving from 40 kHz to 10 kHz sampling frequency, there is not much change after that. I used a frequency of 2.5 kHz 20 trials, 5 wave periods per trial, and 200 samples per wave to obtain final values for calibration slope and offset for the current loop interface. Those values are stored in [Calibration_Params.json](Calibration_Params.json) and are reported here:

|                     | Channel 1 | Channel 2 |
|---------------------|-----------|-----------|
| Slope (mA / V)        | 2.499177  | 2.499259  |
| Interecept (mA)     | 7.2334E-3 | 8.4657E-3 |
| Standard Error (mA) | 2.088E-2  | 2.013E-2  |
| R Squared           | 0.99999   | 0.99999   |

<br>

# Electric Regulator Calibration
## Materials
- Two electronic pressure regulators, model ITV2050-04N3S4-X27
- A calibrated pressure transducer (100 PSI rating), P/N AXD1100PG2M1102FCN S/N 12688243
- NI-DAQ USB-6421, S/N 283489E
- 24V Power supply, model LYD1302405000
- Lab custom current loop interface
- Three twisted pairs of 24 AWG wire ~150 mm long

## Setup
The following connections were made with twisted pairs, where every 2 rows starting from the top is a twisted cable pair:
| NI-DAQ Port | Current Loop Interface Port |
|-------------|-----------------------------|
| AO0         | AO FROM DAQ: 1+             |
| Gnd         | AO FROM DAQ: 1-             |
| AI0         | AI TO DAQ: V1               |
| AI8         | AI TO DAQ: GND              |
| AI1         | AI TO DAQ: V2               |
| AI9         | AI TO DAQ: GND              |

<br>

The following connections were made between the regulator and the current loop interface:
| Regulator Wire | Current Loop Interface Port |
|----------------|-----------------------------|
| Brown          | PWR OUT: V+                 |
| Blue           | PWR OUT: V-                 |
| White          | CURR OUT: I1                |
| Black          | CURR IN: I2                 |

<br>

The following connections were made between the pressure tranducer and the current loop interface:
| Transducer Wire | Current Loop Interface Port |
|-----------------|-----------------------------|
| Red             | Curr IN: V+                 |
| Black           | Curr IN: I1                 |
| Shield          | N/A                         |


- The DAQ was connected to the lab computer via USB-C
- The 24V power supply was connected to the current loop interface via barrel jack.
- The regulator manifold was connected to a line regulated to 80 PSI from the wall as read by the pressure indicator on the manual regulator
- The pressure transducer was connected directly to the regulator outlet by 1/4" OD tubing ~40 mm long
- All other outlets on the regulator manifold were plugged with 1/4" tubing connected to a closed valve

I assume a linear relationship from 0 to 100 PSI acting on the pressure transducer to 4 to 20 mA of output current, which is supported by its calibration data. The pressure transducer was directly connected to the output of the regulator, and the regulator manifold was supplied with a regulated 80 PSI from the wall.

Below are images of the wiring setup and pneumatic setup for this calibration:
![](Images/Setup/PneumaticCalibrationWiring.jpg)

![](Images/Setup/PneumaticCalibrationAir.jpg)

## Methods & Results
I first wanted to test the transient response for these regulators, so I looked at the step response. To get the step response, I used a square wave with 2s period and 10kS per period. The measured pressure data was very noisy, so I applied a lowpass filter (`scipy.signal.butter`) with cutoff frequency of 50 Hz to eliminate most of the noise. The result of this step response is shown below:
![](Images/Figures/RegulatorTimeResponse.png)

<br>

I calculated the 95% settling time off of the filtered transducer signal in code, which yielded: