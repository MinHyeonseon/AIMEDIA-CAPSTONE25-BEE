#!/usr/bin/env python3

import asyncio
from bleak import BleakClient

ADDRESS = "D4:D8:F3:B7:68:90"
WRITE_CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

COMMAND = "3"

async def main():
    print(f"Attempting to connect to {ADDRESS}...")
    client = BleakClient(ADDRESS)

    try:
        await client.connect()

        if client.is_connected:
            print("Connected to device.")

            # 명령어 전송
            data = (COMMAND + "\n").encode()
            await client.write_gatt_char(WRITE_CHAR_UUID, data, response=False)
            print(f"Sent command: {COMMAND}")
            

            # 연결 유지를 위한 루프
            print("\nConnection maintained. Press Ctrl+C to disconnect and exit.")
            while client.is_connected:
                # 1초마다 연결 상태를 체크하며 대기
                await asyncio.sleep(1)

            print("Device disconnected unexpectedly.")

    except asyncio.CancelledError:
        # Ctrl+C로 프로그램을 종료할 때 발생
        print("\nProgram cancelled by user.")
    except Exception as e:
        print("An error occurred:")
        print(e)

    finally:
        # 프로그램이 어떤 이유로든 종료될 때 항상 실행
        if client.is_connected:
            print("Disconnecting...")
            await client.disconnect()
            print("Disconnected.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Ctrl+C 입력을 처리하기 위함
        pass
