import numpy as np
import scipy as sp
import matplotlib.pyplot as plotter
import nidaqmx
from nidaqmx.constants import Edge
from nidaqmx.stream_readers import AnalogSingleChannelReader
from nidaqmx.stream_writers import AnalogSingleChannelWriter

# READ ME
# This script is an example of synchronised read/writing from the NI DAQ.
# The wiring setup is Ao0 to Ai0, Gnd to Ai8.
# The expected behavior is input voltage exactly the same as output voltage

print("\n----- Testing Single Channel Read/Write -----")

# Hardware info
device_name = "LabDAQ"
input_channel = device_name + "/ai1"
output_channel = device_name + "/ao0"

# Validate hardware info
daq_system = nidaqmx.system.System.local()
device_names = [device.name for device in daq_system.devices]
if device_name in device_names:
    print(device_name + " is connected")
else:
    expt_msg = "Device \'{}\' is not connected".format(device_name)
    raise Exception(expt_msg)


# Set up output data array
sample_freq = 2.0
end_time = 5.0
num_samples = int(sample_freq*end_time)

t = np.arange(num_samples)/sample_freq
sig_freq = 0.5
sig_amp = 5
sig_phase = 0
# sin wave: sig = sig_amp*np.sin(2*np.pi*sig_freq*(t + sig_phase))
sig = sig_amp*sp.signal.sawtooth(2*np.pi*sig_freq*(t + sig_phase),0.5)

print("Collecting data...")
with nidaqmx.Task() as read_task, nidaqmx.Task() as write_task:
    # Configure input channel (leader clock)
    read_task.ai_channels.add_ai_voltage_chan(input_channel,
                                              min_val=-5, max_val=5,
                                              terminal_config=nidaqmx.constants.TerminalConfiguration.DIFF)     # We must use differential mode to avoid connecting the negative "AO From DAQ" reference to the 24V ground                                                                                              # For this example, the pins will be ao0 as + and ao8 as - (vertical pairs)
    
    read_task.timing.cfg_samp_clk_timing(rate=sample_freq,
                                         sample_mode=nidaqmx.constants.AcquisitionType.FINITE,                  # we know the number of samples to collect
                                         samps_per_chan=num_samples)
    
    # Configure output channel (follower clock)
    write_task.ao_channels.add_ao_voltage_chan(output_channel,
                                               min_val=-5, max_val=5)
    
    write_task.timing.cfg_samp_clk_timing(rate=sample_freq,
                                          source="/{}/ai/SampleClock".format(device_name),                      # sample using the input clock as the leader
                                          sample_mode=nidaqmx.constants.AcquisitionType.FINITE,                 # we know the number of samples to collect
                                          samps_per_chan=num_samples)


    
    write_task.triggers.start_trigger.cfg_dig_edge_start_trig(read_task.triggers.start_trigger.term,Edge.RISING)            # make sure both tasks start at the same time
    write_task.write(sig, auto_start=False)
    write_task.start()
    input_data = read_task.read(num_samples)

    # Because of how sampling is handled, we need to shift the input array back one sample for it to align with the output array
    # input_data = input_data[1:]

print("Plotting data...")

# Plot data
fig, axs = plotter.subplots(2,2)
axs[0,0].plot(t,sig)
axs[0,0].set_title('Output')
axs[0,0].set(xlabel='time (s)', ylabel='AO Voltage (V)')

axs[1,0].plot(t,input_data)
axs[1,0].set_title('Input')
axs[1,0].set(xlabel='time (s)', ylabel='AI Voltage (V)')

axs[0,1].plot(sig,input_data)
axs[0,1].set_title('Input vs Output')
axs[0,1].set(xlabel='AO Voltage (V)', ylabel='AI Voltage (V)')

plotter.show()

print("\n")