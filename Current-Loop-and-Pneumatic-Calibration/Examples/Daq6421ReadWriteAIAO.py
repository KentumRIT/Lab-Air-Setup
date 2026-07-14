import numpy as np
import scipy as sp
import matplotlib.pyplot as plotter
from SamplingFuncs.Daq6421 import Daq6421

print("-------- TEST --------\n")
frequency_scale = 1/4   # increase base sampling frequency of 1Hz with this

# Set up output data array
fs = 200 * frequency_scale      # change 100 to as low as 4 to reduce num_samples
end_time = 1 / frequency_scale
num_samples = int(fs*end_time)

t = np.arange(num_samples)/fs
sig_freq = 2 * frequency_scale
sig_amp = 2
sig_phase = 0
# sin wave: sig = sig_amp*np.sin(2*np.pi*sig_freq*(t + sig_phase))
sig = sig_amp*sp.signal.sawtooth(2*np.pi*sig_freq*(t + sig_phase),0.5) + sig_amp

sig = np.vstack((sig,sig))

my_daq = Daq6421()
my_daq.setup()
input_data = my_daq.read_write_AiAo(fs,sig,{0,1},{0,1},(-5,5),True)


# MULTI_CHANNEL IN AND OUT PLOTTING (2 IN 2 OUT)
fig, axs = plotter.subplots(2,2)
axs[0,0].plot(t,sig[0,:],marker='v',linestyle='-',color='k',label='Out1')
axs[0,0].plot(t,sig[1,:],marker='^',linestyle='--',color='r',label='Out2')
axs[0,0].set_title('Output Vs Time')
axs[0,0].set(xlabel='time (s)', ylabel='AO Voltage (V)')

axs[1,0].plot(t,sig[0,:],marker='v',linestyle='None',color='k',label='Out1')
axs[1,0].plot(t,sig[1,:],marker='^',linestyle='None',color='r',label='Out2')
axs[1,0].plot(t, input_data[0,:],
              marker='o', linestyle='None', color='g',
              label='Channel 1')
axs[1,0].plot(t, input_data[1,:],
              marker='s', linestyle='None', color='b',
              label='Channel 2')
axs[1,0].set_title('Signals Vs Time')
axs[1,0].set(xlabel='time (s)', ylabel='AI Voltage (V)')
axs[1,0].legend()


axs[0,1].plot(sig[0,:], input_data[0,:],
              marker='o', linestyle='None', color='r',
              label='Channel 1')
axs[0,1].plot(sig[1,:], input_data[1,:],
              marker='s', linestyle='None', color='g',
              label='Channel 2')
axs[0,1].set_title('Input vs Output')
axs[0,1].set(xlabel='AO Voltage (V)', ylabel='AI Voltage (V)')
axs[0,1].legend()

""" MULTI-CHANNEL IN SINGLE CHANNEL OUT PLOTTING (3 IN 1 OUT)
fig, axs = plotter.subplots(2,2)
axs[0,0].plot(t,sig,marker='o',linestyle='-',color='k')
axs[0,0].set_title('Output Vs Time')
axs[0,0].set(xlabel='time (s)', ylabel='AO Voltage (V)')

axs[1,0].plot(t, sig,'k--',label='Output')
axs[1,0].plot(t, input_data[0,:],
              marker='o', linestyle='None', color='r',
              label='Channel 1')

axs[1,0].plot(t, input_data[1,:],
              marker='s', linestyle='None', color='g',
              label='Channel 2')

axs[1,0].plot(t, input_data[2,:],
              marker='^', linestyle='None', color='b',
              label='Channel 3')

axs[1,0].set_title('Signals Vs Time')
axs[1,0].set(xlabel='time (s)', ylabel='AI Voltage (V)')
axs[1,0].legend()


axs[0,1].plot(sig, input_data[0,:],
              marker='o', linestyle='None', color='r',
              label='Channel 1')

axs[0,1].plot(sig, input_data[1,:],
              marker='s', linestyle='None', color='g',
              label='Channel 2')

axs[0,1].plot(sig, input_data[2,:],
              marker='^', linestyle='None', color='b',
              label='Channel 3')

axs[0,1].set_title('Input vs Output')
axs[0,1].set(xlabel='AO Voltage (V)', ylabel='AI Voltage (V)')
axs[0,1].legend()
"""

""" SINGLE CHANNEL IN/OUT PLOTTING (1 IN 1 OUT)
fig, axs = plotter.subplots(2,2)
axs[0,0].plot(t,sig,'k-')
axs[0,0].set_title('Output Vs Time')
axs[0,0].set(xlabel='time (s)', ylabel='AO Voltage (V)')

axs[1,0].plot(t,sig,'k--',label='Output')
axs[1,0].plot(t,input_data,marker='s',linestyle='None',color='r',label='Input')
axs[1,0].set_title('Signals vs Time')
axs[1,0].set(xlabel='time (s)', ylabel='AI Voltage (V)')
axs[1,0].legend()

axs[0,1].plot(sig,input_data)
axs[0,1].set_title('Input vs Output')
axs[0,1].set(xlabel='AO Voltage (V)', ylabel='AI Voltage (V)')
"""

plotter.show()

print("\n")