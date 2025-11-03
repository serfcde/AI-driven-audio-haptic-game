# This is the Python "Software Application Layer"
# This is an UPDATED version with 5 levels, wall collisions, and level progression.

import pygame
import math
import serial
import time

# --- 1. CONFIGURATION ---

# -- Serial Port Configuration --
SERIAL_PORT = "COM4"  # Change this to match your Arduino's COM port
BAUD_RATE = 115200

# -- Game Window --
TILE_SIZE = 40  # The size of each grid square in pixels
MAP_WIDTH_TILES = 20
MAP_HEIGHT_TILES = 15

# Calculate window size based on map
WINDOW_WIDTH = TILE_SIZE * MAP_WIDTH_TILES
WINDOW_HEIGHT = TILE_SIZE * MAP_HEIGHT_TILES
GAME_TITLE = "Haptic Game - Researcher View"

# -- Colors --
COLOR_BACKGROUND = (0, 0, 0)       # Black
COLOR_WALL = (100, 100, 255)     # Blue
COLOR_USER = (0, 255, 0)         # Green
COLOR_TARGET = (255, 0, 0)       # Red
COLOR_TEXT = (255, 255, 255)     # White

# -- Game Logic --
USER_SPEED = 5  # Pixels per frame
PLAYER_RADIUS = 8 # Size of the player dot

# -- GAME LEVEL DATA --
# We now have 5 levels, each with a start/target (in tiles) and a map.
LEVEL_DATA = [
    # Level 1: Simple S-curve
    {
        "start_pos": (1.5, 1.5), "target_pos": (18.5, 13.5),
        "map": [
            "11111111111111111111",
            "10000000000001111111",
            "11111111111100000001",
            "11111111111101111111",
            "11111111111100000001",
            "10000000000001111111",
            "10111111111111111111",
            "10000000000000000001",
            "11111111111111110111",
            "11111111111111110111",
            "10000000000000000111",
            "10111111111111111111",
            "10111111111111111111",
            "10000000000000000001",
            "11111111111111111111"
        ]
    },
    # Level 2: Original Map
    {
        "start_pos": (1.5, 1.5), "target_pos": (18.5, 13.5),
        "map": [
            "11111111111111111111",
            "10001000000001000001",
            "10111011111101011101",
            "10000010000000000001",
            "10111110111111110111",
            "10100000100000010001",
            "10101110101111110101",
            "10001000100000000101",
            "11101011111111111101",
            "10001000000000100001",
            "10111111101111101111",
            "10000000101000000001",
            "10111110101011111101",
            "10000010000010000001",
            "11111111111111111111"
        ]
    },
    # Level 3: Long Corridor
    {
        "start_pos": (1.5, 7.5), "target_pos": (18.5, 7.5),
        "map": [
            "11111111111111111111",
            "11111111111111111111",
            "11111111111111111111",
            "11110000000000000111",
            "11110111111111110111",
            "11110111111111110111",
            "11110111111111110111",
            "10000111111111110001",
            "11110111111111110111",
            "11110111111111110111",
            "11110111111111110111",
            "11110000000000000111",
            "11111111111111111111",
            "11111111111111111111",
            "11111111111111111111"
        ]
    },
    # Level 4: The Spiral Trap (Updated)
    {
        "start_pos": (1.5, 1.5), "target_pos": (10.5, 7.5),
        "map": [
            "11111111111111111111",
            "10000000000000000001",
            "10111111111111111101",
            "10000000000000000101",
            "10101111111111110101",
            "101000000001111010101",
            "10101011100001010101",
            "10101010000001010101",
            "10101011111111010101",
            "10101000000000010101",
            "10101111111111110101",
            "10100000000000000101",
            "10111111111111111101",
            "10000000000000000001",
            "11111111111111111111"
        ]
    },
    # Level 5: The Final Maze (Updated)
    {
        "start_pos": (1.5, 1.5), "target_pos": (18.5, 13.5),
        "map": [
            "11111111111111111111",
            "10001000001000000001",
            "11101011101011101101",
            "10001010001010001001",
            "10111010111010101011",
            "10000010000010101001",
            "11111011111011101101",
            "10001000100000101001",
            "10111011101110101101",
            "10001010001000101001",
            "11101010111011101101",
            "10001010100010001001",
            "10111010111010111011",
            "10000000100000000001",
            "11111111111111111111"
        ]
    }
]


# Calculate the maximum possible distance in the game (the diagonal)
MAX_GAME_DIST = math.dist((0, 0), (WINDOW_WIDTH, WINDOW_HEIGHT))

# -- Haptic / AI Configuration --
JERK_THRESHOLD = 0.8  # You can tune this value

# --- 2. HELPER FUNCTIONS (From Report) ---

