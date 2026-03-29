## Final Analysis
### Component list
- [XTR116U](https://www.ti.com/lit/ds/symlink/xtr116.pdf?ts=1774598215051&ref_url=https%253A%252F%252Fwww.mouser.cn%252F): current transmitter (SOIC 8 package)
- [NI DAQ USB-6421](https://www.ni.com/docs/en-US/bundle/usb-6421-specs/page/specs.html#GUID-9F1851E2-8975-4F76-8A53-6D161C828398__GUID-C57C375E-2FA6-4D42-B253-B50185774842): voltage controller @ voltage measurment
- [RT1206BRD0740KL](https://www.digikey.com/en/products/detail/yageo/RT1206BRD0740KL/5936957): R_in for XTR control: input resistor for voltage to current conversion (1206 package)
- [RNCF1206TKW250R](https://www.digikey.com/en/products/detail/stackpole-electronics-inc/RNCF1206TKW250R/24819171): load resistor for current to voltage conversion (1206 package)
- [FZT653TA](https://www.digikey.com/en/products/detail/diodes-incorporated/FZT653TA/92830): external transistor for XTR (SOT-223-3 package)
- [SMBJ5362B-TP](https://www.digikey.com/en/products/detail/mcc-micro-commercial-components/SMBJ5362B-TP/1636184): Zener diode for overvoltage protection (DO-214AA package)
- [1N4148](https://www.digikey.com/en/products/detail/onsemi/1N4148/458603): reverse-voltage protection diode (DO-35) package
- [GCM21B5G1H103FA16L](https://www.digikey.com/en/products/detail/murata-electronics/GCM21B5G1H103FA16L/17847866): decoupling capacitor (0805 package)
- [CL0612KRX7R9BB104](https://www.digikey.com/en/products/detail/yageo/CL0612KRX7R9BB104/5884876): bypass capacitor (0805 package)

### To offset or not to offset
I can use the on-board voltage reference of the XTR11X to create a constant 4 mA zero-level current output from the transmitter. This would reduce the range the DAQ needs to control the current transmission for, from 0-20 mA to 4-20 mA. To see if this is worth it, we need to compare the minimum resolution of the DAQ at the larger 0-20 mA range to the span error of the XTR itself. If the DAQ is capable of theoretically driving output currents with error smaller than the span error of the XTR, then we can be confident it's not necessary to include a bias current from the voltage reference.

The NI DAQ USB-6421 has an analog output range of +/- 10V, though we will only be using the positive side (0-10V). The DAQ has a rated absolute accuracy at 10 years of 3.487 mV. With 10 V corresponding to an output current of 25 mA (maximum of linear range of XTR116), 3.487 mV of error corresponds to an output current of 8.72 uA. The XTR116U has a typical span error of 0.05%, which at the same output current of 25 mA equates to 12.5 uA of error. This means that the *maximum* error of the NI DAQ is less than the *typical* error of the XTR, thus the XTR's error dominates and there's no need to create a bias current to get more resolution out of the NI DAQ.

### Selecting an input resistor
The maximum 10V input of the NI DAQ needs create the maximum 25 mA output of the XTR. The XTR116 has a 100X gain of input to output current, so I need a resistor that will allow 250 uA of current to flow at 10V. This comes out to 40 kohm. 250 uA of current across this resistor is equivalent to 2.5 mW of power. Looking on Digikey for a suitable resistor, the best we can do is +/- 0.1% tolerance, +/- 25 ppm/C temp stability with the [RT1206BRD0740KL](https://www.digikey.com/en/products/detail/yageo/RT1206BRD0740KL/5936957).

The resistance error doesn't matter too much, as the system will be calibrated and the resistor's deviation from the true value of 40 kohm will be captured in that calibration. The maximum error to output current is 25 uA or 0.1% FS error @ 25 mA. This is much less than what would be necessary to trip over-scale limit in the XTR or controlled components, and is comfortably less the 0.2% FS sensitivity of the ITV 2025 pressure regulators we have.

The resistor's temperature dependence may matter if the temperature fluctuates significantly during use. The input power is likely small enough to not significantly affect the temperature of the resistor, but I will conservatively use a 10C change to estimate maximum temperature-based error. This temperature change would cause a 6.25 uA change in output current, which is basically nothing.

### Selecting an output resistor
All of the current transmitters we have (pressure regulators and pressure transmitters) can supply a maximum load impeadance of 250 ohms, which will provide 0-5 V output. At that voltage range, the DAQ has a measuring accuracy of 1.704 mV @ 10yrs, so we should keep error in voltage readings caused by resistor error to less than that value.

The resistor will need to handle 25 mA, or a power of 0.156 W. Looking to Digikey, the best option is [RNCF1206TKW250R](https://www.digikey.com/en/products/detail/stackpole-electronics-inc/RNCF1206TKW250R/24819171), with +/- 0.01% tolerance and +/- 2 ppm/C temp stability. Given this resistor has more power flowing through it, we can assume a higher conservative maximum temperature change of 25C. Combining both tolerance error and temperature error with the assumed 25C increase in temperature yields an error to measured voltage of only 0.75 mV. That's much less than the minimum measuring accuracy of 1.704 mV and pretty close to the theoretical maximum resolution of 0.15 mV (from 15 bits 0-5V).

### Selecting an external transistor
The XTR requires an external NPN transistor to function. The datasheet gives specs for electrical properties using TIP29C. Looking on Digikey, the TIP29C is only available with through-hole mounting, and I'd like to choose a surface-mounted alternative. The XTR datasheet says that, "the XTR11x is designed to use virtually any NPN transistor with sufficient voltage, current, and power rating" so I'm not too worried about specs like gain or frequency transition. However, I still was able to find a transistor that has the same or better characteristics to the TIP29C, the [FZT653TA](https://www.digikey.com/en/products/detail/diodes-incorporated/FZT653TA/92830)

### Selecting a Zener Diode
The XTR116 datasheet suggests using a Zener diode in parallel with I_o and V+ for overvoltage surge protection. They suggest using a 36V protection diode for a loop voltage of 30V, but suggest to use "as low a voltage rating as possible". My loop voltage will be 24V, so keeping the same voltage tolerance I should probably use a 30V Zener diode for protection.

Their recommended diode has a max power of 1 W, a max impedance of 50 ohms, and a reverse current leakage of 5 uA @ 27.4 V. I searched on Digikey for Zener diodes meeting or beating these specs with a Vz of 28-30V. The best fit was [SMBJ5362B-TP](https://www.digikey.com/en/products/detail/mcc-micro-commercial-components/SMBJ5362B-TP/1636184), which has 28V Vz (same percent margin protection over 24V as datasheet's 36V over 30V), 5 W power, 6 ohm impedance, and 500 nA reverse current leakage.

### Do we need a diode bridge
The XTR116 datasheet shows a diode bridge between the loop voltage and XTR. This ensures the XTR will work correctly regardless of loop voltage polarity. I don't really care about that functionality, as I can just... plug in things the right way. However, I should definitely protect the loop against reverse voltage, so instead of four diodes to form the bridge I'll only need one in series with the loop positive and the V+ pin. This causes a ~0.7 V drop, which isn't significant for my purposes. The datasheet recommends the [1N4148](https://www.digikey.com/en/products/detail/onsemi/1N4148/458603) diode.

### Decoupling capacitor
The XTR datasheet recommends a 10nF decoupling capacitor across V+ and I_o. Looking on Digikey for ceramic capacitors, I found the [GCM21B5G1H103FA16L](https://www.digikey.com/en/products/detail/murata-electronics/GCM21B5G1H103FA16L/17847866).

### Bypass capacitor
The XTR datasheet recommends connecting "low-ESR, 0.1uF ceramic bypass capacitors between the supply pin and ground". I found the [CL0612KRX7R9BB104](https://www.digikey.com/en/products/detail/yageo/CL0612KRX7R9BB104/5884876) on Digikey, which has +/- 10% error, 50V rating, and low ESL.

This cap may not be a thing though, as there's no supply or ground pin on the chip itself. I started a TI E2E [forum post](https://e2e.ti.com/support/amplifiers-group/amplifiers/f/amplifiers-forum/1631118/xtr116-xtr116-bypass-capacitor-placement) about this to see if I can get to the bottom of it.