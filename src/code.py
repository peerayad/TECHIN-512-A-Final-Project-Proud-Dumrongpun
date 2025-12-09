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
# OLED DISPLAY SETUP
# Initialize 128x64 OLED screen via I2C
# ============================================
displayio.release_displays()
i2c = board.I2C()
display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# Create bitmap for drawing (2 colors: black and white)
bitmap = displayio.Bitmap(128, 64, 2)
palette = displayio.Palette(2)
palette[0] = 0x000000  # Black
palette[1] = 0xFFFFFF  # White
tilegrid = displayio.TileGrid(bitmap, pixel_shader=palette)

# -------- LEFT UI ELEMENTS --------
# Display level information on the left side
level_text = label.Label(terminalio.FONT, text="Level", color=0xFFFFFF, x=2, y=3)
level_value = label.Label(terminalio.FONT, text="1", color=0xFFFFFF, x=2, y=15)

# Display timer information on the left side
timer_text = label.Label(terminalio.FONT, text="Time", color=0xFFFFFF, x=2, y=29)
timer_value = label.Label(terminalio.FONT, text="10:00", color=0xFFFFFF, x=2, y=41)

# -------- RIGHT UI ELEMENTS --------
# Display game mode (Easy/Med/Hard) on the right side
mode_text = label.Label(terminalio.FONT, text="Mode", color=0xFFFFFF, x=98, y=3)
mode_value = label.Label(terminalio.FONT, text="---", color=0xFFFFFF, x=98, y=15)

# Group all UI elements together
ui_group = displayio.Group()
ui_group.append(level_text)
ui_group.append(level_value)
ui_group.append(timer_text)
ui_group.append(timer_value)
ui_group.append(mode_text)
ui_group.append(mode_value)

# Create root display group with game board and UI
root = displayio.Group()
root.append(tilegrid)
root.append(ui_group)

# ============================================
# NEOPIXEL LED SETUP
# Single RGB LED for visual feedback
# ============================================
pixels = neopixel.NeoPixel(board.D0, 1, brightness=0.4, auto_write=True)

# Rainbow color rotation for LED effects
rotate_color_index = 0
rotate_colors = [
    (255, 0, 0),      # Red
    (255, 128, 0),    # Orange
    (255, 255, 0),    # Yellow
    (0, 255, 0),      # Green
    (0, 255, 255),    # Cyan
    (0, 0, 255),      # Blue
    (128, 0, 255)     # Purple
]


# ============================================
# ACCELEROMETER SETUP
# Detect tilt for game controls
# ============================================
accel = adafruit_adxl34x.ADXL345(i2c)
accel.range = adafruit_adxl34x.Range.RANGE_2_G

# Filtered acceleration values
fx = fy = 0
ALPHA = 0.25  # Low-pass filter coefficient

def tilt():
    """Read and filter accelerometer data for smooth tilt detection"""
    global fx, fy
    x, y, z = accel.acceleration
    # Apply low-pass filter to reduce noise
    fx = fx*(1-ALPHA) + x*ALPHA
    fy = fy*(1-ALPHA) + y*ALPHA
    return fx, fy


# ============================================
# ROTARY ENCODER + BUTTON SETUP
# For rotation and game control
# ============================================
enc_a = digitalio.DigitalInOut(board.D9)
enc_b = digitalio.DigitalInOut(board.D10)
enc_btn = digitalio.DigitalInOut(board.D7)

enc_a.direction = digitalio.Direction.INPUT
enc_b.direction = digitalio.Direction.INPUT
enc_btn.direction = digitalio.Direction.INPUT
enc_btn.pull = digitalio.Pull.UP

# Rotary encoder state tracking
lastA = enc_a.value
stableA = enc_a.value
lastTime = 0
debounceDelay = 0.003  # 3ms debounce delay

def rotary_turn():
    """Detect rotary encoder rotation with debouncing"""
    global lastA, stableA, lastTime
    now = time.monotonic()
    currentA = enc_a.value
    moved = 0

    # Detect state change
    if currentA != lastA:
        lastTime = now
        lastA = currentA

    # Wait for debounce period before confirming
    if (now - lastTime) > debounceDelay:
        if currentA != stableA:
            stableA = currentA
            # Determine direction based on encoder B signal
            moved = 1 if enc_b.value else -1
    return moved

def button_pressed():
    """Check if button is pressed (active low)"""
    return not enc_btn.value


