import time
import random
import board
import displayio
import digitalio
import terminalio
import neopixel
from adafruit_display_text import label
import i2cdisplaybus
import adafruit_displayio_ssd1306
import adafruit_adxl34x


# ============================================
# OLED SETUP
# ============================================
displayio.release_displays()
i2c = board.I2C()
display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

bitmap = displayio.Bitmap(128, 64, 2)
palette = displayio.Palette(2)
palette[0] = 0x000000
palette[1] = 0xFFFFFF
tilegrid = displayio.TileGrid(bitmap, pixel_shader=palette)

# -------- LEFT UI --------
level_text = label.Label(terminalio.FONT, text="Level", color=0xFFFFFF, x=2, y=3)
level_value = label.Label(terminalio.FONT, text="1", color=0xFFFFFF, x=2, y=15)

timer_text = label.Label(terminalio.FONT, text="Time", color=0xFFFFFF, x=2, y=29)
timer_value = label.Label(terminalio.FONT, text="10:00", color=0xFFFFFF, x=2, y=41)

# -------- RIGHT UI --------
mode_text = label.Label(terminalio.FONT, text="Mode", color=0xFFFFFF, x=98, y=3)
mode_value = label.Label(terminalio.FONT, text="---", color=0xFFFFFF, x=98, y=15)

ui_group = displayio.Group()
ui_group.append(level_text)
ui_group.append(level_value)
ui_group.append(timer_text)
ui_group.append(timer_value)
ui_group.append(mode_text)
ui_group.append(mode_value)

root = displayio.Group()
root.append(tilegrid)
root.append(ui_group)

# ============================================
# NEOPIXEL
# ============================================
pixels = neopixel.NeoPixel(board.D0, 1, brightness=0.4, auto_write=True)

rotate_color_index = 0
rotate_colors = [
    (255, 0, 0),
    (255, 128, 0),
    (255, 255, 0),
    (0, 255, 0),
    (0, 255, 255),
    (0, 0, 255),
    (128, 0, 255)
]


# ============================================
# ACCELEROMETER
# ============================================
accel = adafruit_adxl34x.ADXL345(i2c)
accel.range = adafruit_adxl34x.Range.RANGE_2_G

fx = fy = 0
ALPHA = 0.25

def tilt():
    global fx, fy
    x, y, z = accel.acceleration
    fx = fx*(1-ALPHA) + x*ALPHA
    fy = fy*(1-ALPHA) + y*ALPHA
    return fx, fy


# ============================================
# ROTARY + BUTTON
# ============================================
enc_a = digitalio.DigitalInOut(board.D9)
enc_b = digitalio.DigitalInOut(board.D10)
enc_btn = digitalio.DigitalInOut(board.D7)

enc_a.direction = digitalio.Direction.INPUT
enc_b.direction = digitalio.Direction.INPUT
enc_btn.direction = digitalio.Direction.INPUT
enc_btn.pull = digitalio.Pull.UP

lastA = enc_a.value
stableA = enc_a.value
lastTime = 0
debounceDelay = 0.003

def rotary_turn():
    global lastA, stableA, lastTime
    now = time.monotonic()
    currentA = enc_a.value
    moved = 0

    if currentA != lastA:
        lastTime = now
        lastA = currentA

    if (now - lastTime) > debounceDelay:
        if currentA != stableA:
            stableA = currentA
            moved = 1 if enc_b.value else -1
    return moved

def button_pressed():
    return not enc_btn.value


# ============================================
# TETRIS LOGIC
# ============================================
BOARD_W = 10
BOARD_H = 16
CELL = 4
BOARD_X_OFFSET = (128 - BOARD_W * CELL) // 2

SHAPES = {
    "I": [[1,1,1,1]],
    "O": [[1,1],[1,1]],
    "T": [[1,1,1],[0,1,0]],
    "L": [[1,0],[1,0],[1,1]],
    "J": [[0,1],[0,1],[1,1]],
    "S": [[0,1,1],[1,1,0]],
    "Z": [[1,1,0],[0,1,1]]
}

def rotate(shape):
    return [list(x) for x in zip(*shape[::-1])]

board_matrix = [[0] * BOARD_W for _ in range(BOARD_H)]

# For MED mode
original_shape = None
alt_shape = None
using_alt = False


# ============================================
# DRAW TILE & BOARD
# ============================================
tile_pixels = [(dx, dy) for dx in range(CELL) for dy in range(CELL)]

def draw_tile(gx, gy):
    px = gx * CELL + BOARD_X_OFFSET
    py = gy * CELL
    for dx, dy in tile_pixels:
        xx = px + dx
        yy = py + dy
        if 0 <= xx < 128 and 0 <= yy < 64:
            bitmap[xx, yy] = 1


