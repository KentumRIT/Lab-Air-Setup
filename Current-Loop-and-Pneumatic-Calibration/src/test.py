from SamplingFuncs.Daq6421 import Daq6421
from SamplingFuncs.CalibrationFunctions import generate_waveform
from SamplingFuncs.CalibrationFunctions import get_best_fit
import numpy as np
import scipy as sp

# Constants
json_filename = "Calibration_Params.json"
samp_per_wave = 8000                        # number of samples per period of wave in calibration data collection
samp_freq = 2000                            # sample frequency in [Hz]
num_wave = 2                                # number of wave periods per trial in calibration data collection
num_trials = 1                              # number of trials to combine to get complete calibration data (necessary to separate from num_wave due b/c of max buffer size)


# Create a triangle wave form
def triangle_wave(x):
    return sp.signal.sawtooth(x, width=0.5)

wave_frequency = samp_freq/samp_per_wave

# Create a square wave form
def square_wave(x):
    return sp.signal.square(x - np.pi/2, duty=0.5)

t,sig1 = generate_waveform(square_wave,num_wave,(0,2.1),samp_per_wave,samp_freq,None)
t = t[:-1]
sig = sig1[:-1]

# Connect to the DAQ and get data with the above wave form
my_daq = Daq6421()
my_daq.setup()
my_daq.set_PFI_trigger(8,False)

t_total = None
sig_total = None
data_total = None
for trial in range(num_trials):
    print(f"\rtrial {trial+1}/{num_trials}", end="")
    data = my_daq.read_write_AiAo(samp_freq,sig,{0},{0},(0,7))

    # concatenate data from multiple trials
    if t_total is None:
        t_total = t
    else:
        t_total = np.hstack((t_total,t+t_total[-1]))
    if sig_total is None:
        sig_total = sig
    else:
        sig_total = np.hstack((sig_total,sig))
    if data_total is None:
        data_total = data
    else:
        data_total = np.hstack((data_total,data))

# Get best fit data from results
get_best_fit(t_total,sig_total,data_total,[],"Measured Pressure (PSI)")