# 국립한밭대학교 지능미디어공학과 BEE팀

**팀 구성**
- 20221095 민현선 
- 20221110 이다은

## <u>Teamate</u> Project Background
- ### 기존 해결책의 문제점
  - 웨어러블 기기는 보통ﾠ편의성과 호환성 위주로 개발되며 보안 업데이트나 암호화 프로토콜 적용이 부족한 경우가 많아ﾠ공격자가 쉽게 통신을 가로채거나 변조 가능
  - 공격자가 수트의 진동을 임의로 제어하면 착용자에게 불쾌감, 통증, 피부 자극, 근육 긴장, 장비 손상 등ﾠ신체적 위험 초래 가능
- ### 필요성 
  - AR과 연동되는 수트는 전용 앱으로만 제어되어야 하지만 통신이 조작되면 공격자가 진동을 임의로 제어할 수 있어 제어 권한 탈취와 개인정보 유출 위험 발생
  - 출시된 지 오래되지 않은 AR/VR연동 웨어러블 수트는 기능 중심 개발로 인해 보안 검증이 미흡해 블루투스 취약점 등 보안 우려가 존재하여 해결 방안 필요
  
## System Design
- ### System Requirements
  + ### 공통 실험 환경 구축
    <img width="516" height="252" alt="image" src="https://github.com/user-attachments/assets/6f83e3a5-d1bb-438d-b3a3-b5c1f973edcd" />    

    + 칼리 리눅스 기반 공격 환경 세팅    
    + BLE 지원 동글을 장착한 컴퓨터 A(피해자), 컴퓨터 B(공격자) 구성    
    + BLE 기반 조명 장치 및 AR 수트(진동센서 장착) 연결    
    + Bluepy, BtleJuice 등 오픈소스 툴을 활용한 통신 분석 및 공격 시나리오 설계    

  + ### 실험 1: BLE 조명 장치 공격
    <img width="409" height="230" alt="image" src="https://github.com/user-attachments/assets/67cd45d0-8f7d-493a-8ac9-ca3f80eda263" />    

    1) 특정 BLE 장치(KocoaFab_BLE)를 스캔하여 UUID 기반 Write Characteristic을 식별    
    2) 값 "2\n" 전송 시 조명의 색상 제어 가능함을 확인    
    3) bleak를 통해 A-PC가 조명과 연결 유지, 연결이 끊기면 B-PC가 즉시 재연결되는 무결성 취약점 실험 수행    

  + ### 실험 2: AR 수트 진동 센서 공격
    <img width="409" height="230" alt="image" src="https://github.com/user-attachments/assets/75c2afff-5150-4e20-b9fa-af7fa3925012" />

    1) 실험 1에서 세팅한 환경을 BLE 조명이 아닌 촉각 수트에 적용하여 실험
    2) 공격자가 PC 동글을 통해 수트와 모바일 앱 사이의 Bluetooth 통신을 가로채는 환경 구성
    3) Bluepy를 활용하여 수트의 GATT Characteristic(UUID)에 임의 바이트 payload를 Write → 수트가 이를 진동 세기로 해석하여 동작
    4) 자동 연결 해제 및 재주입(inject) 코드를 통해 지속적으로 통신 세션을 제어
    5) 개별 센서 제어 및 세기 조절 가능성을 검증
   
  + ### 보안 솔루션 제안
    
    + 와이어샤크 등의 패킷 분석 도구를 활용하여 공격 패킷 및 이상 징후를 수집하여 수집된 무선 프로토콜 트래픽을 기반으로 AI 모델 학습을 활용한 실시간 공격 탐지 솔루션 제안
    + 기존 패턴 기반 탐지보다 강화된 AI 기반 무선 프로토콜 보안 프레임워크 제안

    
