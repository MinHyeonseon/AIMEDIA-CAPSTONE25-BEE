#!/usr/bin/env python3
import sys, re, json, argparse
import datetime # 시간 관리를 위해 추가
from collections import deque
import numpy as np
import torch
import smtplib                # SMTP 클라이언트
from email.mime.text import MIMEText # 텍스트 메일 본문 생성


# 메일 설정 
NAVER_EMAIL_ADDRESS = "luonj@naver.com" 
NAVER_EMAIL_PASSWORD = "BJUM26N28F7U"    # 네이버 앱 비밀번호 (송신자)
RECIPIENT_EMAIL = None # main 함수에서 args.notify_email로 설정됩니다.

def send_naver_email(subject, body, to_email):
    """Naver SMTP를 사용하여 메일을 전송합니다."""

    if NAVER_EMAIL_PASSWORD == "your_naver_password":
        print("[ERROR] Naver 이메일 주소와 앱 비밀번호를 설정하지 않았습니다. 메일을 건너킵니다.", file=sys.stderr)
        return False

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = NAVER_EMAIL_ADDRESS
    msg['To'] = to_email

    try:
        # SMTP 서버에 연결 (네이버: smpt.naver.com, 포트 465)
        with smtplib.SMTP_SSL('smtp.naver.com', 465) as server:
            # 로그인
            server.login(NAVER_EMAIL_ADDRESS, NAVER_EMAIL_PASSWORD)
            # 메일 전송
            server.sendmail(NAVER_EMAIL_ADDRESS, to_email, msg.as_string())

        print(f"\n[EMAIL SENT] '{subject}' to {to_email}", file=sys.stderr)
        return True

    except smtplib.SMTPAuthenticationError:
        print("\n[EMAIL FAILED] SMTP 인증 실패: ID/비밀번호(앱 비밀번호)를 확인하세요.", file=sys.stderr)
    except Exception as e:
        print(f"\n[EMAIL FAILED] 메일 전송 중 오류 발생: {e}", file=sys.stderr)

    return False

def load_scaler(path):
    d = np.load(path, allow_pickle=True)
    mean = d["mean"].astype(np.float32)                 # (2,)
    std  = d["std"].astype(np.float32)                  # (2,)
    std[std < 1e-8] = 1e-8
    window = int(d["window"])
    feature_order = list(d["feature_order"])
    return mean, std, window, feature_order

def softmax_np(logits: np.ndarray) -> np.ndarray:
    x = logits - logits.max(axis=1, keepdims=True)
    ex = np.exp(x)
    return ex / ex.sum(axis=1, keepdims=True)

def parse_two_floats(line: str):
    # "12.345\t0.678" 또는 "12.345 0.678" 등에서 실수 2개 추출
    nums = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", line)
    if len(nums) < 2:
        return None
    return float(nums[0]), float(nums[1])

