import asyncio
import time
import struct
from bleak import BleakScanner, BleakClient

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

gx = gy = gz = ax = ay = az = force = 0.0
interval = 0

def bytearray_to_float(byte_data):
    try:
        return struct.unpack('<f', byte_data)[0]
    except Exception as e:
        print(f"Error converting bytearray to float: {e}")
        return None

async def find_device_address(device_name):
    while (True):
        print("Scanning for BLE devices...")
        devices = await BleakScanner.discover()
        for device in devices:
            if device.name == device_name:
                return device.address
        time.sleep(5)

async def main(device_name):
    # Find device's address
    device_addr = await find_device_address(device_name)
    if device_addr is not None:
        print(f"Found device: {device_name} with address {device_addr}")

    async with BleakClient(device_addr) as client:
        while True:
            # Update data collected
            gx = bytearray_to_float(await client.read_gatt_char(gx_characteristic))
            gy = bytearray_to_float(await client.read_gatt_char(gy_characteristic))
            gz = bytearray_to_float(await client.read_gatt_char(gz_characteristic))

            ax = bytearray_to_float(await client.read_gatt_char(ax_characteristic))
            ay = bytearray_to_float(await client.read_gatt_char(ay_characteristic))
            az = bytearray_to_float(await client.read_gatt_char(az_characteristic))

            force = bytearray_to_float(await client.read_gatt_char(force_characteristic))

            print(f"gx={gx}, gy={gy}, gz={gz}, ax={ax}, ay={ay}, az={az}, F={force}")

        

if __name__ == "__main__":
    try:
        asyncio.run(main(device_name))
    except KeyboardInterrupt:
        print("Program stopped.")