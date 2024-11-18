import asyncio
import time
import numpy as np
import struct
import speed_utils
from bleak import BleakScanner, BleakClient
from visualization import Visualizer
import threading
import queue

# BLE device and characteristic UUIDs
device_name = "Smart Boxing Gloves"
gx_characteristic = "77777777-7777-7777-7777-a77777777777"
gy_characteristic = "77777777-7777-7777-7777-b77777777777"
gz_characteristic = "77777777-7777-7777-7777-c77777777777"

ax_characteristic = "77777777-7777-7777-7777-d77777777777"
ay_characteristic = "77777777-7777-7777-7777-e77777777777"
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
f_max = 0
punch_cnt = 0

# Maximum number of data points to keep
MAX_DATA_LENGTH = 1000

def bytearray_to_float(byte_data):
    try:
        return struct.unpack('<f', byte_data)[0]
    except Exception as e:
        print(f"Error converting bytearray to float: {e}")
        return None

async def find_device_address(device_name):
    while True:
        print("Scanning for BLE devices...")
        devices = await BleakScanner.discover()
        for device in devices:
            if device.name == device_name:
                return device.address
        await asyncio.sleep(5)

def add_to_array(array, value):
    if value is not None:
        array.append(value)
        if len(array) > MAX_DATA_LENGTH:
            array.pop(0)

async def main(device_name, update_queue):
    global state, v_max, v, f_max, punch_cnt
    # Find device's address
    device_addr = await find_device_address(device_name)
    if device_addr is not None:
        print(f"Found device: {device_name} with address {device_addr}")

    async with BleakClient(device_addr) as client:
        # main loop
        while True:
            start_time = time.perf_counter()
            try:
                # Uncomment and use gyro data if needed
                # gx = bytearray_to_float(await client.read_gatt_char(gx_characteristic))
                # gy = bytearray_to_float(await client.read_gatt_char(gy_characteristic))
                # gz = bytearray_to_float(await client.read_gatt_char(gz_characteristic))

                # Get accelerometer's data for now
                ax = bytearray_to_float(await client.read_gatt_char(ax_characteristic))
                ay = bytearray_to_float(await client.read_gatt_char(ay_characteristic))
                az = bytearray_to_float(await client.read_gatt_char(az_characteristic)) - 1  # remove az shift
                force = bytearray_to_float(await client.read_gatt_char(force_characteristic))
                force = 196.4092 * force * force

            except Exception as e:
                print(f"Error reading characteristics: {e}. Exiting...")
                await client.disconnect()
                break

            end_time = time.perf_counter()
            elapsed_time = end_time - start_time

            ax, ay, az = speed_utils.cleanse_accel(ax, ay, az)

            # Check and switch state:
            state = speed_utils.detect_motion([ax, ay, az], elapsed_time, state)
            # Add data to arrays
            # Uncomment if you decide to use gyro data
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
                print(f"State = {state}, ax={ax}, ay={ay}, az={az}, f={force:.2f}N took {elapsed_time:.6f} seconds")
                continue
            elif state == 'Motion':
                delta_v = speed_utils.update_spd([ax, ay, az], elapsed_time)
                v = v + delta_v
                v_max = max(np.linalg.norm(v), v_max)
                f_max = max(f_max, force)
                print(f"State = {state}, ax={ax}, ay={ay}, az={az}, v_max={v_max:.2f}m/s, f_max={f_max:.2f}N")
                punch_cnt += 1  # Increment punch count on motion detection

            # Update UI via queue
            update_queue.put(('count', punch_cnt))
            update_queue.put(('force', force))
            update_queue.put(('speed', v_max))

            await asyncio.sleep(0.1)  # Adjust the sleep time as needed

def start_asyncio_loop(device_name, update_queue):
    asyncio.run(main(device_name, update_queue))

if __name__ == "__main__":
    try:
        # Create a thread-safe queue for communication
        update_queue = queue.Queue()

        # Initialize the Visualizer (Tkinter runs in the main thread)
        visualizer = Visualizer(update_queue)

        # Start the asyncio event loop in a separate thread
        asyncio_thread = threading.Thread(target=start_asyncio_loop, args=(device_name, update_queue), daemon=True)
        asyncio_thread.start()

        # Start the Tkinter main loop (runs in the main thread)
        visualizer.start()

    except KeyboardInterrupt:
        print("Program stopped.")
