import cv2
import numpy as np
import pygame
import random

# Initialize Pygame and OpenCV
pygame.init()
cap = cv2.VideoCapture(0)

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Load images
car_image = pygame.image.load('car.png')  # Replace with your car image path
obstacle_image = pygame.image.load('obstacle.png')  # Replace with your obstacle image path
background_image = pygame.image.load('background.png')  # Replace with your background image path

# Resize images if necessary
car_image = pygame.transform.scale(car_image, (50, 100))
obstacle_image = pygame.transform.scale(obstacle_image, (50, 50))
background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

# Car properties
car = pygame.Rect(WIDTH // 2 - 25, HEIGHT - 150, 50, 100)
car_speed = 5

# Track and Obstacles
obstacles = [pygame.Rect(random.randint(0, WIDTH - 50), -random.randint(50, 200), 50, 50) for _ in range(5)]

# Background movement
bg_y = 0
bg_speed = 5

# Color range for hand detection
lower_color = np.array([0, 48, 80], dtype=np.uint8)
upper_color = np.array([20, 255, 255], dtype=np.uint8)

def draw_text(text, font, color, surface, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.center = (x, y)
    surface.blit(textobj, textrect)

def show_menu():
    font = pygame.font.Font(None, 74)
    small_font = pygame.font.Font(None, 36)
    while True:
        screen.fill((0, 0, 0))
        draw_text('Main Menu', font, (255, 255, 255), screen, WIDTH // 2, HEIGHT // 2 - 50)
        draw_text('Press P to Play', small_font, (255, 255, 255), screen, WIDTH // 2, HEIGHT // 2 + 50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    return  # Start the game

        pygame.display.flip()
        clock.tick(30)

# Show the menu before starting the game
show_menu()

# Main game loop
running = True
while running:
    # Handle OpenCV
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame.")
        break

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_color, upper_color)
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    steering_input = 0.5  # Default to center (no movement)
    if contours:
        max_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(max_contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Convert hand position to steering input
        steering_input = (x + w // 2) / frame.shape[1]

    cv2.imshow("Webcam Feed", frame)

    # Map steering input to car movement
    if steering_input < 0.4 and car.left > 0:  # Move left
        car.move_ip(-car_speed, 0)
    elif steering_input > 0.6 and car.right < WIDTH:  # Move right
        car.move_ip(car_speed, 0)

    # Move obstacles
    for obstacle in obstacles:
        obstacle.move_ip(0, car_speed)
        if obstacle.top > HEIGHT:
            obstacle.topleft = (random.randint(0, WIDTH - 50), -50)

    # Check for collisions
    for obstacle in obstacles:
        if car.colliderect(obstacle):
            print("Collision detected!")
            running = False

    # Handle Pygame
    screen.fill((0, 0, 0))  # Clear the screen with a black background

    # Move the background
    bg_y += bg_speed
    if bg_y >= HEIGHT:
        bg_y = 0

    # Draw the background
    screen.blit(background_image, (0, bg_y))
    screen.blit(background_image, (0, bg_y - HEIGHT))  # Draw the background image again to create a seamless loop

    # Draw the car and obstacles
    screen.blit(car_image, car)
    for obstacle in obstacles:
        screen.blit(obstacle_image, obstacle)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()
    clock.tick(30)

# Release resources
cap.release()
cv2.destroyAllWindows()
pygame.quit()