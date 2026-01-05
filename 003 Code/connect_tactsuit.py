#send_tactsuit.py
#!/usr/bin/env python3

from bluepy.btle import Scanner, DefaultDelegate, Peripheral, BTLEException
import time

TARGET_NAME = "TactSuitAirAsh"
CHARACTERISTIC_UUID = "12345-12345-12345-12345"
VIBRATION_COMMAND = "TACT,1,50,500\n".encode("utf-8")

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        super().__init__()

def main():
    print("Scanning for devices...")

    scanner = Scanner().withDelegate(ScanDelegate())
    try:
        devices = scanner.scan(10.0)
    except BTLEException as e:
        print("Scan failed: root permission may be required")
        print(f"Error: {e}")
        return

    target_addr = None

    for dev in devices:
        for (adtype, desc, value) in dev.getScanData():
            if desc == "Complete Local Name" and value == TARGET_NAME:
                print(f"Found device: {value} ({dev.addr})")
                target_addr = dev.addr
                break
        if target_addr:
            break

    if not target_addr:
        print(f"BLE device with name '{TARGET_NAME}' was not found.")
        return

    try:
        peripheral = Peripheral(target_addr, addrType="random")
        print("Connected to device.")

        chars = peripheral.getCharacteristics(uuid=CHARACTERISTIC_UUID)
        if not chars:
            print("Characteristic with the specified UUID was not found.")
            return

        char = chars[0]
        char.write(VIBRATION_COMMAND, withResponse=False)
        print("Vibration command sent successfully.")

        # 연결 유지 및 끊김 감지 루프
        print("Keeping connection alive. Press Ctrl+C to exit.")
        while True:
            try:
                # Force periodic reads to detect disconnections (difficult to detect without read/write/notify)
                _ = char.read()  # If it is not a readable characteristic, replace it with a notify subscription or write
                time.sleep(2)
            except BTLEException:
                print("Connection lost with device.")
                break

    except BTLEException as e:
        print(f"BLE communication error: {e}")

if __name__ == "__main__":
    main()
