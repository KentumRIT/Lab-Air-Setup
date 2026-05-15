import numpy as np
import nidaqmx
from nidaqmx.stream_readers import AnalogMultiChannelReader
from nidaqmx.stream_writers import AnalogMultiChannelWriter
from nidaqmx.stream_readers import AnalogSingleChannelReader
from nidaqmx.stream_writers import AnalogSingleChannelWriter

class Daq6421:
    """ READ ME
    PURPOSE:
      - This class is built to handle single and multi-channel read/write operations on a single NI-DAQ USB-6421

    IMPLEMENTED FEATURES:
      - setup() validates device is connected
      - read_write_AiAo() validates arguments
      - read_write_AiAo() supports single or multi channel writing to Ai/Ao

    TODO:
      - add convert clock delay instead of increasing input samples by 1 and shifting first input channel
    """

    def setup(self, device_name:str = None):
        # Pulls the device name that will be used for future connections and ensures that DAQ is connected to the host
        self.device_name = device_name

        # Grab the host (computer) system info
        local_system = nidaqmx.system.System.local()
        driver_version = local_system.driver_version
        print(f"Local Version: DAQmx {driver_version.major_version}.{driver_version.minor_version}.{driver_version.update_version}")

        # Grab devices connected to the host computer and make sure device_name is among them
        device_names = [device.name for device in local_system.devices]

        # If no devices are connected, raise exception
        if len(device_names) == 0:
            raise RuntimeError("No DAQ devices connected to host")

        # If no device name was given, ensure only one device is connected and use that one
        if self.device_name is None:
            if len(device_names) == 1:
                self.device_name = device_names[0]
            else:
                expt_msg = "Device name must be specified when multiple DAQs are connected to host. Devices connected to host are:\n"
                for name in device_names:
                    expt_msg += f"   - {name}\n"
                raise ValueError(expt_msg)
            return

        # If a device name was given, ensure it's connected
        if self.device_name not in device_names:
            expt_msg = f"Device \'{self.device_name}\' is not connected. Devices connected to host are:\n"
            for name in device_names:
                expt_msg += f"   - {name}\n"
            raise ValueError(expt_msg)

    def read_write_AiAo(self, sample_update_rate: float, output_data: np.ndarray[np.float64], input_pins: set[int], output_pins: set[int], input_bounds: tuple[float] = (-10,10), differential_pair: bool = True) -> np.ndarray[np.float64]:
        """ INFO
        Purpose
          - Runs synchronous analog out, analog in tasks
          - Writes output_data sequentially to AO pins at
          - Returns observed voltage on input pins
        
        ARGUMENTS
          - sample_update_rate:   the sample rate for the input pins and update rate for the output pins in [Hz]
          - output_data:          AxN array where A is the number of output channels and N is the number of samples
                                      stores sequential output data for each output pin (one per row) in [V]
          - input_pins:           the pin numbers for the input pins to be used
          - output pins:          the pin numbers for the output pins to be used
          - input_bounds:         the expected voltage bounds for the input pins {low,high}, {-10,10} is max bounds in [V]
          - differential_pair:    True if input pins are to be used in differential pair mode, false for RSE mode
        
        RETURNS
          - input_data:           BxN array where B is the number of input channels and N is the number of samples
                                      stores sequential input data for each input pin (one per row) in [V]
        """
        
        # ----------------- VERIFY ARGUMENT TYPES -----------------
        if (type(input_pins) is not set) or (type(output_pins) is not set):
            raise TypeError("Expect \'set\' type for input_pins, output_pins")

        # extract some implied information in arguments
        is_in_multichan = len(input_pins) > 1
        is_out_multichan = len(output_pins) > 1


        # ---------------- CHECK ARGUMENT VALIDITY ----------------
        if sample_update_rate > 250000:                                     # sampling rate too high
            raise ValueError(f"Desired sample rate ({sample_update_rate}) "
                          "exceeds USB-6421 max sample/update rate of 250 kS/s")
        
        if max(input_pins) > 15 or min(input_pins) < 0:                     # input pins out of range
            raise ValueError("Input pins range from 0-15")
        
        if max(output_pins) > 1 or min(output_pins) < 0:
            raise ValueError("Output pins range 0-1")                       # output pins out of range
        
        if max(input_bounds) > 10 or min(input_bounds) < -10:               # input bounds out of range
            raise ValueError("AI max range is -10 V to 10 V")
        
        if is_out_multichan:                                                # output data not shaped properly
            if len(output_data.shape) != 2 or output_data.shape[0] < 2:     # output_data must be 2D for mulitple outputs
                raise ValueError("output_data must contain exactly 1"
                                 " row per output pin")
            num_samples = output_data.shape[1]     
        else:
            if len(output_data.shape) != 1:                                 # output_data must be 1D for one output
                raise ValueError("output_data must contain exactly 1"
                                 " row per output pin")
            num_samples = output_data.shape[0]

        if differential_pair:                                               # if in differential pair mode can only use Ai 0-7
            if max(input_pins) > 7:
                raise ValueError("In differential pair mode, only"
                                 " input pins 0-7 are usable")


        # -------------------- ADDITIONAL SETUP -------------------
        # Generate I/O pin strings
        input_channels = "".join(f"{self.device_name}/ai{pin}," for pin in input_pins)
        input_channels = input_channels[:-1]                                            # remove trailing comma

        output_channels = "".join(f"{self.device_name}/ao{pin}," for pin in output_pins)
        output_channels = output_channels[:-1]                                          # remove trailing comma

        # Define terminal configuration
        if differential_pair:
            terminal_config = nidaqmx.constants.TerminalConfiguration.DIFF
        else:
            terminal_config = nidaqmx.constants.TerminalConfiguration.RSE

        # Define output bounds
        output_bounds = (np.min(output_data), np.max(output_data))
        if np.min(output_data) == np.max(output_data):
            output_bounds = (-10,10)
        else:
            output_bounds = (np.min(output_data), np.max(output_data))


        # --------------- CREATE AND CONFIGURE TASKS --------------
        with nidaqmx.Task() as read_task, nidaqmx.Task() as write_task:
            # Configure input channel (leader clock)
            read_task.ai_channels.add_ai_voltage_chan(input_channels,
                                                    min_val=input_bounds[0], max_val=input_bounds[1],
                                                    terminal_config=terminal_config)

            read_task.timing.cfg_samp_clk_timing(rate=sample_update_rate,
                                                sample_mode=nidaqmx.constants.AcquisitionType.FINITE,           # we know the number of samples to collect
                                                samps_per_chan=num_samples + 1)                                 # we have to add 1 because first AI channel has 1 sample delay 
                                                                                
            
            # Configure output channel (follower clock)
            write_task.ao_channels.add_ao_voltage_chan(output_channels,
                                                    min_val=output_bounds[0], max_val=output_bounds[1])
            write_task.timing.cfg_samp_clk_timing(rate=sample_update_rate,
                                                source=f"/{self.device_name}/ai/SampleClock",                   # sample using the output clock as the leader
                                                sample_mode=nidaqmx.constants.AcquisitionType.FINITE,           # we know the number of samples to collect
                                                samps_per_chan=num_samples)

            write_task.triggers.start_trigger.cfg_dig_edge_start_trig(read_task.triggers.start_trigger.term)    # make sure both tasks start at the same time (rising edge default)


            # ----------------------- RUN TASKS -----------------------
            if is_in_multichan:
                reader = AnalogMultiChannelReader(read_task.in_stream)
            else:
                reader = AnalogSingleChannelReader(read_task.in_stream)

            if is_out_multichan:
                writer = AnalogMultiChannelWriter(write_task.out_stream, auto_start=False)
            else:
                writer = AnalogSingleChannelWriter(write_task.out_stream, auto_start=False)

            # Pre-allocate buffer for reader
            if is_in_multichan:
                input_data = np.zeros((len(input_pins), num_samples + 1))   # +1 for same reason as in read task timing configuration
            else:
                input_data = np.zeros(num_samples + 1)

            # Run tasks, follower first
            writer.write_many_sample(output_data)
            write_task.start()
            reader.read_many_sample(input_data,number_of_samples_per_channel=num_samples + 1,timeout=nidaqmx.constants.WAIT_INFINITELY)   # +1 for same reason as in read task timing configuration

            # Adjust input_data first channel
            if is_in_multichan:
                first_ch_data = input_data[0, 1:]
                last_chs_data = input_data[1:, :-1]
                input_data = np.vstack((first_ch_data,last_chs_data))
            else:
                input_data = input_data[1:]

            return input_data

    
