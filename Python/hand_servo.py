import math
from collections import deque
import cv2
import mediapipe as mp
import serial
import time
import argparse

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# ---------------- Settings ----------------
TRAIL_LEN = 5          # frames to compare for movement (shown on screen only)
MOVE_THRESHOLD = 15    # pixels; below this the hand counts as "not moving"
CAMERA_INDEX = 0
SMOOTHING = 0.3   # 0 to 1; lower = smoother but slower

# Angle convention (measured clockwise, starting from the left horizontal):
#   Left = 0, Up = 90, Right = 180, Down = 270
LABELS = ["Left", "Up-Left", "Up", "Up-Right",
          "Right", "Down-Right", "Down", "Down-Left"]


def clockwise_angle(dx, dy):
    """Angle of (dx, dy) in image coords, clockwise from the left horizontal."""
    theta = math.degrees(math.atan2(-dy, dx))  # 0 = right, counter-clockwise
    return (180 - theta) % 360


def label(angle):
    return LABELS[int((angle + 22.5) % 360 // 45)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM8")
    args = parser.parse_args()

    try:
        arduino = serial.Serial(args.port, 9600, timeout=1)
    except serial.SerialException as e:
        raise SystemExit(f"Could not open {args.port}: {e}")
    time.sleep(2)
    cap = cv2.VideoCapture(CAMERA_INDEX)
    trail = deque(maxlen=TRAIL_LEN)
    last_text = None  # last hand-angle text printed to the terminal
    smoothed, last_sent = None, None

    with mp_hands.Hands(max_num_hands=1,
                        min_detection_confidence=0.6,
                        min_tracking_confidence=0.6) as hands:
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            result = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            if result.multi_hand_landmarks:
                hand = result.multi_hand_landmarks[0]
                lm = hand.landmark
                mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

                wrist = (lm[0].x * w, lm[0].y * h)
                mcp = (lm[9].x * w, lm[9].y * h)  # base of middle finger

                # Hand orientation (wrist -> middle finger base)
                orient = clockwise_angle(mcp[0] - wrist[0], mcp[1] - wrist[1])

                # Draw the hand axis and the horizontal reference line
                cv2.line(frame, (int(wrist[0]), int(wrist[1])),
                         (int(mcp[0]), int(mcp[1])), (0, 255, 0), 3)
                cv2.line(frame, (int(wrist[0]) - 80, int(wrist[1])),
                         (int(wrist[0]) + 80, int(wrist[1])), (255, 255, 255), 1)

                # Text shown on screen AND printed in the terminal
                text = f"Hand angle: {orient:.0f} deg ({label(orient)})"
                target = max(0, min(180, orient))
                smoothed = target if smoothed is None else smoothed + SMOOTHING * (target - smoothed)
                angle = int(round(smoothed))
                if angle != last_sent:
                    arduino.write(bytes([angle]))
                    last_sent = angle
                cv2.putText(frame, text, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                if text != last_text:   # print only when the value changes
                    print(text)
                    last_text = text

                # Movement direction (on screen only, not printed)
                trail.append(wrist)
                if len(trail) == trail.maxlen:
                    dx = trail[-1][0] - trail[0][0]
                    dy = trail[-1][1] - trail[0][1]
                    if math.hypot(dx, dy) > MOVE_THRESHOLD:
                        move_angle = clockwise_angle(dx, dy)
                        cv2.putText(frame,
                                    f"Move angle: {move_angle:.0f} deg ({label(move_angle)})",
                                    (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)
            else:
                trail.clear()
                last_text = None  # print again when the hand reappears

            cv2.imshow("Hand angle (clockwise)", frame)
            if cv2.waitKey(1) & 0xFF == 27:  # Esc to quit
                break

    cap.release()
    cv2.destroyAllWindows()
    arduino.close()


if __name__ == "__main__":
    main()