def calculate_proximity(user_pos, target_pos):
    """
    This is the "Proximity Module."
    Calculates Euclidean distance and maps it to a 0-255 intensity value.
    """
    distance = math.dist(user_pos, target_pos)
    norm_dist = 1.0 - (distance / MAX_GAME_DIST)
    intensity = int((norm_dist ** 2) * 255)
    return max(0, min(255, intensity))

def calculate_cognitive_load(current_x, current_y, last_x, last_y, last_vel_x, last_vel_y):
    """
    This is the "AI Module."
    Calculates kinematic jerk as a proxy for cognitive load.
    """
    vel_x = current_x - last_x
    vel_y = current_y - last_y
    accel_x = vel_x - last_vel_x
    accel_y = vel_y - last_vel_y
    jerk = math.dist((0, 0), (accel_x, accel_y))
    
    if jerk > JERK_THRESHOLD:
        state = "PULSE"  # "Uncertain"
    else:
        state = "STEADY" # "Focused"
        
    return state, jerk, vel_x, vel_y

def send_haptic_command(serial_conn, state, intensity):
    """
    Sends the final command (e.g., "STEADY,180") to the ESP8266.
    """
    if serial_conn:
        try:
            cmd = f"{state},{intensity}\n"
            serial_conn.write(cmd.encode()) # Send as bytes
        except serial.SerialException:
            # This can happen if the device is unplugged
            print("Serial write error")
            return

def build_wall_rects(game_map):
    """
    Helper function to create a list of wall rectangles from a map.
    """
    wall_rects = []
    for y_index, row in enumerate(game_map):
        for x_index, tile in enumerate(row):
            if tile == "1":
                wall_rects.append(
                    pygame.Rect(
                        x_index * TILE_SIZE, 
                        y_index * TILE_SIZE, 
                        TILE_SIZE, 
                        TILE_SIZE
                    )
                )
    return wall_rects

# --- 3. INITIALIZATION ---

# Initialize Pygame
pygame.init()
pygame.font.init()

# Set up the display
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption(GAME_TITLE)
clock = pygame.time.Clock()
debug_font = pygame.font.SysFont('Arial', 30) # Larger font
title_font = pygame.font.SysFont('Arial', 50)

# Initialize Joystick
joystick = None
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Joystick detected: {joystick.get_name()}")
else:
    print("No joystick detected. Using arrow keys as fallback.")

# Initialize Serial Connection
arduino = None
try:
    arduino = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=0.1)
    print(f"Successfully connected to {SERIAL_PORT}")
    time.sleep(2) # Give the ESP8266 time to boot
except serial.SerialException as e:
    print(f"--- WARNING: Could not connect to {SERIAL_PORT}. {e}")
    print("--- Running in software-only mode. ---")
except Exception as e:
    print(f"--- WARNING: An unexpected error occurred: {e}")
    print("--- Running in software-only mode. ---")

# --- 4. MAIN GAME LOOP ---