# ============================================
# TETRIS GAME LOGIC
# Board dimensions and piece definitions
# ============================================
BOARD_W = 10  # Board width in cells
BOARD_H = 16  # Board height in cells
CELL = 4      # Cell size in pixels
BOARD_X_OFFSET = (128 - BOARD_W * CELL) // 2  # Center board horizontally

# Tetris piece shapes (1 = filled, 0 = empty)
SHAPES = {
    "I": [[1,1,1,1]],           # Line piece
    "O": [[1,1],[1,1]],         # Square piece
    "T": [[1,1,1],[0,1,0]],     # T piece
    "L": [[1,0],[1,0],[1,1]],   # L piece
    "J": [[0,1],[0,1],[1,1]],   # J piece
    "S": [[0,1,1],[1,1,0]],     # S piece
    "Z": [[1,1,0],[0,1,1]]      # Z piece
}

def rotate(shape):
    """Rotate a shape 90 degrees clockwise"""
    return [list(x) for x in zip(*shape[::-1])]

# Game board matrix (0 = empty, 1 = filled)
board_matrix = [[0] * BOARD_W for _ in range(BOARD_H)]

# For Medium difficulty mode - alternate between original and rotated shape
original_shape = None
alt_shape = None
using_alt = False


# ============================================
# DRAWING FUNCTIONS
# Render game board and pieces on OLED
# ============================================
# Pre-calculate cell pixels for faster drawing
tile_pixels = [(dx, dy) for dx in range(CELL) for dy in range(CELL)]

def draw_tile(gx, gy):
    """Draw a single 4x4 tile at grid position (gx, gy)"""
    px = gx * CELL + BOARD_X_OFFSET
    py = gy * CELL
    for dx, dy in tile_pixels:
        xx = px + dx
        yy = py + dy
        if 0 <= xx < 128 and 0 <= yy < 64:
            bitmap[xx, yy] = 1


def draw_board(shape, ox, oy):
    """Draw the entire game board including placed blocks, falling piece, and border"""
    bitmap.fill(0)  # Clear screen

    # Draw all placed blocks on the board
    for y in range(BOARD_H):
        for x in range(BOARD_W):
            if board_matrix[y][x]:
                draw_tile(x, y)

    # Draw the currently falling piece
    for y, row in enumerate(shape):
        for x, v in enumerate(row):
            if v:
                draw_tile(ox+x, oy+y)

    # Draw board border
    left = BOARD_X_OFFSET
    right = left + BOARD_W * CELL
    bottom = BOARD_H * CELL

    # Vertical borders
    for yy in range(bottom):
        bitmap[left, yy] = 1
        bitmap[right, yy] = 1

    # Horizontal borders
    for xx in range(left, right+1):
        bitmap[xx, 0] = 1
        bitmap[xx, bottom-1] = 1


# ============================================
# COLLISION DETECTION
# Check if piece can move to a position
# ============================================
def check_collision(shape, ox, oy):
    """Check if shape at position (ox, oy) collides with board or boundaries"""
    for y, row in enumerate(shape):
        for x, v in enumerate(row):
            if v:
                bx = ox+x
                by = oy+y
                # Check horizontal boundaries
                if bx < 0 or bx >= BOARD_W:
                    return True
                # Check bottom boundary
                if by >= BOARD_H:
                    return True
                # Check collision with placed blocks
                if by >= 0 and board_matrix[by][bx]:
                    return True
    return False


def place_shape(shape, ox, oy):
    """Place the current shape permanently on the board"""
    for y, row in enumerate(shape):
        for x, v in enumerate(row):
            if v:
                board_matrix[oy+y][ox+x] = 1


def clear_lines():
    """Clear completed lines and return number of lines cleared"""
    global board_matrix
    # Keep only incomplete rows
    new = [r for r in board_matrix if not all(r)]
    cleared = BOARD_H - len(new)
    # Add empty rows at the top
    for _ in range(cleared):
        new.insert(0, [0]*BOARD_W)
    board_matrix = new
    return cleared


