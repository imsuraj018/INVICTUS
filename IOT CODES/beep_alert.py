import serial
import os
import time
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

def set_max_volume():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volume.SetMasterVolumeLevelScalar(1.0, None)

ser = serial.Serial('COM5', 115200, timeout=3)

set_max_volume()

while True:
    time.sleep(2.1)
    while ser.in_waiting:
        raw_data = ser.readline().strip()
        if not raw_data:
            continue
        
        print(f"Raw Data: {raw_data}")

        try:
            line = raw_data.decode('utf-8', errors='ignore').strip()
            print(f"Decoded Data: {line}")

            if "ALERT: Object Detected" in line:
                os.system('echo \a')
                print("🚨 Beep Alert Triggered! 🚨")

        except Exception as e:
            print(f"Decoding Error: {e}")