def draw_board(shape, ox, oy):
    bitmap.fill(0)

    # placed blocks
    for y in range(BOARD_H):
        for x in range(BOARD_W):
            if board_matrix[y][x]:
                draw_tile(x, y)

    # falling block
    for y, row in enumerate(shape):
        for x, v in enumerate(row):
            if v:
                draw_tile(ox+x, oy+y)

    # border
    left = BOARD_X_OFFSET
    right = left + BOARD_W * CELL
    bottom = BOARD_H * CELL

    for yy in range(bottom):
        bitmap[left, yy] = 1
        bitmap[right, yy] = 1

    for xx in range(left, right+1):
        bitmap[xx, 0] = 1
        bitmap[xx, bottom-1] = 1


# ============================================
# COLLISION
# ============================================
def check_collision(shape, ox, oy):
    for y, row in enumerate(shape):
        for x, v in enumerate(row):
            if v:
                bx = ox+x
                by = oy+y
                if bx < 0 or bx >= BOARD_W:
                    return True
                if by >= BOARD_H:
                    return True
                if by >= 0 and board_matrix[by][bx]:
                    return True
    return False


def place_shape(shape, ox, oy):
    for y, row in enumerate(shape):
        for x, v in enumerate(row):
            if v:
                board_matrix[oy+y][ox+x] = 1


def clear_lines():
    global board_matrix
    new = [r for r in board_matrix if not all(r)]
    cleared = BOARD_H - len(new)
    for _ in range(cleared):
        new.insert(0, [0]*BOARD_W)
    board_matrix = new
    return cleared


# ============================================
# INTRO SCREEN WITH ANIMATION
# ============================================
def intro_screen():
    intro_bitmap = displayio.Bitmap(128, 64, 2)
    intro_palette = displayio.Palette(2)
    intro_palette[0] = 0x000000
    intro_palette[1] = 0xFFFFFF
    intro_grid = displayio.TileGrid(intro_bitmap, pixel_shader=intro_palette)
    
    intro = displayio.Group()
    intro.append(intro_grid)
    
    title_label = label.Label(terminalio.FONT, text="BLOCK PUZZLE", color=0xFFFFFF, x=30, y=30)
    press_label = label.Label(terminalio.FONT, text="Press to Start", color=0xFFFFFF, x=26, y=50)
    
    intro.append(title_label)
    intro.append(press_label)
    
    display.root_group = intro
    
    # Falling blocks animation
    blocks = []
    for i in range(5):
        blocks.append({
            'x': random.randint(1, 10) * 10,
            'y': -random.randint(0, 30),
            'speed': random.randint(1, 3),
            'size': random.choice([3, 4, 5])
        })
    
    step = 0
    
    while True:
        intro_bitmap.fill(0)
        
        # Animate falling blocks
        for block in blocks:
            # Draw block
            for dx in range(block['size']):
                for dy in range(block['size']):
                    px = block['x'] + dx
                    py = int(block['y']) + dy
                    if 0 <= px < 128 and 0 <= py < 64:
                        intro_bitmap[px, py] = 1
            
            # Move block down
            block['y'] += block['speed'] * 0.5
            
            # Reset if off screen
            if block['y'] > 64:
                block['y'] = -random.randint(5, 15)
                block['x'] = random.randint(1, 10) * 10
        
        # Rainbow LED
        pixels[0] = rotate_colors[step % 7]
        step += 1
        
        if button_pressed():
            time.sleep(0.2)
            return
        
        time.sleep(0.05)


# ============================================
# DIFFICULTY MENU
# ============================================
DIFFICULTIES = [
    ("Easy", 0.80),
    ("Med",  0.40),
    ("Hard", 0.20)
]

def choose_difficulty():
    index = 0

    menu = displayio.Group()
    title = label.Label(terminalio.FONT, text="Select Difficulty:", color=0xFFFFFF, x=5, y=8)
    option = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=15, y=26)
    menu.append(title)
    menu.append(option)

    display.root_group = menu

    while True:
        lst = ["  Easy", "  Med", "  Hard"]
        lst[index] = "> " + DIFFICULTIES[index][0]
        option.text = "\n".join(lst)

        mv = rotary_turn()
        if mv == 1:
            index = (index + 1) % 3
        elif mv == -1:
            index = (index - 1) % 3

        if button_pressed():
            time.sleep(0.2)
            return DIFFICULTIES[index][0], DIFFICULTIES[index][1]

        time.sleep(0.05)


# ============================================
# FORMAT TIME
# ============================================
def format_time(sec):
    m = sec // 60
    s = sec % 60
    return f"{m:02d}:{s:02d}"