# ============================================
# INTRO SCREEN WITH ANIMATION
# Show title screen with falling blocks
# ============================================
def intro_screen():
    """Display animated intro screen until button is pressed"""
    # Create intro display
    intro_bitmap = displayio.Bitmap(128, 64, 2)
    intro_palette = displayio.Palette(2)
    intro_palette[0] = 0x000000
    intro_palette[1] = 0xFFFFFF
    intro_grid = displayio.TileGrid(intro_bitmap, pixel_shader=intro_palette)
    
    intro = displayio.Group()
    intro.append(intro_grid)
    
    # Title and instruction text
    title_label = label.Label(terminalio.FONT, text="BLOCK PUZZLE", color=0xFFFFFF, x=30, y=30)
    press_label = label.Label(terminalio.FONT, text="Press to Start", color=0xFFFFFF, x=26, y=50)
    
    intro.append(title_label)
    intro.append(press_label)
    
    display.root_group = intro
    
    # Create animated falling blocks
    blocks = []
    for i in range(5):
        blocks.append({
            'x': random.randint(1, 10) * 10,
            'y': -random.randint(0, 30),
            'speed': random.randint(1, 3),
            'size': random.choice([3, 4, 5])
        })
    
    step = 0
    
    # Animation loop
    while True:
        intro_bitmap.fill(0)
        
        # Animate each falling block
        for block in blocks:
            # Draw block
            for dx in range(block['size']):
                for dy in range(block['size']):
                    px = block['x'] + dx
                    py = int(block['y']) + dy
                    if 0 <= px < 128 and 0 <= py < 64:
                        intro_bitmap[px, py] = 1
            
            # Move block downward
            block['y'] += block['speed'] * 0.5
            
            # Reset block position when off screen
            if block['y'] > 64:
                block['y'] = -random.randint(5, 15)
                block['x'] = random.randint(1, 10) * 10
        
        # Cycle through rainbow colors on LED
        pixels[0] = rotate_colors[step % 7]
        step += 1
        
        # Exit when button is pressed
        if button_pressed():
            time.sleep(0.2)
            return
        
        time.sleep(0.05)


# ============================================
# DIFFICULTY SELECTION MENU
# Choose game speed and rotation rules
# ============================================
# Difficulty settings: (name, fall_interval_in_seconds)
DIFFICULTIES = [
    ("Easy", 0.80),  # Slow fall, free rotation
    ("Med",  0.40),  # Medium fall, toggle between 2 rotations
    ("Hard", 0.20)   # Fast fall, no rotation allowed
]

def choose_difficulty():
    """Display menu to select difficulty level using rotary encoder"""
    index = 0

    # Create menu display
    menu = displayio.Group()
    title = label.Label(terminalio.FONT, text="Select Difficulty:", color=0xFFFFFF, x=5, y=8)
    option = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=15, y=26)
    menu.append(title)
    menu.append(option)

    display.root_group = menu

    while True:
        # Build menu text with current selection marked
        lst = ["  Easy", "  Med", "  Hard"]
        lst[index] = "> " + DIFFICULTIES[index][0]
        option.text = "\n".join(lst)

        # Handle rotary encoder input
        mv = rotary_turn()
        if mv == 1:
            index = (index + 1) % 3
        elif mv == -1:
            index = (index - 1) % 3

        # Confirm selection with button press
        if button_pressed():
            time.sleep(0.2)
            return DIFFICULTIES[index][0], DIFFICULTIES[index][1]

        time.sleep(0.05)


# ============================================
# TIME FORMATTING
# Convert seconds to MM:SS format
# ============================================
def format_time(sec):
    """Format seconds as MM:SS string"""
    m = sec // 60
    s = sec % 60
    return f"{m:02d}:{s:02d}"


