# BLOCK PUZZLE – Tilt & Rotate Tetris Game

A 90’s-style handheld falling-block game built on the Xiao ESP32-C3 using CircuitPython.  
Players tilt the device to move blocks, press to rotate, and survive against a countdown timer while clearing lines and leveling up.

---

## ⭐ Overview
**BLOCK PUZZLE** is a motion-controlled puzzle game inspired by Tetris-like gameplay.  
The game includes:

- Accelerometer-based tilt control  
- Rotary encoder + button input  
- Difficulty selection (Easy / Med / Hard)  
- 10-minute countdown timer  
- Level progression + falling speed increase  
- NeoPixel visual indicators  
- Intro animation splash screen  
- Restart without power cycling  
- OLED UI for level, timer, and mode

---

## 🎮 How to Play

### 1. Power On  
Flip the switch to turn on the device.  
An animated intro screen appears with falling block effects and rainbow NeoPixel.  
Press the button to continue.

### 2. Choose Difficulty  
Rotate encoder to select:

| Difficulty | Fall Speed |
|-----------|------------|
| Easy | 0.80 sec |
| Med | 0.40 sec |
| Hard | 0.20 sec |

Press encoder button to confirm.

### 3. Gameplay  
The OLED shows:

- Level  
- Time Remaining  
- Difficulty Mode  
- Falling Block Board  

#### Controls
| Action | How to Perform |
|--------|----------------|
| Move Left | Tilt left (fx < –1.2) |
| Move Right | Tilt right (fx > 1.2) |
| Soft Drop | Tilt backward (fy < –3) |
| Rotate Block | Press encoder button |
| Start / Restart | Press encoder button |

#### Rotation Rules by Mode
| Mode | Rotation Behavior |
|------|-------------------|
| Easy | Full rotation allowed |
| Med | Switches between original and one rotated variant |
| Hard | No rotation |

---

## 🎯 Level Progression & Timer
- Clearing lines increases level  
- Each level increases falling speed  
- Timer starts at **10:00**  
- If timer reaches 00:00 → Game Over  

---

## ❌ Game Over
Triggered when:
- Blocks reach the top  
- Timer expires  

Screen shows:
- GAME OVER  
- Final Level  
- “Press to Restart”

NeoPixel flashes red.  
Press button to restart the game loop.

---

## 🔧 Components Used

| Component | Purpose |
|----------|---------|
| Xiao ESP32-C3 | Runs CircuitPython + game logic |
| SSD1306 128×64 OLED | Shows UI + board rendering |
| ADXL345 Accelerometer | Tilt-based controls |
| Rotary Encoder | Menu navigation |
| Encoder Button | Rotation + Start/Restart |
| NeoPixel (D0) | LED effects |
| LiPo Battery | Power source |
| On/Off Switch | Hardware power control |
| Perfboard + Female Headers | Required for removable hardware |

---

## 🧠 System Architecture

### Inputs
- ADXL345 accelerometer  
- Rotary encoder A/B  
- Push button  

### Outputs
- OLED display (displayio)  
- NeoPixel RGB indicator  

### Microcontroller
- Xiao ESP32-C3  
- CircuitPython 10.x  

### Power Flow
LiPo → Switch → 5V pin on Xiao

System Diagram:  
`Documentation/SystemDiagram.png`

---

## 🔌 Circuit Diagram
Includes wiring for:

- OLED (I2C)
- ADXL345 (I2C)
- Rotary Encoder (D9 / D10)
- Button (D7 + pull-up)
- NeoPixel (D0)
- LiPo → Switch → 5V

Diagram:  
`Documentation/CircuitDiagram.png`

---

## 🎨 Enclosure Design
The enclosure includes:

- OLED viewing window  
- Rotary encoder opening  
- Button access  
- USB-C access  
- On/Off switch opening  
- Removable lid for electronics  
- Printed in non-yellow materials (class constraint)

Files:  
`Documentation/Enclosure/`

---

## 🧪 Accelerometer Filtering
A low-pass filter is applied:

```
f = f * (1 - ALPHA) + x * ALPHA
```

This improves stability of:
- Left/right movement  
- Fast drop detection  
- Noise reduction  

---

## 💡 NeoPixel Feedback

| Event | LED Color |
|--------|-----------|
| Intro Animation | Rainbow |
| Game Start | Green |
| Rotation Action | Cycling colors |
| Game Over | Red flashing |
| Restart Ready | Off |

---

## 📁 Repository Structure

```
.
/
├── src/
│   └── code.py
│
├── Libraries/
│   ├── adafruit_bus_device/
│   │   ├── __init__.py
│   │   ├── i2c_device.mpy
│   │   └── spi_device.mpy
│   │
│   ├── adafruit_display_text/
│   │   ├── __init__.mpy
│   │   ├── bitmap_label.mpy
│   │   ├── label.mpy
│   │   ├── outlined_label.mpy
│   │   ├── scrolling_label.mpy
│   │   └── text_box.mpy
│   │
│   ├── adafruit_adxl34x.mpy
│   ├── adafruit_displayio_ssd1306.mpy
│   └── neopixel.mpy
│
├── Documentation/
│   ├── Circuit diagram picture.png
│   └── getting-started.kicad_sch
│
└── README.md
```

---

## ▶️ How to Run

1. Install CircuitPython 10.x on Xiao ESP32-C3  
2. Copy to CIRCUITPY drive:  
   - `code.py`  
   - `libraries/` folder  
3. Power with USB-C or LiPo  
4. Game will start at the Intro Screen  
5. Press button to begin!

---

## 👩‍💻 Author
Peeraya (Proud) Dumrongpun  
TECHIN 509 — University of Washington GIX  
Final Project – 2025