# Main
def main():
    ap = argparse.ArgumentParser(description="Real-time HCI jitter classifier")
    # 경로 기본값을 사용자 폴더로 설정
    ap.add_argument("--model",   default="/home/hsmin/deeplearning_model/tst_jitter_ts.pt")
    ap.add_argument("--scaler",  default="/home/hsmin/deeplearning_model/scaler.npz")
    ap.add_argument("--labels",  default="/home/hsmin/deeplearning_model/label_map.json")

    # 입력 모드: ts(Unix epoch 한개/줄) 또는 feat(지터ms, 표준편차ms 두개/줄)
    ap.add_argument("--input-mode", choices=["ts", "feat"], default="ts",
                     help="stdin에서 ts(Unix epoch) 또는 feat(jitter_ms std_ms) 읽기")

    # ts 모드에서만 사용
    ap.add_argument("--expected-interval", type=float, default=0.05,
                     help="기대 간격(초), 예: 0.05 = 50ms (ts 모드)")
    ap.add_argument("--gap-sec", type=float, default=0.5,
                     help="갭 무시 임계값(초) (ts 모드)")

    # 분류 파라미터
    ap.add_argument("--prob-th", type=float, default=0.6,
                     help="attack 확정 확률 임계값")
    ap.add_argument("--vote", type=int, default=5,
                     help="최근 N회 다수결")
    ap.add_argument("--min-consec", type=int, default=3,
                     help="전환 확정에 필요한 연속 횟수")

    # 메일 알림 설정 추가
    ap.add_argument("--notify-email", default=None,
                     help="공격 탐지 시 알림을 받을 이메일 주소 (예: user@example.com)")
    ap.add_argument("--email-interval-min", type=int, default=5,
                     help="공격 지속 중 메일 전송 간격(분)")

    # 로깅
    ap.add_argument("--echo-features", action="store_true",
                     help="특징(jitter_ms, std_ms)도 함께 출력")
    args = ap.parse_args()

    # 전역 메일 수신자 설정
    global RECIPIENT_EMAIL
    RECIPIENT_EMAIL = args.notify_email

    device = torch.device("cpu")
    model = torch.jit.load(args.model, map_location=device).eval()

    mean, std, window, feature_order = load_scaler(args.scaler)
    if feature_order != ["jitter_ms", "std_jitter_ms"]:
        print(f"[warn] feature_order from scaler is {feature_order}, expected ['jitter_ms','std_jitter_ms']",
              file=sys.stderr)

    with open(args.labels) as f:
        label_map = {int(k): v for k, v in json.load(f).items()}

    # 공통 상태
    buf = deque(maxlen=window)           # (L, 2) = [jitter_ms, std_ms]
    pred_hist = deque(maxlen=args.vote)  # 최근 예측 기록
    last_state = None

    # 🚨 메일 전송 상태 추가
    last_email_time = datetime.datetime.min # 마지막 메일 전송 시간 기록
    EMAIL_INTERVAL = datetime.timedelta(minutes=args.email_interval_min) # 메일 전송 최소 간격

    # ts 모드용 상태
    EXPECTED_INTERVAL = args.expected_interval
    GAP_SEC = args.gap_sec
    prev_ts = None
    count = 0
    mean_j = 0.0
    M2_j = 0.0

    print(f"[ready] mode={args.input_mode}, window={window}, "
              f"EI={(EXPECTED_INTERVAL*1000):.1f}ms, GAP={GAP_SEC:.3f}s, "
              f"prob_th={args.prob_th}, vote={args.vote}, min_consec={args.min_consec}", file=sys.stderr)
    #if args.notify_email:
        #print(f"[email] notification to {args.notify_email} every {args.email_interval_min} min while attack.", file=sys.stderr)

    # 연속 카운터(상태 전환 안정화용)
    consec_same = 0
    consec_diff = 0

    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue

        if args.input_mode == "feat":
            # 생산자(지터 계산기)에서 이미 ms 단위로 두 수를 출력
            vals = parse_two_floats(line)
            if vals is None:
                continue
            jitter_ms, std_ms = vals
            buf.append(np.array([jitter_ms, std_ms], dtype=np.float32))

            if args.echo_features:
                print(f"feat\t{jitter_ms:.6f}\t{std_ms:.6f}")

            if len(buf) < window:
                continue

        else:
            # ts 모드: 한 줄에 Unix epoch(초) 한 개
            m = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", line)
            if not m:
                continue
            try:
                ts = float(m.group(0))
            except ValueError:
                continue

            if prev_ts is None:
                prev_ts = ts
                print(f"First packet time: {ts:.6f}s", file=sys.stderr) # 표준 오류로 출력
                continue

            arrival_interval = ts - prev_ts
            if arrival_interval <= 0:
                prev_ts = ts
                continue

            # 갭 무시
            if arrival_interval > GAP_SEC:
                prev_ts = ts
                #print(f"[gap {arrival_interval*1000:.0f} ms] ignored; baseline reset", file=sys.stderr)

                # 수정: 지터 통계 및 버퍼 초기화
                #count = 0
                #mean_j = 0.0
                #M2_j = 0.0
                #buf.clear() # 버퍼 초기화로 새로운 윈도우 채우기를 강제
            
                continue

            # 지터(초)
            j = abs(arrival_interval - EXPECTED_INTERVAL)

            # Welford 업데이트 (지터 표준편차, sample std)
            count += 1
            delta = j - mean_j
            mean_j += delta / count
            delta2 = j - mean_j
            M2_j += delta * delta2
            std_j = (np.sqrt(M2_j / (count - 1)) if count > 1 else 0.0)  # seconds

            # 특징(ms)
            jitter_ms = j * 1000.0
            std_ms = std_j * 1000.0
            buf.append(np.array([jitter_ms, std_ms], dtype=np.float32))

            if args.echo_features:
                print(f"feat\t{jitter_ms:.6f}\t{std_ms:.6f}")

            if len(buf) < window:
                prev_ts = ts
                continue

            prev_ts = ts

        x = np.stack(buf, axis=0).astype(np.float32)    # (L,2)
        x = (x - mean) / std                             # 표준화
        x = np.transpose(x, (1, 0))[None, ...]           # (1,2,L)
        xt = torch.from_numpy(x).to(device)

        with torch.no_grad():
            logits = model(xt)                           # (1,2)
        probs = softmax_np(logits.cpu().numpy())
        p_attack = float(probs[0, 1])
        pred_raw = 1 if p_attack >= args.prob_th else 0

        pred_hist.append(pred_raw)
        maj = 1 if sum(pred_hist) > (len(pred_hist) / 2) else 0

        # 안정화된 상태 전환 로직 (연속 다른 상태 카운트)
        current_time = datetime.datetime.now()

        should_send_email = False

        if last_state is None:
            last_state = maj
            consec_same = 1
            consec_diff = 0
            print(f"INIT -> {label_map[last_state]} (p_attack={p_attack:.2f})", file=sys.stderr) # 표준 오류로 출력
            if last_state == 1 and args.notify_email:
                # 초기 상태가 Attack이면 바로 메일 발송
                should_send_email = True

        else:
            if maj == last_state:
                consec_same = min(consec_same + 1, 10**9)
                consec_diff = 0

                # Attack 상태(1)가 유지될 때 5분 간격 체크
                if last_state == 1 and args.notify_email:
                    if current_time - last_email_time >= EMAIL_INTERVAL:
                        should_send_email = True

            else:
                consec_diff = min(consec_diff + 1, 10**9)
                consec_same = 0
                if consec_diff >= args.min_consec:
                    prev_state = last_state
                    last_state = maj
                    consec_diff = 0
                    print(f"\n[TRANSITION] -> {label_map[last_state]} (p_attack={p_attack:.2f})", file=sys.stderr) # 표준 오류로 출력

                    # Normal(0) -> Attack(1) 전환 시 메일 발송
                    if prev_state == 0 and last_state == 1 and args.notify_email:
                        should_send_email = True

        # 메일 전송 실행 로직
        if should_send_email:
            time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
            subject = f"[ALERT] HCI Jitter Attack Detected! (p={p_attack:.2f})"
            body = (f"공격이 탐지되었습니다.\n\n"
                    f"전환 시간: {time_str}\n"
                    f"공격 확률: {p_attack:.3f}\n"
                    f"최근 특징: Jitter={buf[-1][0]:.3f}ms, StdJitter={buf[-1][1]:.3f}ms\n"
                    f"상태: {label_map[last_state]}")

            if send_naver_email(subject, body, args.notify_email):
                last_email_time = current_time # 성공적으로 보냈을 때만 시간 업데이트

        # 진행 상태 한 줄 출력(덮어쓰기)
        line_out = (f"state={label_map[last_state]}  "
                    f"p_attack={p_attack:.3f}  raw={pred_raw}  maj={maj}  "
                    f"J={buf[-1][0]:.3f}ms  StdJ={buf[-1][1]:.3f}ms")
        print(line_out, end="\r")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
