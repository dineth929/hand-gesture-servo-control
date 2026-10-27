# Hand Angle Servo Control

Control a servo motor with your hand. A webcam tracks your hand with [MediaPipe](https://developers.google.com/mediapipe), Python computes the angle your hand is pointing, and an Arduino turns a servo to match.

## How it works

1. The webcam captures a frame and MediaPipe finds the hand landmarks.
2. The script draws a line from the **wrist** to the **base of the middle finger** and measures its angle, clockwise from the left horizontal:

   | Hand points | Angle |
   |-------------|-------|
   | Left        | 0°    |
   | Up          | 90°   |
   | Right       | 180°  |
   | Down        | 270°  |

3. The angle is clamped to 0-180°, smoothed, and sent over serial as a single byte.
4. The Arduino reads the byte and moves the servo (`180 - angle`, so the servo follows the hand direction rather than mirroring it).

Only the upper half-sweep (Left → Up → Right) is mapped to the servo. Angles past 180° (hand pointing downward) are held at 180°.

## Project structure

```
hand-angle-servo/
├── README.md
├── requirements.txt
├── LICENSE
├── .gitignore
├── python/
│   └── hand_servo.py              # hand tracking + serial sender
└── arduino/
    └── servo_receiver.ino         # servo controller sketch
```

## Hardware

- Arduino (Uno, Nano, or similar)
- Hobby servo (e.g. SG90 or MG90S)
- USB webcam or built-in laptop camera
- Jumper wires

### Wiring

| Servo wire | Arduino pin |
|------------|-------------|
| Signal (orange/yellow) | D3 |
| Power (red) | 5V |
| Ground (brown/black) | GND |

> For larger servos, power them from an external supply and connect its ground to the Arduino GND.

## Software setup

### 1. Upload the Arduino sketch

1. Open `arduino/servo_receiver.ino` in the Arduino IDE.
2. Select your board and port, then click **Upload**.
3. Close the Serial Monitor afterward, since it blocks the port.

### 2. Install Python dependencies

Python 3.9-3.11 is recommended (MediaPipe's legacy `solutions` API is used).

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Run

```bash
python python/hand_servo.py --port COM8
```

Replace `COM8` with your Arduino's port:

| OS | Typical port |
|----|--------------|
| Windows | `COM3`, `COM8`, ... (see Device Manager) |
| Linux | `/dev/ttyUSB0` or `/dev/ttyACM0` |
| macOS | `/dev/cu.usbmodemXXXX` |

Press **Esc** in the video window to quit.

## Settings

Edit the constants at the top of `python/hand_servo.py`:

| Setting | Default | Meaning |
|---------|---------|---------|
| `CAMERA_INDEX` | `0` | Which camera to use |
| `SMOOTHING` | `0.3` | 0-1; lower = smoother but slower response |
| `TRAIL_LEN` | `5` | Frames used to estimate movement direction (display only) |
| `MOVE_THRESHOLD` | `15` | Pixels of movement before direction is shown |

## Troubleshooting

- **`Could not open COM8`**: wrong port, or another program (Serial Monitor) is using it.
- **Servo jitters**: lower `SMOOTHING`, or power the servo from an external supply.
- **Servo moves the wrong way**: change `180-angle` to `angle` in the Arduino sketch.
- **No camera image**: try `CAMERA_INDEX = 1`.
- **`mediapipe` has no attribute `solutions`**: install the pinned version from `requirements.txt`.

## License

MIT, see [LICENSE](LICENSE).
