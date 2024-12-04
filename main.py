import asyncio
import struct
import threading
import queue
from bleak import BleakScanner, BleakClient
from visualization import Visualizer

# BLE device and characteristic UUIDs
DEVICE_NAME = "Smart Boxing Gloves"
IMU_SERVICE_UUID = "119"
SPEED_CHARACTERISTIC_UUID = "77777777-7777-7777-7777-a77777777777"
FORCE_CHARACTERISTIC_UUID = "77777777-7777-7777-7777-b77777777777"

class BLEManager:
    def __init__(self, device_name: str, update_queue: queue.Queue):
        self.device_name = device_name
        self.device_address = None
        self.client = None
        # Store the update_queue for use in callbacks
        self.update_queue = update_queue

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
        self.device_address = await self.find_device_address()
        if self.device_address is None:
            raise ConnectionError(f"Device {self.device_name} not found.")
        self.client = BleakClient(self.device_address)
        await self.client.connect()
        if not self.client.is_connected:
            raise ConnectionError(f"Failed to connect to {self.device_name}.")
        print(f"Connected to {self.device_name}.")

        # Register callbacks for notifications
        self.client.set_disconnected_callback(self.on_disconnected)

        await self.client.start_notify(SPEED_CHARACTERISTIC_UUID, self.on_speed_notify)
        await self.client.start_notify(FORCE_CHARACTERISTIC_UUID, self.on_force_notify)
        print("Started notifications for speed and force.")

    def on_disconnected(self, client):
        print(f"Device {self.device_name} disconnected.")

    def on_speed_notify(self, sender, data):
        """Synchronous callback for speed notifications."""
        try:
            # float32 ?
            max_speed = struct.unpack('<f', data)[0]
            print(f"Speed Notification: {max_speed} m/s")
            self.update_queue.put(('previous_max_speed', max_speed))
        except struct.error as e:
            print(f"Error unpacking speed data: {e}")

    def on_force_notify(self, sender, data):
        """Synchronous callback for force notifications."""
        try:
            max_force = struct.unpack('<f', data)[0]
            print(f"Force Notification: {max_force} N")
            self.update_queue.put(('previous_max_force', max_force))
        except struct.error as e:
            print(f"Error unpacking force data: {e}")

    async def disconnect(self):
        """Disconnects from the BLE device."""
        if self.client:
            await self.client.disconnect()
            print(f"Disconnected from {self.device_name}.")

class DataProcessor:
    def __init__(self, update_queue: queue.Queue, command_queue: queue.Queue):
        self.update_queue = update_queue
        self.command_queue = command_queue
        self.punch_count = 0
        self.previous_max_speed = 0.0
        self.previous_max_force = 0.0
        self.historical_max_speed = 0.0
        self.historical_max_force = 0.0

    async def process_commands(self):
        """Processes incoming commands from the command queue."""
        try:
            while True:
                command, _ = self.command_queue.get_nowait()
                if command == 'reset':
                    print("Received reset command.")
                    self.reset()
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Error processing commands: {e}")

    def reset(self):
        """Resets internal state and sends reset message to UI."""
        self.punch_count = 0
        self.previous_max_speed = 0.0
        self.previous_max_force = 0.0
        self.historical_max_speed = 0.0
        self.historical_max_force = 0.0

        # Send reset message to UI
        self.update_queue.put(('reset', None))
        print("Internal state has been reset.")

    async def process_data(self):
        """Main loop to process data from update_queue."""
        try:
            while True:
                await self.process_commands()

                try:
                    # Non-blocking get from the queue
                    data = self.update_queue.get_nowait()
                    key, value = data

                    if key == 'previous_max_speed':
                        self.previous_max_speed = value
                        if self.previous_max_speed > self.historical_max_speed:
                            self.historical_max_speed = self.previous_max_speed
                        self.update_queue.put(('previous_max_speed', self.previous_max_speed))
                        self.update_queue.put(('historical_max_speed', self.historical_max_speed))
                        # self.punch_count += 1
                        # self.update_queue.put(('count', self.punch_count))

                    elif key == 'previous_max_force':
                        self.previous_max_force = value
                        if self.previous_max_force > self.historical_max_force:
                            self.historical_max_force = self.previous_max_force
                        self.update_queue.put(('previous_max_force', self.previous_max_force))
                        self.update_queue.put(('historical_max_force', self.historical_max_force))

                except queue.Empty:
                    pass
                except Exception as e:
                    print(f"Error processing data: {e}")

                await asyncio.sleep(0.05)  # Adjust sleep time as needed
        except asyncio.CancelledError:
            print("Data processing task was cancelled.")

def start_asyncio_loop(loop):
    """Starts the asyncio event loop."""
    asyncio.set_event_loop(loop)
    loop.run_forever()

async def run_ble_operations(update_queue: queue.Queue, command_queue: queue.Queue):
    """Initializes BLEManager and DataProcessor, connects to BLE device, and starts processing data."""
    # Initialize BLE Manager and Data Processor
    ble_manager = BLEManager(DEVICE_NAME, update_queue)
    data_processor = DataProcessor(update_queue, command_queue)

    # Connect to BLE device
    try:
        await ble_manager.connect()
    except ConnectionError as e:
        print(e)
        return

    # Start processing data
    data_task = asyncio.create_task(data_processor.process_data())

    try:
        await data_task
    except asyncio.CancelledError:
        print("BLE operations task was cancelled.")
    except Exception as e:
        print(f"An error occurred during BLE operations: {e}")
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
    ble_operations_future = asyncio.run_coroutine_threadsafe(
        run_ble_operations(update_queue, command_queue), loop
    )

    # Start the Tkinter main loop
    try:
        visualizer.start()
    except KeyboardInterrupt:
        print("Program interrupted by user.")
    finally:
        # Cancel the BLE operations task
        ble_operations_future.cancel()

        # Stop the asyncio loop
        loop.call_soon_threadsafe(loop.stop)
        asyncio_thread.join()

if __name__ == "__main__":
    main()