## Case Study
- ### 블루투스 프로토콜의 보안 취약점에 대한 연구 동향(한국통신학회 학술 대회 논문 발표)
  + **BtleJuice**: BtleJuice는 BLE 프로토콜의 구조적 취약점을 동시에 악용하는 능동형 중간자(MITM) 공격 기법이다. 일반적으로 BLE 장치는 한 번에 하나의 연결만 가능하지만, BtleJuice는 이를 우회하여 피해자의 앱과 기기 사이에 ‘가짜 앱’과 ‘가짜 장치’를 각각 만들어 세션을 중계한다. 이 과정에서 공격자는 SMP 계층의 키 교환 취약점(Temporary Key를 0으로 설정하는 Just Works 페어링 방식)을 이용해 암호화되지 않은 키 교환을 가로채고, GATT 계층의 인증 부재를 이용해 Write·Notify 요청을 변조하거나 재전송 하여 기기의 정상 동작을 교란할 수 있다.
    
  + **GATTacker**: GATTacker는 BLE 프로토콜의 핵심 계층인 GATT(Generic Attribute Profile) 구조를 악용하는 공격이다. 공격자는 먼저 정상 BLE 장치를 흉내 낸 가짜 BLE 장치를 만들어 피해자의 앱이 이를 진짜 장치로 오인하도록 유도한다. 이후 실제 장치에서 제공하는 GATT 서비스와 특성을 복제하고, 피해자의 앱이 해당 가짜 장치와 통신하도록 연결을 가로챈다. 이를 통해 공격자는 읽기, 쓰기, 알림 이벤트를 변조하거나 중간에서 가로채어 사용자 정보의 기밀성과 무결성을 침해할 수 있다.
    
  + **InjectaBLE**: InjectaBLE은 기존 공격 기법과 달리 이미 연결이 완료된 BLE 세션에서도 공격을 수행할 수 있는 점이 특징이다. 이 공격은 링크 계층의 윈도우 확장(Window Widening) 메커니즘을 악용하여 프레임 전송 타이밍에서 경쟁 조건(Race Condition)을 만들어내고 이 틈을 이용해 악성 패킷을 주입한다. 공격자는 ATT 요청(읽기·쓰기), LL 제어 프레임, CONNECTION UPDATE PDU 등 다양한 메시지를 삽입할 수 있으며, 이를 통해 기기의 특정 기능을 강제로 실행(Trigger)하거나 Master/Slave 역할을 탈취할 수 있다. 또한 기존 연결을 끊지 않고도 공격이 가능하기 때문에 사용자가 눈치채지 못한 상태에서 지속적인 MITM 공격이 가능하다. 이로 인해 BLE 보안 위협 범위가 기존 연결 이전 단계에서 연결 이후 단계로까지 확장되었다는 점에서 중요한 의미가 있다.


  + BLE 공격 기법 비교표
    | 항목 | BtleJuice | GATTacker | InjectaBLE |
    |---|---|---|---|
    | **장치/환경** | Bluetooth USB 동글 2개<br>(가짜 앱 / 가짜 장치)<br>Kali Linux | Bluetooth USB 동글 2개<br>(실제 장치 / 피해자 앱)<br>Linux | Bluetooth 스니퍼<br>타이밍 제어 가능 장비<br>(동글 1개도 가능) |
    | **공격 목적** | - BLE write 무결성 침해<br>- 사용자 기기 제어<br>- GATT 특성 변조 | - BLE 세션 가로채기<br>- 정보 유출<br>- 기능 오용 | - 연결된 BLE 장치 제어<br>- 기능 트리거<br>- 역할 탈취<br>- 민감 정보 탈취 |
    | **공격 계층** | - Link Layer<br>- SMP<br>- GATT | - GATT | - Link Layer<br>- ATT |
    | **침해 정도** | 중간자 위치 및<br>전방위 조작 가능 | 가짜 장치로 연결 유도 및<br>데이터 조작 | 중대한 기능 탈취 및<br>역할 조작 가능 |
  
  
