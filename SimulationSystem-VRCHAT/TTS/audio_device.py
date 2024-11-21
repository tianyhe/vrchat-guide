import sounddevice as sd
import pyaudio
from dataclasses import dataclass

@dataclass
class AudioDeviceInfo:
    name: str
    id: int
    max_input_channels: int
    max_output_channels: int
    default_samplerate: int


@dataclass
class VBCableDevicesInfo:
    cable_c_input: AudioDeviceInfo
    cable_c_output: AudioDeviceInfo
    cable_d_input: AudioDeviceInfo
    cable_d_output: AudioDeviceInfo
    stereo_mix: AudioDeviceInfo

def main():
    # Query and print all available devices
    print(sd.query_devices())
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if (dev['name'] == 'Stereo Mix (Realtek(R) Audio)' and dev['hostApi'] == 0):
            dev_index = dev['index'];
            print('dev_index', dev_index)

def get_vbcable_devices_info():
    devices_info = VBCableDevicesInfo(None, None, None, None, None)
    for dev in sd.query_devices():
        if 'CABLE-C' in dev['name'] and 'Input' in dev['name'] and dev['hostapi'] == 0:
            devices_info.cable_c_input = AudioDeviceInfo(dev['name'], dev['index'], dev['max_input_channels'], dev['max_output_channels'], dev['default_samplerate'])
        elif 'CABLE-C' in dev['name'] and 'Output' in dev['name'] and dev['hostapi'] == 0:
            devices_info.cable_c_output = AudioDeviceInfo(dev['name'], dev['index'], dev['max_input_channels'], dev['max_output_channels'], dev['default_samplerate'])
        elif 'CABLE-D' in dev['name'] and 'Input' in dev['name'] and dev['hostapi'] == 0:
            devices_info.cable_d_input = AudioDeviceInfo(dev['name'], dev['index'], dev['max_input_channels'], dev['max_output_channels'], dev['default_samplerate'])
        elif 'CABLE-D' in dev['name'] and 'Output' in dev['name'] and dev['hostapi'] == 0:
            devices_info.cable_d_output = AudioDeviceInfo(dev['name'], dev['index'], dev['max_input_channels'], dev['max_output_channels'], dev['default_samplerate'])
        elif 'Stereo Mix' in dev['name'] and dev['hostapi'] == 0:
            devices_info.stereo_mix = AudioDeviceInfo(dev['name'], dev['index'], dev['max_input_channels'], dev['max_output_channels'], dev['default_samplerate'])
    assert devices_info.cable_d_input is not None, "CABLE-D Input device not found"
    assert devices_info.cable_d_output is not None, "CABLE-D Output device not found"
    assert devices_info.stereo_mix is not None, "Stereo Mix device not found"
    assert devices_info.cable_c_input is not None, "CABLE-C Input device not found"
    assert devices_info.cable_c_output is not None, "CABLE-C Output device not found"
    return devices_info

def get_info_from_id(id):
    for dev in sd.query_devices():
        if dev['index'] == id:
            dev_info = AudioDeviceInfo(dev['name'], dev['index'], dev['max_input_channels'], dev['max_output_channels'], dev['default_samplerate'])
            return dev_info
    return None

if __name__ == "__main__":
    main()
    print("VBCable devices info: ", get_vbcable_devices_info())

