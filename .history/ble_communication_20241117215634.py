import asyncio
import time
import numpy as np
import struct
import speed_utils
from bleak import BleakScanner, BleakClient

# BLE device and characteristic UUIDs
DEVICE_NAME = "Smart Boxing Gloves"
GX_CHARACTERISTIC = "77777777-7777-7777-7777-a77777777777"
GY_CHARACTERISTIC = "77777777-7777-7777-7777-b77777777777"
GZ_CHARACTERISTIC = "77777777-7777-7777-7777-c77777777777"

AX_CHARACTERISTIC = "77777777-7777-7777-7777-d77777777777"
AY_CHARACTERISTIC = "77777777-7777-7777-7777-e77777777777"
az_characteristic = "77777777-7777-7777-7777-f77777777777"

force_characteristic = "77777777-7777-7777-7777-77777777777f"
com_characteristic = "77777777-7777-7777-7777-777777777777"

# Arrays to store IMU data
gx_data, gy_data, gz_data = [], [], []
ax_data, ay_data, az_data = [], [], []
force_data = []
state = 'Static'

v = np.array([0, 0, 0])
v_max = 0

# Maximum number of data points to keep
MAX_DATA_LENGTH = 1000

def bytearray_to_float(byte_data):
    try:
        return struct.unpack('<f', byte_data)[0]
    except Exception as e:
        print(f"Error converting bytearray to float: {e}")
        return None

async def find_device_address(ns):
    while True:
        print("Scanning for BLE devices...")
        devices = await BleakScanner.discover()
        for device in devices:
            if device.name == DEVICE_NAME:
                return device.address
        time.sleep(5)

def add_to_array(array, value):
    if value is not None:
        array.append(value)
        if len(array) > MAX_DATA_LENGTH:
            array.pop(0)

async def main(DEVICE_NAME):
    global state, v_max, v
    # Find device's address
    device_addr = await find_device_address(DEVICE_NAME)
    if device_addr is not None:
        print(f"Found device: {DEVICE_NAME} with address {device_addr}")

    async with BleakClient(device_addr) as client:
        # main loop
        while True:
            
            start_time = time.perf_counter()
            try:
                # Update data collected
                # gx = bytearray_to_float(await client.read_gatt_char(GX_CHARACTERISTIC))
                # gy = bytearray_to_float(await client.read_gatt_char(GY_CHARACTERISTIC))
                # gz = bytearray_to_float(await client.read_gatt_char(GZ_CHARACTERISTIC))

                # Get accelerometer's data for now
                ax = bytearray_to_float(await client.read_gatt_char(AX_CHARACTERISTIC))
                ay = bytearray_to_float(await client.read_gatt_char(AY_CHARACTERISTIC))
                az = bytearray_to_float(await client.read_gatt_char(az_characteristic)) - 1     # remove az shift
                force = bytearray_to_float(await client.read_gatt_char(force_characteristic))
                
            except Exception as e:
                print(f"Error reading characteristics. Exitting...")
                client.disconnect()
                break
                
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
                
            ax, ay, az = speed_utils.cleanse_accel(ax, ay, az)
            
            # Check and switch state:
            state = speed_utils.detect_motion([ax, ay, az], elapsed_time, state)
            # Add data to arrays
            # add_to_array(gx_data, gx)
            # add_to_array(gy_data, gy)
            # add_to_array(gz_data, gz)

            add_to_array(ax_data, ax)
            add_to_array(ay_data, ay)
            add_to_array(az_data, az)
            add_to_array(force_data, force)
            
            if state == 'Static':
                v_max = 0
                v = np.array([0, 0, 0])
                print(f"State = {state}, ax={ax}, ay={ay}, az={az}, took {elapsed_time:.6f} seconds")
                continue
            elif state == 'Motion':
                delta_v = speed_utils.update_spd([ax, ay, az], elapsed_time)
                v = v + delta_v
                v_max = max(np.linalg.norm(v), v_max)
                print(f"State = {state}, ax={ax}, ay={ay}, az={az}, v = {v}, v_max = {v_max}")

if __name__ == "__main__":
    try:
        asyncio.run(main(DEVICE_NAME))
    except KeyboardInterrupt:
        print("Program stopped.")
