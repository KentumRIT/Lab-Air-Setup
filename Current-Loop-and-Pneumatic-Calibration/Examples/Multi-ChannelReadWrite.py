import numpy as np
import matplotlib.pyplot as plotter
import nidaqmx
from nidaqmx.constants import Edge
from nidaqmx.stream_readers import AnalogMultiChannelReader
from nidaqmx.stream_writers import AnalogMultiChannelWriter

# TODO:
#   - change method of shifting input arrays to instead just sample twice at every output point

# READ ME
# This script is an example of synchronised read/writing from the NI DAQ.
# The wiring setup is Ao0 to Ai0, Gnd to Ai8.
# The expected behavior is input voltage exactly the same as output voltage

# Print info about NI DAQ system
daq_system = nidaqmx.system.System.local()
daq_system.driver_version
for device in daq_system.devices:
    print(device)

# Hardware info
device_name = "LabDAQ"
input_channels = f"{device_name}/ai0,{device_name}/ai1"
output_channels = f"{device_name}/ao0,{device_name}/ao1"

# Set up output data array
sample_rate = 2.0
end_time = 5.0
half_samples = np.astype(np.ceil(end_time*sample_rate/2),int)
output_data = np.concatenate([np.linspace(0,10,half_samples),np.linspace(10,0,half_samples)])
num_samples = np.size(output_data)
time = np.linspace(0,end_time,num_samples)
print(num_samples)
output_data = np.stack([output_data,output_data])   # one row per channel

with nidaqmx.Task() as read_task, nidaqmx.Task() as write_task:
    # Configure input channel (leader clock)
    read_task.ai_channels.add_ai_voltage_chan(input_channels,
                                              min_val=0, max_val=10,
                                              terminal_config=nidaqmx.constants.TerminalConfiguration.DIFF)     # We must use differential mode to avoid connecting the negative "AO From DAQ" reference to the 24V ground
                                                                                                                # For this example, the pins will be ao0 as + and ao8 as - (vertical pairs)
    read_task.timing.cfg_samp_clk_timing(rate=sample_rate,
                                         sample_mode=nidaqmx.constants.AcquisitionType.FINITE,                  # we know the number of samples to collect
                                         samps_per_chan=num_samples)                                            
    
    # Configure output channel (follower clock)
    write_task.ao_channels.add_ao_voltage_chan(output_channels,
                                               min_val=0, max_val=10)
    write_task.timing.cfg_samp_clk_timing(rate=sample_rate,
                                          source=f"/{device_name}/ai/SampleClock",                              # sample using the output clock as the leader
                                          sample_mode=nidaqmx.constants.AcquisitionType.FINITE,                 # we know the number of samples to collect
                                          samps_per_chan=num_samples)

    write_task.triggers.start_trigger.cfg_dig_edge_start_trig(read_task.triggers.start_trigger.term)            # make sure both tasks start at the same time

    # Create reader and writer
    reader = AnalogMultiChannelReader(read_task.in_stream)
    writer = AnalogMultiChannelWriter(write_task.out_stream, auto_start=False)

    # Pre-allocate buffer for reader
    input_data = np.zeros((2, num_samples))

    # Run tasks, follower first
    writer.write_many_sample(output_data)
    write_task.start()
    reader.read_many_sample(input_data,number_of_samples_per_channel=num_samples)

    # Because of how sampling is handled, we need to shift the input array back one sample for it to align with the output array
    # ch1_data = input_data[0, 1:]
    # ch2_data = input_data[1, :-1]
    # input_data = np.stack([ch1_data,ch2_data])

# Plot data
fig, axs = plotter.subplots(2,2)
axs[0,0].plot(time,output_data[0,:],'r--',label='Channel 1')
axs[0,0].plot(time,output_data[1,:],'b-',label='Channel 2')
axs[0,0].set_title('Output')
axs[0,0].set(xlabel='time (s)', ylabel='AO Voltage (V)')
axs[0,0].legend()

axs[1,0].plot(time,input_data[0,:],'r--',label='Channel 1')
axs[1,0].plot(time,input_data[1,:],'b-',label='Channel 2')
axs[1,0].set_title('Input')
axs[1,0].set(xlabel='time (s)', ylabel='AI Voltage (V)')
axs[1,0].legend()

axs[0,1].plot(output_data[0,:],input_data[0,:],'r--',label='Channel 1')
axs[0,1].plot(output_data[1,:],input_data[1,:],'b-',label='Channel 2')
axs[0,1].set_title('Input vs Output')
axs[0,1].set(xlabel='AO Voltage (V)', ylabel='AI Voltage (V)')
axs[0,1].legend()

plotter.show()


