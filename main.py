# main.py
import asyncio
import time
import struct
import numpy as np
import threading
import queue
from bleak import BleakScanner, BleakClient
from visualization import Visualizer
from speed_utils import SpeedUtils

# BLE device and characteristic UUIDs
DEVICE_NAME = "Smart Boxing Gloves"
GX_CHARACTERISTIC = "77777777-7777-7777-7777-a77777777777"
GY_CHARACTERISTIC = "77777777-7777-7777-7777-b77777777777"
GZ_CHARACTERISTIC = "77777777-7777-7777-7777-c77777777777"

AX_CHARACTERISTIC = "77777777-7777-7777-7777-d77777777777"
AY_CHARACTERISTIC = "77777777-7777-7777-7777-e77777777777"
AZ_CHARACTERISTIC = "77777777-7777-7777-7777-f77777777777"

FORCE_CHARACTERISTIC = "77777777-7777-7777-7777-77777777777f"
COM_CHARACTERISTIC = "77777777-7777-7777-7777-777777777777"

MAX_DATA_LENGTH = 1000

class BLEManager:
    def __init__(self, device_name: str):
        self.device_name = device_name
        self.device_address = None
        self.client = None

    async def find_device_address(self) -> str:
        """Scans for BLE devices and returns the address of the target device."""
        while True:
            print("Scanning for BLE devices...")
            devices = await BleakScanner.discover()
            for device in devices:
                if device.name == self.device_name:
                    print(f"Found device: {self.device_name} with address {device.address}")
                    return device.address
            await asyncio.sleep(5)

    async def connect(self):
        """Connects to the BLE device."""
        self.device_address = await self.find_device_address()
        if self.device_address is None:
            raise ConnectionError(f"Device {self.device_name} not found.")
        self.client = BleakClient(self.device_address)
        await self.client.connect()
        if not self.client.is_connected:
            raise ConnectionError(f"Failed to connect to {self.device_name}.")

    async def read_characteristic(self, uuid: str) -> bytes:
        """Reads a characteristic from the BLE device."""
        if self.client and self.client.is_connected:
            return await self.client.read_gatt_char(uuid)
        else:
            raise ConnectionError("BLE client is not connected.")

    async def disconnect(self):
        """Disconnects from the BLE device."""
        if self.client:
            await self.client.disconnect()

