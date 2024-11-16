import cv2
import numpy as np
import pygame
import random

# Initialize Pygame and OpenCV
pygame.init()
cap = cv2.VideoCapture(0)

logo = pygame.image.load('clearpath - logo.png')
pygame.display.set_icon(logo)
pygame.display.set_caption("ClearPath")
# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Load images
car_image = pygame.image.load('car.png')
obstacle_images = [
    pygame.image.load('bato.png'),
    pygame.image.load('bitak.png')
]
background_image = pygame.image.load('background.png')

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
    menu_image = pygame.image.load('splashart.jpg')
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

def detect_hand_position(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_color, upper_color)
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    steering_input = 0.5  # Default to center (no movement)
    if contours:
        max_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(max_contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        steering_input = (x + w // 2) / frame.shape[1]
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

def main_game():
    global bg_y, score, base_car_speed, bg_speed
    running = True
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

        # Move obstacles and check for collisions
        for obstacle in obstacles:
            obstacle["rect"].y += base_car_speed
            if obstacle["rect"].top > HEIGHT:
                obstacle["rect"].topleft = (random.randint(0, WIDTH - 50), -50)
                obstacle["image"] = random.choice(obstacle_images)

            if car.colliderect(obstacle["rect"]):
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

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        pygame.display.flip()
        clock.tick(30)

def show_game_over():
    global score, high_score

    if score > high_score:
        high_score = score
        # Save the new high score to the file
        with open("highscore.txt", "w") as highscore_file:
            highscore_file.write(str(high_score))  # Write the high score as a string

    font = pygame.font.Font(None, 74)
    gameover_image = pygame.image.load('gameover.jpg')
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
