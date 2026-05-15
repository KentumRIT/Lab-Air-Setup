from typing import Callable
import numpy as np
import matplotlib.pyplot as plotter
import json
from itertools import cycle

def generate_waveform(wave_function: Callable, wave_count: int, bounds: tuple[float,float], samples_per_wave: float = None, sampling_frequency: float = None, wave_frequency: float = None) -> tuple[np.ndarray[np.float64], np.ndarray[np.float64]]:
    """ INFO
        Purpose
          - Creates a wave defined by wave_function with frequency wave_frequency divided into samples_per_wave parts that spans from bounds[0] to bounds[1] volts
        
        ARGUMENTS
          - wave_function:      a function handle for a wave generator with base period 2*pi and base P2P amplitude 1
                                    for example, can pass a triangle wave in using: 
                                        triangle_wave where triangle_wave = partial(scipy.sawtooth, width=0.5)
                                        or lambda x: scipy.sawtooth(x, 0.5)
          - wave_style:         triangle, sin, cos, 
          - wave_count:         number of periods in signal
          - bounds:             (low,high) upper and lower bounds for signal
          
          Note: YOU MUST DEFINE EXACTLY 2/3 OF:
          - samples_per_wave :  number of points per period of wave
          - sampling_frequency: frequency of the sample points within the wave
          - wave_frequency:     frequency of the overall waveform
          
        
        RETURNS
          - t:      time array (1xN)
          - sig:    signal array (1xN)
    """

    # ---------- CALCULATE MISSING ARGUMENT ----------
    if samples_per_wave is None and (sampling_frequency is not None and wave_frequency):                # define samples_per_wave if left undefined
        samples_per_wave = sampling_frequency/wave_frequency

    elif sampling_frequency is None and (samples_per_wave is not None and wave_frequency is not None):  # define sampling_frequency if left undefined
        sampling_frequency = samples_per_wave*wave_frequency

    elif wave_frequency is None and (samples_per_wave is not None and sampling_frequency is not None):  # define wave_frequency if left undefined
        wave_frequency = sampling_frequency/samples_per_wave
    else:
        raise ValueError("Must define exactly 2/3 of last 3 arguments in \'generate_waveform\'")


    # ------------ CALCULATE WAVE SIGNAL -------------
    num_samples = int(samples_per_wave*wave_count) + 1      # total number of samples in waveform + 1 ensures we always end at 0, otherwise would end and step before 0
    t = np.arange(num_samples)/sampling_frequency


    sig_amp = (bounds[1]-bounds[0])/2                       # single-ended amplitude of signal

    sig = sig_amp*wave_function(2*np.pi*wave_frequency*t) + sig_amp + bounds[0]

    return t, sig  # time, volts