# ============================================
# GAME LOOP + TIMER
# ============================================
def game_loop(mode_name, fall_interval):
    global board_matrix, original_shape, alt_shape, using_alt

    board_matrix = [[0]*BOARD_W for _ in range(BOARD_H)]

    # ย้ายมาไว้ที่นี่แทน - แสดงหน้าเกมเฉพาะเมื่อเริ่มเกมจริง ๆ
    display.root_group = root

    level = 1
    level_value.text = str(level)
    mode_value.text = mode_name

    # ====== TIMER START: 10 MINUTES ======
    time_left = 600
    last_tick = time.monotonic()
    timer_value.text = "10:00"

    speed_increment = 0.03

    name, original_shape = random.choice(list(SHAPES.items()))
    shape = [row[:] for row in original_shape]
    alt_shape = rotate(original_shape)
    using_alt = False

    x, y = 4, 0
    last_fall = time.monotonic()
    last_move = 0  # สำหรับ debounce การเคลื่อนที่
    last_draw = 0  # สำหรับจำกัดอัตราการวาด

    pixels[0] = (0, 255, 0)

    while True:
        fx, fy = tilt()
        
        moved = False  # ตรวจสอบว่ามีการเคลื่อนที่หรือไม่
        now = time.monotonic()

        # เอียงซ้าย-ขวา = เลื่อนบล็อกซ้าย-ขวา (เพิ่ม debounce)
        if now - last_move > 0.1:  # debounce 100ms
            if fx < -1.2 and not check_collision(shape, x-1, y):
                x -= 1
                moved = True
                last_move = now
            elif fx > 1.2 and not check_collision(shape, x+1, y):
                x += 1
                moved = True
                last_move = now

        # เอียงข้างหลัง (fy < -3) = ตกเร็วทันที (จอคว่ำลง)
        if fy < -3:
            if not check_collision(shape, x, y+1):
                y += 1
                last_fall = time.monotonic()  # reset timer
                moved = True

        # ROTATION RULE
        if button_pressed():
            old_shape = shape
            if mode_name == "Easy":
                r = rotate(shape)
                if not check_collision(r, x, y):
                    shape = r
                    moved = True

            elif mode_name == "Med":
                if alt_shape != original_shape:
                    new_shape = alt_shape if not using_alt else original_shape
                    if not check_collision(new_shape, x, y):
                        shape = new_shape
                        using_alt = not using_alt
                        moved = True

            elif mode_name == "Hard":
                pass

            pixels[0] = rotate_colors[rotate_color_index]
            globals()["rotate_color_index"] = (rotate_color_index + 1) % 7
            time.sleep(0.15)

        # ==========================
        # TIMER UPDATE EVERY 1 SEC
        # ==========================
        now = time.monotonic()
        if now - last_tick >= 1:
            time_left -= 1
            if time_left <= 0:
                timer_value.text = "00:00"
                return level
            timer_value.text = format_time(time_left)
            last_tick = now

        # FALL - ตกตามปกติ
        if time.monotonic() - last_fall > fall_interval:
            if not check_collision(shape, x, y+1):
                y += 1
                moved = True
            else:
                place_shape(shape, x, y)
                cleared = clear_lines()

                if cleared:
                    level += 1
                    level_value.text = str(level)
                    fall_interval = max(0.05, fall_interval - speed_increment)

                name, original_shape = random.choice(list(SHAPES.items()))
                shape = [row[:] for row in original_shape]
                alt_shape = rotate(original_shape)
                using_alt = False
                x, y = 4, 0

                if check_collision(shape, x, y):
                    return level
                
                moved = True

            last_fall = time.monotonic()

        # วาดเฉพาะเมื่อมีการเปลี่ยนแปลง และจำกัดอัตราการวาด
        if moved and (time.monotonic() - last_draw > 0.05):
            draw_board(shape, x, y)
            last_draw = time.monotonic()
        
        time.sleep(0.01)


# ============================================
# GAME OVER
# ============================================
def game_over_screen(level):
    for _ in range(3):
        pixels[0] = (255, 0, 0)
        time.sleep(0.2)
        pixels[0] = (0, 0, 0)
        time.sleep(0.2)

    pixels[0] = (255, 0, 0)

    g = displayio.Group()
    g.append(label.Label(terminalio.FONT, text="GAME OVER", color=0xFFFFFF, x=32, y=20))
    g.append(label.Label(terminalio.FONT, text=f"Level: {level}", color=0xFFFFFF, x=40, y=36))
    g.append(label.Label(terminalio.FONT, text="Press to Restart", color=0xFFFFFF, x=14, y=52))

    display.root_group = g

    while not button_pressed():
        time.sleep(0.05)

    pixels[0] = (0, 0, 0)


# ============================================
# MAIN LOOP
# ============================================
while True:
    intro_screen()
    mode_name, speed = choose_difficulty()
    level = game_loop(mode_name, speed)
    game_over_screen(level)
