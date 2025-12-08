# TECHIN-512-A-Final-Project-Proud-Dumrongpun
# 📘 Block Puzzle – CircuitPython Tetris-Style Game

## 🎮 Overview
Block Puzzle is a Tetris-inspired falling-block game built on the Seeed Studio XIAO ESP32-C3 using CircuitPython.  
It includes a centered 10×16 playfield, intro animation, difficulty menu, accelerometer-based control, rotary encoder navigation, line-clearing logic, leveling, a 10-minute timer, and NeoPixel feedback.

---

## 📁 Repository Structure
```
/
├── src/
│   └── code.py
│
├── library/
│   ├── adafruit_adxl34x/
│   ├── adafruit_displayio_ssd1306/
│   ├── adafruit_display_text/
│   ├── adafruit_bus_device/
│   └── neopixel.mpy
│
├── Documentation/
│   ├── Block Diagram.pdf
│   ├── CircuitDiagram.png
│   └── getting-started.kicad_sch
│
└── README.md
```

---

## ✨ Features
- Animated intro screen  
- Difficulty selection  
- Tilt-based movement using ADXL345  
- Rotary encoder menu control  
- Line-clearing and leveling system  
- NeoPixel visual feedback  
- 10‑minute countdown timer  

---

## 🔌 Hardware Wiring
OLED + ADXL345 share I2C:  
- SDA → D4  
- SCL → D5  
- VCC → 3V3  
- GND → GND  

Rotary Encoder:  
- A → D9  
- B → D10  
- Button → D7  

NeoPixel:  
- IN → D0  
- VCC → 3V3  
- GND → GND  

---

## ▶️ How to Run
1. Install CircuitPython on XIAO ESP32‑C3  
2. Add required libraries into `/library`  
3. Copy project to the CIRCUITPY drive  
4. Run `code.py` inside `/src/`  
5. Reset the board  

---

## 👤 Author
Peeraya “Proud” Dumrongpun  
TECHIN 512: Embedded Systems  
University of Washington MSTI Program