def main_game_loop():
    current_level_index = 0
    game_state = "RUNNING"  # "RUNNING", "LEVEL_CLEAR", "GAME_WIN"

    # --- Load Level Function ---
    def load_level(level_index):
        """Pulls all data for the new level and returns it."""
        level_info = LEVEL_DATA[level_index]
        current_map = level_info["map"]
        wall_rects = build_wall_rects(current_map)
        
        # Convert tile coordinates to pixel coordinates
        start_pos = [level_info["start_pos"][0] * TILE_SIZE, level_info["start_pos"][1] * TILE_SIZE]
        target_pos = [level_info["target_pos"][0] * TILE_SIZE, level_info["target_pos"][1] * TILE_SIZE]
        
        # Create player and target rectangles
        player_rect = pygame.Rect(start_pos[0] - PLAYER_RADIUS, 
                                  start_pos[1] - PLAYER_RADIUS, 
                                  PLAYER_RADIUS * 2, 
                                  PLAYER_RADIUS * 2)
        target_rect = pygame.Rect(target_pos[0] - 10, target_pos[1] - 10, 20, 20)
        
        return wall_rects, player_rect, target_pos, target_rect

    # --- Load the first level ---
    wall_rects, player_rect, target_pos, target_rect = load_level(current_level_index)
    
    # Joystick axis values
    joystick_x = 0.0
    joystick_y = 0.0
    
    # Kinematic history
    last_x, last_y = 0.0, 0.0
    last_vel_x, last_vel_y = 0.0, 0.0
    current_jerk = 0.0
    haptic_state = "STEADY"
    
    running = True
    while running:
        
        # --- A. Event Handling (Input) ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # --- B. Game Logic (Game Engine) ---
        
        if game_state == "RUNNING":
            # -- 1. Get Input --
            if joystick:
                joystick_x = joystick.get_axis(0)
                joystick_y = joystick.get_axis(1)
                if abs(joystick_x) < 0.1: joystick_x = 0
                if abs(joystick_y) < 0.1: joystick_y = 0
            else:
                keys = pygame.key.get_pressed()
                joystick_x = 0.0
                joystick_y = 0.0
                if keys[pygame.K_LEFT]: joystick_x = -1.0
                if keys[pygame.K_RIGHT]: joystick_x = 1.0
                if keys[pygame.K_UP]: joystick_y = -1.0
                if keys[pygame.K_DOWN]: joystick_y = 1.0

            # -- 2. Apply Movement & Check Collisions (X-Axis) --
            player_rect.x += joystick_x * USER_SPEED
            for wall in wall_rects:
                if player_rect.colliderect(wall):
                    if joystick_x > 0: player_rect.right = wall.left
                    if joystick_x < 0: player_rect.left = wall.right
            
            # -- 3. Apply Movement & Check Collisions (Y-Axis) --
            player_rect.y += joystick_y * USER_SPEED
            for wall in wall_rects:
                if player_rect.colliderect(wall):
                    if joystick_y > 0: player_rect.bottom = wall.top
                    if joystick_y < 0: player_rect.top = wall.bottom
            
            # Sync the visual position (center of the rect)
            user_pos = [player_rect.centerx, player_rect.centery]

            # -- 4. Check for Level Win Condition --
            if player_rect.colliderect(target_rect):
                game_state = "LEVEL_CLEAR"
                send_haptic_command(arduino, "STEADY", 255) # Give a solid buzz for winning
                
                screen.fill(COLOR_BACKGROUND)
                msg_sfc = title_font.render(f"Level {current_level_index + 1} Complete!", True, COLOR_USER)
                screen.blit(msg_sfc, (WINDOW_WIDTH // 2 - msg_sfc.get_width() // 2, WINDOW_HEIGHT // 2))
                pygame.display.flip()
                pygame.time.wait(2000) # Wait 2 seconds
                
                # Load next level
                current_level_index += 1
                if current_level_index >= len(LEVEL_DATA):
                    game_state = "GAME_WIN"
                else:
                    # Load new level data and reset player
                    wall_rects, player_rect, target_pos, target_rect = load_level(current_level_index)
                    game_state = "RUNNING"

            # --- C. Haptic Module (Software Side) ---
            
            proximity_intensity = calculate_proximity(user_pos, target_pos)
            
            haptic_state, current_jerk, vel_x, vel_y = calculate_cognitive_load(
                joystick_x, joystick_y, 
                last_x, last_y, 
                last_vel_x, last_vel_y
            )
            last_x, last_y = joystick_x, joystick_y
            last_vel_x, last_vel_y = vel_x, vel_y
            
            send_haptic_command(arduino, haptic_state, proximity_intensity)

            # --- D. Researcher UI Rendering ---
            
            screen.fill(COLOR_BACKGROUND)
            for wall in wall_rects:
                pygame.draw.rect(screen, COLOR_WALL, wall)
            
            pygame.draw.line(screen, COLOR_TARGET, (target_pos[0]-10, target_pos[1]-10), (target_pos[0]+10, target_pos[1]+10), 3)
            pygame.draw.line(screen, COLOR_TARGET, (target_pos[0]-10, target_pos[1]+10), (target_pos[0]+10, target_pos[1]-10), 3)
            
            pygame.draw.circle(screen, COLOR_USER, user_pos, PLAYER_RADIUS)
            
            # Draw Debug Panel (matches the report's UI)
            debug_text_lines = [
                f"Level: {current_level_index + 1} / {len(LEVEL_DATA)}",
                f"Proximity: {proximity_intensity}",
                f"AI State: {haptic_state}",
                f"Jerk: {current_jerk:.2f}",
                f"Haptic Command: {haptic_state},{proximity_intensity}"
            ]
            
            for i, line in enumerate(debug_text_lines):
                text_surface = debug_font.render(line, True, COLOR_TEXT)
                screen.blit(text_surface, (10, 10 + i * 30))
                
            pygame.display.flip()

        elif game_state == "GAME_WIN":
            # Show "Congratulations!" message (Updated)
            screen.fill(COLOR_BACKGROUND)
            
            # Title
            msg_sfc_1 = title_font.render("Congratulations!", True, COLOR_USER)
            msg_rect_1 = msg_sfc_1.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30))
            screen.blit(msg_sfc_1, msg_rect_1)
            
            # Subtitle
            msg_sfc_2 = debug_font.render("You have completed all levels!", True, COLOR_TEXT)
            msg_rect_2 = msg_sfc_2.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 30))
            screen.blit(msg_sfc_2, msg_rect_2)
            
            # Give a final buzz
            send_haptic_command(arduino, "PULSE", 200)
            
            pygame.display.flip()
            
            # Wait for quit
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
        
        clock.tick(60)

    # --- 5. CLEANUP ---
    print("Shutting down...")
    send_haptic_command(arduino, "OFF", 0) # Turn off motor
    if arduino:
        arduino.close()
    if joystick:
        joystick.quit()
    pygame.quit()

# --- Run the game ---
if __name__ == "__main__":
    main_game_loop()