class DataProcessor:
    def __init__(self, update_queue: queue.Queue, command_queue: queue.Queue):
        self.update_queue = update_queue
        self.command_queue = command_queue
        self.speed_utils = SpeedUtils()
        self.state = 'Static'
        self.v = np.array([0.0, 0.0, 0.0])
        self.v_max = 0.0
        self.f_max = 0.0
        self.punch_count = 0

        # Data storage
        self.ax_data = []
        self.ay_data = []
        self.az_data = []
        self.force_data = []

    @staticmethod
    def bytearray_to_float(byte_data: bytes) -> float:
        """Converts byte array to float."""
        try:
            return struct.unpack('<f', byte_data)[0]
        except struct.error as e:
            print(f"Error converting bytearray to float: {e}")
            return 0.0

    def add_to_array(self, array: list, value: float):
        """Adds a value to a list and maintains its maximum length."""
        array.append(value)
        if len(array) > MAX_DATA_LENGTH:
            array.pop(0)

    async def process_commands(self):
        """Processes incoming commands from the command queue."""
        try:
            while True:
                try:
                    command, _ = self.command_queue.get_nowait()
                    if command == 'reset':
                        print("Received reset command.")
                        self.reset()
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Error processing commands: {e}")

    def reset(self):
        """Resets internal state and sends reset message to UI."""
        self.punch_count = 0
        self.v = np.array([0.0, 0.0, 0.0])
        self.v_max = 0.0
        self.f_max = 0.0
        self.state = 'Static'

        self.ax_data.clear()
        self.ay_data.clear()
        self.az_data.clear()
        self.force_data.clear()

        # Send reset message to UI
        self.update_queue.put(('reset', None))
        print("Internal state has been reset.")

    async def process_data(self, ble_manager: BLEManager):
        """Main loop to process data from BLE device."""
        try:
            while True:
                await self.process_commands()

                start_time = time.perf_counter()
                try:
                    # Read accelerometer data
                    ax = self.bytearray_to_float(await ble_manager.read_characteristic(AX_CHARACTERISTIC))
                    ay = self.bytearray_to_float(await ble_manager.read_characteristic(AY_CHARACTERISTIC))
                    az = self.bytearray_to_float(await ble_manager.read_characteristic(AZ_CHARACTERISTIC)) - 1.0  # Remove az shift

                    # Read force data and compute force
                    force_raw = self.bytearray_to_float(await ble_manager.read_characteristic(FORCE_CHARACTERISTIC))
                    force = 196.4092 * force_raw ** 2

                except Exception as e:
                    print(f"Error reading characteristics: {e}. Attempting to reconnect...")
                    await ble_manager.disconnect()
                    await ble_manager.connect()
                    continue

                end_time = time.perf_counter()
                elapsed_time = end_time - start_time

                # Cleanse accelerometer data
                ax, ay, az = self.speed_utils.cleanse_accel(ax, ay, az)

                # Detect motion state
                previous_state = self.state
                self.state = self.speed_utils.detect_motion((ax, ay, az), elapsed_time, self.state)

                # Add data to arrays
                self.add_to_array(self.ax_data, ax)
                self.add_to_array(self.ay_data, ay)
                self.add_to_array(self.az_data, az)
                self.add_to_array(self.force_data, force)

                if self.state == 'Static':
                    self.v_max = 0.0
                    self.v = np.array([0.0, 0.0, 0.0])
                    print(f"State = {self.state}, ax={ax:.2f}, ay={ay:.2f}, az={az:.2f}, force={force:.2f}N took {elapsed_time:.6f} seconds")
                elif self.state == 'Motion':
                    delta_v = self.speed_utils.update_speed((ax, ay, az), elapsed_time)
                    self.v += delta_v
                    current_speed = np.linalg.norm(self.v)
                    self.v_max = max(current_speed, self.v_max)
                    self.f_max = max(force, self.f_max)
                    print(f"State = {self.state}, ax={ax:.2f}, ay={ay:.2f}, az={az:.2f}, v_max={self.v_max:.2f} m/s, f_max={self.f_max:.2f}N")

                    # Increment punch count if transitioning to Motion
                    if previous_state == 'Static':
                        self.punch_count += 1

                # Update UI via queue
                self.update_queue.put(('count', self.punch_count))
                self.update_queue.put(('force', force))
                self.update_queue.put(('speed', self.v_max))

                await asyncio.sleep(0.1)  # Adjust the sleep time as needed

        except asyncio.CancelledError:
            print("Data processing task was cancelled.")

def start_asyncio_loop(loop):
    """Starts the asyncio event loop."""
    asyncio.set_event_loop(loop)
    loop.run_forever()

async def run_ble_operations(update_queue: queue.Queue, command_queue: queue.Queue):
    # Initialize BLE Manager and Data Processor
    ble_manager = BLEManager(DEVICE_NAME)
    data_processor = DataProcessor(update_queue, command_queue)

    # Connect to BLE device
    try:
        await ble_manager.connect()
    except ConnectionError as e:
        print(e)
        return

    # Start processing data
    try:
        await data_processor.process_data(ble_manager)
    except Exception as e:
        print(f"An error occurred during data processing: {e}")
    finally:
        await ble_manager.disconnect()

def main():
    # Create thread-safe queues for communication
    update_queue = queue.Queue()
    command_queue = queue.Queue()

    # Initialize the Visualizer (Tkinter runs in the main thread)
    visualizer = Visualizer(update_queue, command_queue)

    # Create a new asyncio event loop
    loop = asyncio.new_event_loop()

    # Start the asyncio loop in a separate thread
    asyncio_thread = threading.Thread(target=start_asyncio_loop, args=(loop,), daemon=True)
    asyncio_thread.start()

    # Schedule the BLE operations coroutine
    asyncio.run_coroutine_threadsafe(run_ble_operations(update_queue, command_queue), loop)

    # Start the Tkinter main loop (runs in the main thread)
    try:
        visualizer.start()
    except KeyboardInterrupt:
        print("Program interrupted by user.")
    finally:
        # Stop the asyncio loop
        loop.call_soon_threadsafe(loop.stop)
        asyncio_thread.join()

if __name__ == "__main__":
    main()
