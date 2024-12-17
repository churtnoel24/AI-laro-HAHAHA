import cv2
import numpy as np
import pygame
import random
import mediapipe as mp

# Initialize Pygame and OpenCV
pygame.init()
cap = cv2.VideoCapture(0)
cv2.setUseOptimized(True)
cv2.ocl.setUseOpenCL(True)

pygame.mixer.init()
pygame.mixer.music.load("assets/background_music.mp3")
crash_sound = pygame.mixer.Sound("assets/car-crash.mp3")


logo = pygame.image.load('assets/clearpath - logo.png')
pygame.display.set_icon(logo)
pygame.display.set_caption("ClearPath")
# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Load images
car_image = pygame.image.load('assets/car.png')
obstacle_images = [
    pygame.image.load('assets/bato.png'),
    pygame.image.load('assets/bitak.png')
]
background_image = pygame.image.load('assets/background.png')

# Resize images if necessary
car_image = pygame.transform.scale(car_image, (50, 100))
obstacle_images = [pygame.transform.scale(img, (50, 50)) for img in obstacle_images]
background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

# Car properties
car = pygame.Rect(WIDTH // 2 - 25, HEIGHT - 150, 50, 100)
base_car_speed = 5  # Base speed
steering_multiplier = 12  # Adjust this value for faster steering

# Obstacles
obstacles = [
    {
        "rect": pygame.Rect(random.randint(0, WIDTH - 50), -random.randint(50, 200), 50, 50),
        "image": random.choice(obstacle_images)
    }
    for _ in range(5)
]

# Background movement
bg_y = 0
bg_speed = 5

# Score and Speed Adjustment
score = 0
speed_increment_threshold = 500  # Increase speed every 500 points

# Initialize High Score
try:
    with open("highscore.txt", "r") as file:
        high_score = int(file.read())  # Read the value and convert it to an integer
except FileNotFoundError:
    high_score = 0  # If the file doesn't exist, start with 0

# Color range for hand detection
lower_color = np.array([0, 48, 80], dtype=np.uint8)
upper_color = np.array([20, 255, 255], dtype=np.uint8)


def draw_text(text, font, color, surface, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect(center=(x, y))
    surface.blit(textobj, textrect)

def show_menu():
    font = pygame.font.Font(None, 74)
    small_font = pygame.font.Font(None, 36)

    #Background Splash Art
    menu_image = pygame.image.load('assets/splashart.jpg')
    menu_image = pygame.transform.scale(menu_image, (WIDTH, HEIGHT))
    menu_image.set_alpha(100)
    while True:
        screen.fill((0, 0, 0))
        screen.blit(menu_image, (0, 0))  # Blit low-opacity image
        draw_text('Main Menu', font, (255, 255, 255), screen, WIDTH // 2, HEIGHT // 2 - 50)
        draw_text('Press P to Play', small_font, (255, 255, 255), screen, WIDTH // 2, HEIGHT // 2 + 50)
        draw_text('Press Q to Quit', small_font, (255, 255, 255), screen, WIDTH // 2, HEIGHT // 2 + 100)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:  # Start the game
                    return
                if event.key == pygame.K_q:  # Quit the game
                    pygame.quit()
                    exit()  # Start the game
        pygame.display.flip()
        clock.tick(30)

def handle_steering(steering_input):
    offset = abs(steering_input - 0.5)
    dynamic_speed = base_car_speed + int(steering_multiplier * offset)

    if steering_input < 0.4 and car.left > 0:  # Move left
        car.x -= dynamic_speed
    elif steering_input > 0.6 and car.right < WIDTH:  # Move right
        car.x += dynamic_speed

# Initialize Mediapipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7, model_complexity=0)
mp_drawing = mp.solutions.drawing_utils

def detect_hand_position(frame):
    global hands  # Use the initialized Mediapipe hands object

    # Convert the frame to RGB as required by Mediapipe
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    steering_input = 0.5  # Default to center (no movement)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Get the x-coordinate of the wrist (landmark 0)
            wrist_x = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x
            steering_input = wrist_x  # Normalize to [0, 1] as required

            # Draw hand landmarks on the OpenCV frame (optional for debugging)
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    return steering_input

def reset_game():
    global score, base_car_speed, bg_speed, obstacles
    score = 0
    base_car_speed = 5
    bg_speed = 5
    car.topleft = (WIDTH // 2 - 25, HEIGHT - 150)
    obstacles = [
        {
            "rect": pygame.Rect(random.randint(0, WIDTH - 50), -random.randint(50, 200), 50, 50),
            "image": random.choice(obstacle_images)
        }
        for _ in range(5)
    ]
def countdown():
    font = pygame.font.Font(None, 74)  # Large font for countdown
    countdown_duration = 3  # Countdown duration in seconds

    # Load the sound effect
    countdown_sound = pygame.mixer.Sound("assets/countdown_sound.mp3")

    for count in range(countdown_duration, 0, -1):  # Countdown from 3 to 1
        screen.fill((0, 0, 0))  # Black background
        draw_text(str(count), font, (255, 255, 255), screen, WIDTH // 2, HEIGHT // 2)

        # Play the sound effect
        countdown_sound.play()

        pygame.display.flip()
        pygame.time.wait(1000)  # Wait for 1 second

    # Show "GO!" before the game starts
    screen.fill((0, 0, 0))
    draw_text("GO!", font, (0, 255, 0), screen, WIDTH // 2, HEIGHT // 2)


    pygame.display.flip()
    pygame.time.wait(500)  # Wait for half a second


def main_game():
    global bg_y, score, base_car_speed, bg_speed

    countdown()  # Show countdown before starting the game
    running = True

    # Start playing the background music in a loop
    pygame.mixer.music.play(-1)  # -1 makes the music loop indefinitely

    # Floating text variables
    floating_text = None
    floating_text_timer = 0
    floating_text_position = (WIDTH // 2, HEIGHT // 3)  # Text position (adjust as needed)
    floating_text_duration = 60  # Duration to display text in frames (e.g., 60 frames = 2 seconds at 30 FPS)

    while running:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        steering_input = detect_hand_position(frame)
        handle_steering(steering_input)

        # Increment score continuously
        score += 1

        # Increase speed every 500 points
        if score % speed_increment_threshold == 0:
            base_car_speed += 1
            bg_speed += 1

            # Set floating text and timer
            floating_text = random.choice(["Great Job!", "Amazing!", "Keep Going!"])
            floating_text_timer = floating_text_duration

        # Move obstacles and check for collisions
        for obstacle in obstacles:
            obstacle["rect"].y += base_car_speed
            if obstacle["rect"].top > HEIGHT:
                obstacle["rect"].topleft = (random.randint(0, WIDTH - 50), -50)
                obstacle["image"] = random.choice(obstacle_images)

            if car.colliderect(obstacle["rect"]):
                crash_sound.play()
                show_game_over()
                running = False

        # Background scrolling
        bg_y += bg_speed
        if bg_y >= HEIGHT:
            bg_y = 0

        # Draw elements
        screen.blit(background_image, (0, bg_y))
        screen.blit(background_image, (0, bg_y - HEIGHT))
        screen.blit(car_image, car)
        for obstacle in obstacles:
            screen.blit(obstacle["image"], obstacle["rect"])

        # Display score
        font = pygame.font.Font(None, 36)
        draw_text(f"Score: {score}", font, (255, 255, 255), screen, 60, 30)
        draw_text(f"High Score: {high_score}", font,(255,255,255),screen, 650, 30)

        # Display floating text if active
        if floating_text and floating_text_timer > 0:
            draw_text(floating_text, pygame.font.Font(None, 74), (255, 255, 0), screen,
                      floating_text_position[0], floating_text_position[1])
            floating_text_timer -= 1  # Decrease timer

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        pygame.display.flip()
        clock.tick(30)

def show_game_over():
    global score, high_score

    pygame.mixer.music.stop()

    if score > high_score:
        high_score = score
        # Save the new high score to the file
        with open("highscore.txt", "w") as highscore_file:
            highscore_file.write(str(high_score))  # Write the high score as a string

    font = pygame.font.Font(None, 74)
    gameover_image = pygame.image.load('assets/gameover.jpg')
    gameover_image = pygame.transform.scale(gameover_image, (WIDTH, HEIGHT))
    gameover_image.set_alpha(100)
    screen.fill((0, 0, 0))
    screen.blit(gameover_image,(0,0))
    draw_text("Game Over", font, (255, 0, 0), screen, WIDTH // 2, HEIGHT // 2 - 100)
    draw_text(f"Final Score: {score}", pygame.font.Font(None, 50), (255, 255, 255), screen, WIDTH // 2,
              HEIGHT // 2 - 20)
    draw_text(f"High Score: {high_score}", pygame.font.Font(None, 50), (255, 255, 0), screen, WIDTH // 2,
              HEIGHT // 2 + 40)

    # Retry or Quit instructions
    draw_text("Press R to Retry or Q to Quit", pygame.font.Font(None, 36), (255, 255, 255), screen, WIDTH // 2,
              HEIGHT // 2 + 100)
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_game()
                    main_game()  # Restart game
                    waiting = False
                elif event.key == pygame.K_q:
                    pygame.quit()
                    exit()

# Show the menu and start the game
show_menu()
main_game()

# Release resources
cap.release()
cv2.destroyAllWindows()
pygame.quit()