# ============================================
# MAIN GAME LOOP
# Core gameplay with 10-minute timer
# ============================================
def game_loop(mode_name, fall_interval):
    """Main game loop - returns final level when game ends"""
    global board_matrix, original_shape, alt_shape, using_alt

    # Reset board for new game
    board_matrix = [[0]*BOARD_W for _ in range(BOARD_H)]

    # Switch to game display
    display.root_group = root

    # Initialize game state
    level = 1
    level_value.text = str(level)
    mode_value.text = mode_name

    # ====== 10-MINUTE COUNTDOWN TIMER ======
    time_left = 600  # 10 minutes in seconds
    last_tick = time.monotonic()
    timer_value.text = "10:00"

    # Speed increases with each level cleared
    speed_increment = 0.03

    # Spawn first piece
    name, original_shape = random.choice(list(SHAPES.items()))
    shape = [row[:] for row in original_shape]
    alt_shape = rotate(original_shape)
    using_alt = False

    x, y = 4, 0  # Starting position
    last_fall = time.monotonic()
    last_move = 0   # Debounce for tilt movement
    last_draw = 0   # Limit draw rate

    pixels[0] = (0, 255, 0)  # Green LED during gameplay

    while True:
        # Read accelerometer tilt
        fx, fy = tilt()
        
        moved = False  # Track if redraw is needed
        now = time.monotonic()

        # ====== TILT CONTROL: LEFT/RIGHT ======
        # Tilt left/right to move piece horizontally (with debounce)
        if now - last_move > 0.1:  # 100ms debounce
            if fx < -1.2 and not check_collision(shape, x-1, y):
                x -= 1
                moved = True
                last_move = now
            elif fx > 1.2 and not check_collision(shape, x+1, y):
                x += 1
                moved = True
                last_move = now

        # ====== TILT CONTROL: FAST DROP ======
        # Tilt backward (screen face down) to drop piece instantly
        if fy < -3:
            if not check_collision(shape, x, y+1):
                y += 1
                last_fall = time.monotonic()  # Reset fall timer
                moved = True

        # ====== BUTTON: ROTATION ======
        # Rotation behavior depends on difficulty mode
        if button_pressed():
            old_shape = shape
            if mode_name == "Easy":
                # Easy mode: Free rotation
                r = rotate(shape)
                if not check_collision(r, x, y):
                    shape = r
                    moved = True

            elif mode_name == "Med":
                # Medium mode: Toggle between original and 90° rotation only
                if alt_shape != original_shape:
                    new_shape = alt_shape if not using_alt else original_shape
                    if not check_collision(new_shape, x, y):
                        shape = new_shape
                        using_alt = not using_alt
                        moved = True

            elif mode_name == "Hard":
                # Hard mode: No rotation allowed
                pass

            # Change LED color on each rotation
            pixels[0] = rotate_colors[rotate_color_index]
            globals()["rotate_color_index"] = (rotate_color_index + 1) % 7
            time.sleep(0.15)

        # ====== UPDATE COUNTDOWN TIMER ======
        # Update every 1 second
        now = time.monotonic()
        if now - last_tick >= 1:
            time_left -= 1
            if time_left <= 0:
                # Time's up - game over
                timer_value.text = "00:00"
                return level
            timer_value.text = format_time(time_left)
            last_tick = now

        # ====== AUTOMATIC FALL ======
        # Piece falls at regular intervals
        if time.monotonic() - last_fall > fall_interval:
            if not check_collision(shape, x, y+1):
                # Continue falling
                y += 1
                moved = True
            else:
                # Piece has landed
                place_shape(shape, x, y)
                cleared = clear_lines()

                # Level up if lines were cleared
                if cleared:
                    level += 1
                    level_value.text = str(level)
                    # Increase fall speed (minimum 0.05s)
                    fall_interval = max(0.05, fall_interval - speed_increment)

                # Spawn new piece
                name, original_shape = random.choice(list(SHAPES.items()))
                shape = [row[:] for row in original_shape]
                alt_shape = rotate(original_shape)
                using_alt = False
                x, y = 4, 0

                # Check for game over (new piece can't spawn)
                if check_collision(shape, x, y):
                    return level
                
                moved = True

            last_fall = time.monotonic()

        # ====== RENDER ======
        # Redraw only when needed and throttle to 20 FPS
        if moved and (time.monotonic() - last_draw > 0.05):
            draw_board(shape, x, y)
            last_draw = time.monotonic()
        
        time.sleep(0.01)


# ============================================
# GAME OVER SCREEN
# Display final level and restart prompt
# ============================================
def game_over_screen(level):
    """Show game over screen with flashing red LED"""
    # Flash red LED 3 times
    for _ in range(3):
        pixels[0] = (255, 0, 0)
        time.sleep(0.2)
        pixels[0] = (0, 0, 0)
        time.sleep(0.2)

    pixels[0] = (255, 0, 0)  # Keep LED red

    # Create game over display
    g = displayio.Group()
    g.append(label.Label(terminalio.FONT, text="GAME OVER", color=0xFFFFFF, x=32, y=20))
    g.append(label.Label(terminalio.FONT, text=f"Level: {level}", color=0xFFFFFF, x=40, y=36))
    g.append(label.Label(terminalio.FONT, text="Press to Restart", color=0xFFFFFF, x=14, y=52))

    display.root_group = g

    # Wait for button press to restart
    while not button_pressed():
        time.sleep(0.05)

    pixels[0] = (0, 0, 0)  # Turn off LED


# ============================================
# MAIN PROGRAM LOOP
# Cycle through intro -> difficulty -> game -> game over
# ============================================
while True:
    intro_screen()                          # Show intro with animation
    mode_name, speed = choose_difficulty()  # Select difficulty
    level = game_loop(mode_name, speed)     # Play game (returns final level)
    game_over_screen(level)                 # Show game over and wait for restart