## Conclusion
  - 실험 1: BLE 조명 장치 공격 결과
    ![Part2-1 BLE 조명 공격 환경](https://github.com/user-attachments/assets/867de032-aa4a-4bae-80e7-f781d79ac387)
    BLE 조명 공격 환경
    
    <img width="2479" height="2475" alt="Part2-2 BLE 조명 해킹" src="https://github.com/user-attachments/assets/006d9070-3a5a-42f9-8bc9-d1d089cf491b" />
    BLE 조명 해킹 결과

    + 특정 UUID를 통한 Write 접근이 인증 및 무결성 검증 없이 허용됨을 확인
    + 공격자가 조명 제어(색상 변경)를 성공적으로 수행 → BLE Write 취약점 검증 완료
    + BtleJuice 중계 시 GATT 요청 변조가 가능, 공격자가 사용자의 정상 명령어를 수정하여 조명 동작을 제어함
    + **BLE Write 무결성 취약점 존재, 기기 인증 체계 부재로 공격자 개입이 용이함**

  - 실험 2: AR 수트 진동 센서 공격 결과
    ![Part3-1 BLE 웨어러블기기 공격 환경](https://github.com/user-attachments/assets/7b836873-61c4-46bf-8f86-f00043bdeaab)
    BLE 웨어러블기기 공격 환경

    <img width="2575" height="1750" alt="Part3-2 BLE 웨어러블 기기 해킹" src="https://github.com/user-attachments/assets/844d5a6a-4079-4714-a7d2-84a5f4729528" />
    BLE 웨어러블 기기 해킹 결과


    + UUID에 직접 바이트 payload를 Write하여 센서 진동 제어 성공
    + 개별 센서별 진동 강도 조절 가능
    + 앱–수트 간 세션이 공격자에 의해 강제 끊기고 재주입될 수 있음 → 통신 무결성 취약
    + **AR 웨어러블 기기 역시 Bluetooth 통신 취약점을 통해 악용 가능하며, 공격자는 진동 기능을 임의로 제어 가능**

  - 실험 3: 실시간 지터 공격 탐지 결과
    <img width="1512" height="982" alt="Part3-3 Advertising Report" src="https://github.com/user-attachments/assets/93909eff-d269-45df-a1c4-e788e5075967" />
    Advertising Report 캡처 화면

    <img width="2071" height="2062" alt="Part4-1" src="https://github.com/user-attachments/assets/2e687125-c9f3-44cf-aadd-99a71d2059ed" />
    상황별 지터 비교 그래프

    <img width="2809" height="1310" alt="결과1 솔루션 실행 화면" src="https://github.com/user-attachments/assets/ab89ec99-81be-484b-97ea-e7e62954991c" />
    솔루션 실행 화면


    <img width="976" height="607" alt="결과2 공격 탐지시 메일 전송" src="https://github.com/user-attachments/assets/63fe9629-2867-4808-891a-57c56c96063e" />
    공격 탐지 시 메일 전송

    + BLE 공격 상황시 발생하는 advertising packet을 활용해 추출한 상황별 jitter dataset을 Transformer로 학습
    + 하나의 스크립트로 작성하여 효율적인 **실시간 공격 탐지 확인**
    + 공격 탐지 시 메일로 **알림 전송 기능** 구현
      
  - BLE/Bluetooth 기반 AR 기기는 무결성·인증 취약점으로 인해 공격자가 기기 동작을 직접 조작할 수 있음
  - 기존 보안 방식은 재연결 시나리오, 중계 공격, 무결성 검증 부재 상황을 막기 어려움
  - AI 기반 실시간 이상행위 탐지 및 패킷 학습을 통한 보안 강화 솔루션의 필요성 확인
  - 실시간 공격 탐지를 통해 외부의 악의적 간섭을 차단하고, 의도치 않은 촉각 피드백 및 오작동을 방지하여 기기 사용의 안전성과 신뢰도 확보
  - 사전 인지된 공격 정보를 사운드 알림 등과 연계 시, 사용자 즉각 경고를 통한 효율적 예방 가능
  - 기존 보안 시스템과의 통합 가능해 더욱 효과적인 다층적 보안 체계 구축 가능
  - 추가 센서 및 고가 장비 없이 소프트웨어로만 구현 가능해 총소유비용(TCO) 절감 가능


    
  
## Project Outcome
- ### 2025년도 한국통신학회 하계학술대회 논문 발표
  - 민현선, 이다은, 박경민, 김태훈, 방인규, "블루투스 프로토콜의 보안 취약점에 대한 연구 동향," 한국통신학회 하계학술대회 논문집, 2025.

