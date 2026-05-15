from SamplingFuncs.Daq6421 import Daq6421
from SamplingFuncs.CalibrationFunctions import generate_waveform
from SamplingFuncs.CalibrationFunctions import get_best_fit
import numpy as np
import scipy as sp
from scipy.signal import butter, filtfilt
import json


def volts_to_psi(volts: np.ndarray[float]) -> np.ndarray[float]:
    """ INFO
        Purpose
          - Converts voltage measured by DAQ to pressure for calibrated 100 PSI transducer (channel 0)
                and regulator built in transducer (channel 1)
        
        ARGUMENTS
          - volts:      data from DAQ

        RETURNS
          - psi: pressure measured
        """
    
    mA = 1000*(1/250)*volts

    pressure_range_dat = [None,None]

    # Calibrated transducer
    pressure_range_dat[0] = (0.0,100.0)         # 0-100 PSI

    # Built in transducer
    pressure_range_dat[1] = (0.725,130.534)     # 0.005-0.9 MPa

    psi = np.zeros(volts.shape)
    current_range = (4.0,20.0)                  # 4-20 mA loop current  
    for i in range(2):
        
        pressure_range = pressure_range_dat[i]
        m = (pressure_range[1] - pressure_range[0])/(current_range[1] - current_range[0])
        b = pressure_range[0] - m*current_range[0]

        psi[i,:] = m*mA[i,:] + b

    return psi

# Constants
json_filename = "Calibration_Params.json"
samp_per_wave = 10000                        # number of samples per period of wave in calibration data collection
num_wave = 1                                # number of wave periods per trial in calibration data collection
wave_period = 2                             # period of a single wave form in [s]
num_trials = 1                              # number of trials to combine to get complete calibration data (necessary to separate from num_wave due b/c of max buffer size)
# filter_window_size = 10                     # number of samples for window size of moving average filter
cutoff_frequency = 50                      # cutoff frequency for butter filter

# Get 4-20 mA voltage bounds from current loop interface calibration parameters
with open(json_filename, "r") as f:
    data = json.load(f)

    channel1 = data["CurrentLoop1"]

m = channel1["m"]
b = channel1["b"]
s_est = channel1["s_est"]
r2 = channel1["r2"]

current_bounds = np.array([4,20])           # units of mA
voltage_bounds = (current_bounds - b)/m     # units of V


# Create wave form
def triangle_wave(x):
    return sp.signal.sawtooth(x, width=0.5)

def square_wave(x):
    return sp.signal.square(x-(0.5*wave_period), duty=0.5)

t,sig = generate_waveform(square_wave,num_wave,voltage_bounds,samp_per_wave,None,1/wave_period)
fs = 1/(t[1]-t[0])  # get sampling frequency from waveform

# Connect to the DAQ and get data with the above wave form
my_daq = Daq6421()
my_daq.setup()

t_total = None
sig_total = None
data_total = None
for trial in range(num_trials):
    print(f"\rtrial {trial+1}/{num_trials}", end="")
    data = my_daq.read_write_AiAo(fs,sig,{0,1},{0})

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

# Filter noisy data
def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter(order, cutoff, fs=fs, btype='low', analog=False)
    y = filtfilt(b, a, data)
    return y

def moving_average_filter(data,n):
    b = np.ones(n)/n
    a = 1
    y = filtfilt(b,a,data)
    return y

data_total = volts_to_psi(data_total)

chan_1_filtered = butter_lowpass_filter(data_total[0,:],cutoff_frequency,fs)
chan_2_filtered = butter_lowpass_filter(data_total[1,:],cutoff_frequency,fs)

# chan_1_filtered = moving_average_filter(data_total[0,:],filter_window_size)
# chan_2_filtered = moving_average_filter(data_total[1,:],filter_window_size)

data_total = np.vstack((data_total,chan_1_filtered,chan_2_filtered))

# Get best fit data from results
get_best_fit(t_total,sig_total,data_total,[(0,0),(0,1)],"Measured Pressure (PSI)",linestyles= ['dotted','dotted','solid','solid'], linenames= ["Transducer Unfiltered","Regulator Unfiltered","Transducer Filtered","Regulator Filtered"])