def get_best_fit(time: np.ndarray[np.float64], analog_out_data: np.ndarray[np.float64], measured_data: np.ndarray[np.float64], out_in_pairs: list[tuple[int,int]], y_name: str = "AI Voltage (V)", save_data: bool = False, parameter_name: str = "", filename: str = "Calibration_Params.json", linenames: list[str] = None, linestyles: list[str] = None):
    """ INFO
        Purpose
          - Plots data stepwise due to NIDAQ stepwise update
          - Creates best linear fit for each pair of input_data vs measured_data
          - Exports results to JSON file
        
        ARGUMENTS
          - time:               1xN array of sequential time values tied to input/output data
          - analog_out_data:    AxN array where A is the number of output channels and N is the number of samples
                                    stores sequential output data for each output pin (one per row) in [V]
          - measured_data:      BxN array where B is the number of input channels and N is the number of samples
                                    stores sequential input data for each input pin (one per row)
                                    can be analog input data directly or can be transformed data to new units
          - out_in_pairs:       List of 2x1 tuples (AO,Measured) connecting rows of analog_out_data to measured_data
                                    for example [(2,1)] would mean to fit row 2 of analog_out_data and row 1 of measured_data
          - y_name:             Only used for plotting, the name to give the Y-axis (analog in axis) in AI vs AO plot
          - save_data:          True to save to JSON file, False to leave JSON data untouched
          - parameter_name:     Name for the parameter being fit (i.e. "CurrentLoop") to be used when storing data in the JSON file
          - filename:           File name of the JSON file for data export
          - linenames:          Names for each row in measured_data to be put in legend if "none", will use a marker style
          - linestyles:         line styles for each row in measured_data
                                             
        Outputs to JSON for each output pair:
          - m:      slope of LoBF
          - b:      intercept of LoBF
          - s_est:  standard error of the estimate for LoBF
          - r2:     R squared for LoBF
    """


    # -------------------- VALIDATE ARGUMENTS --------------------
    # Get implied data from array input arguments
    if time.ndim != 1:
        raise ValueError("'time' should be 1D array")
    num_samples1 = time.shape[0]
    
    if analog_out_data.ndim == 1:
        num_ao_channels = 1
        num_samples2 = analog_out_data.shape[0]
        analog_out_data = analog_out_data[np.newaxis, :]        # reshape to 2D for later operations to work smoothly
    elif analog_out_data.ndim == 2:
        num_ao_channels = analog_out_data.shape[0]
        num_samples2 = analog_out_data.shape[1]
    else:
        raise ValueError("'analog_out_data' must be 1D or 2D")
    
    if measured_data.ndim == 1:
        num_in_channels = 1
        num_samples3 = measured_data.shape[0]
        measured_data = measured_data[np.newaxis, :]          # reshape to 2D for later operations to work smoothly
    elif measured_data.ndim == 2:
        num_in_channels = measured_data.shape[0]
        num_samples3 = measured_data.shape[1]
    else:
        raise ValueError("'measured_data' must be 1D or 2D")
    
    # Ensure number of samples is same across time, AO, and AI
    if not (num_samples1 == num_samples2 == num_samples3):
        raise ValueError("Number of samples is not consistent across argument inputs")
    num_samples = num_samples1

    # Check out_in_pairs type and size
    if not isinstance(out_in_pairs, (list,tuple)):
        raise TypeError("out_in_pairs must be a list or tuple")

    if not all(isinstance(x, tuple) and len(x) == 2 for x in out_in_pairs):
        raise TypeError("all elements of 'out_in_pairs' must be tuples of length 2")
    num_fits = len(out_in_pairs)

    # Check that linenames and linestyles are correct size and populate them if left blank
    if linenames is not None:
        if len(linenames) != num_in_channels:
            raise ValueError("'linenames' must have exactly one entry per row in measured_data")
    else:
        linenames = [f"Measured row {i+1} data" for i in range(num_in_channels)]
        
    if linestyles is not None:
        if len(linestyles) != num_in_channels:
            raise ValueError("'linestyles' must have exactly one entry per row in measured_data")
    else:
        linestyles = ["dotted" for i in range(num_in_channels)]


    # ---------------------- CALCULATE LoBF ----------------------
    if len(out_in_pairs) > 0:
        lobf_y_dat = np.zeros((num_fits,num_samples))
        s_est_dat = np.zeros(num_fits)

        for fit in range(num_fits):
            fit_pair = out_in_pairs[fit]
            ao_channel = fit_pair[0]
            in_channel = fit_pair[1]

            if not(0 <= ao_channel < num_ao_channels):
                raise ValueError("value for analog out in 'out_in_pairs' is invalid, falls below 0 or outside of range of number of rows in analog_out_data")
            if not(0 <= in_channel < num_in_channels):
                raise ValueError("value for analog in in 'out_in_pairs' is invalid, falls below 0 or outside of range of number of rows in measured_data")

            x = analog_out_data[ao_channel,:]
            y = measured_data[in_channel,:]

            m,b = np.polyfit(x,y,1)                     # LoBF
            y_pred = m*x + b                            # predicted current values from LoBF
            ss_res = np.sum(np.square(y_pred - y))      # sum of square residuals
            s_est = np.sqrt(ss_res/(num_samples-2))     # standard error of the estimate
            y_mean = np.average(y)
            ss_tot = np.sum(np.square(y-y_mean))        # sum of total squared error
            r2 = 1-(ss_res/ss_tot)                      # R squared

            lobf_y_dat[fit,:] = y_pred
            s_est_dat[fit] = s_est

            # Update LoBF data for channel
            if save_data:
                with open(filename, "r") as f:
                    data = json.load(f)

                data[f"{parameter_name}{fit+1}"] = {
                    "m": m,
                    "b": b,
                    "s_est": s_est,
                    "r2": r2
                }

                with open(filename, "w") as f:
                    json.dump(data, f, indent=4)



    # ------------------------- PLOT DATA ------------------------
    # Raw signal data
    fig1, axs1 = plotter.subplots()
    axs1_2 = axs1.twinx()

    colors = cycle(plotter.cm.tab10.colors)  # share color cycle between axes so lines don't have the same colors

    for ao_channel in range(num_ao_channels):
        c = next(colors)
        axs1.step(time,analog_out_data[ao_channel,:], marker = 'o', linestyle='dashed', color=c, label=f"AO row {ao_channel} data", where='post')
        
    for in_channel in range(num_in_channels):
        c = next(colors)
        if linestyles[in_channel] == "none":
            markerstyle = "o"
        else:
            markerstyle = "none"
        axs1_2.step(time,measured_data[in_channel,:], marker = markerstyle, linestyle=linestyles[in_channel], color=c, label=linenames[in_channel], where='post')

    axs1.set_title('Signals Vs Time')
    axs1.set(xlabel='time (s)', ylabel='AO Voltage (V)')
    axs1_2.set(ylabel=y_name)
    lines1, labels1 = axs1.get_legend_handles_labels()
    lines2, labels2 = axs1_2.get_legend_handles_labels()
    axs1.legend(lines1 + lines2, labels1 + labels2, loc='best')


    # PLOT AGAINST LoBF
    if len(out_in_pairs) > 0:
        rows = int(np.ceil(np.sqrt(num_fits)))
        cols = int(np.ceil(num_fits / rows))

        fig2,axs2 = plotter.subplots(rows,cols)
        for fit in range(num_fits):
            col = fit//rows
            row = fit % rows

            if cols == 1:
                if rows == 1:
                    axs = axs2
                else:
                    axs = axs2[row]
            else:
                axs = axs2[row,col]

            fit_pair = out_in_pairs[fit]
            ao_channel = fit_pair[0]
            in_channel = fit_pair[1]

            x = analog_out_data[ao_channel,:]
            y = measured_data[in_channel,:]

            y_est = lobf_y_dat[fit,:]
            y_est_up = y_est + 2*s_est_dat[fit]
            y_est_down = y_est - 2*s_est_dat[fit]

            axs.plot(x,y,'k-',label=f"AO row {ao_channel}, Measured row {in_channel}")
            axs.plot(x,y_est_up,'r--',label="+2 sigma")
            axs.plot(x,y_est_down,'r--',label="-2 sigma")
            axs.set_title(f'Calibration Fit For AO/AI Pair {fit}')
            axs.set(xlabel='AO Voltage (V)', ylabel=y_name)
            axs.legend()

    plotter.show()
    