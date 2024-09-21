import pygame
import socket
import pickle
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Advanced 2D Multiplayer Troop Control Game")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19)

# Troop properties
TROOP_SIZE = 20
TROOP_HEALTH = 100

# Troop types
TROOP_TYPES = {
    'infantry': {'range': 30, 'damage': 10, 'speed': 3, 'color': BLUE},
    'archer': {'range': 60, 'damage': 5, 'speed': 2, 'color': YELLOW},
    'cavalry': {'range': 20, 'damage': 15, 'speed': 5, 'color': RED}
}

# Troop class
class Troop:
    def __init__(self, x, y, troop_type, team):
        self.x = x
        self.y = y
        self.troop_type = troop_type
        self.health = TROOP_HEALTH
        self.selected = False
        self.team = team

    def draw(self, screen):
        color = TROOP_TYPES[self.troop_type]['color']
        pygame.draw.rect(screen, color, (self.x, self.y, TROOP_SIZE, TROOP_SIZE))
        if self.selected:
            pygame.draw.rect(screen, GREEN, (self.x, self.y, TROOP_SIZE, TROOP_SIZE), 2)
        pygame.draw.rect(screen, RED, (self.x, self.y - 10, TROOP_SIZE, 5))
        pygame.draw.rect(screen, GREEN, (self.x, self.y - 10, TROOP_SIZE * (self.health / TROOP_HEALTH), 5))

# Connect to server
try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 12345))
    print("Connected to server")
except Exception as e:
    print(f"Failed to connect to server: {e}")

# Example team assignment
team = 1

# Create player and AI troops
player_troops = [Troop(random.randint(0, 15) * TROOP_SIZE, random.randint(0, 10) * TROOP_SIZE, random.choice(['infantry', 'archer', 'cavalry']), team) for _ in range(5)]

# Main game loop
running = True
selected_troop = None
while running:
    pygame.time.delay(100)
    try:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for troop in player_troops:
                    if troop.x < mouse_pos[0] < troop.x + TROOP_SIZE and troop.y < mouse_pos[1] < troop.y + TROOP_SIZE:
                        selected_troop = troop
                        troop.selected = True
                    else:
                        troop.selected = False

        # Handle troop movement
        keys = pygame.key.get_pressed()
        if selected_troop:
            if keys[pygame.K_LEFT]:
                selected_troop.x -= TROOP_TYPES[selected_troop.troop_type]['speed']
            if keys[pygame.K_RIGHT]:
                selected_troop.x += TROOP_TYPES[selected_troop.troop_type]['speed']
            if keys[pygame.K_UP]:
                selected_troop.y -= TROOP_TYPES[selected_troop.troop_type]['speed']
            if keys[pygame.K_DOWN]:
                selected_troop.y += TROOP_TYPES[selected_troop.troop_type]['speed']

        # Send player troops data to the server
        try:
            data_to_send = {'team_1_troops': [(troop.x, troop.y, troop.troop_type, troop.health) for troop in player_troops]}
            client_socket.sendall(pickle.dumps(data_to_send))
        except Exception as e:
            print(f"Failed to send data to server: {e}")

        # Receive game state from the server
        try:
            game_state_data = client_socket.recv(4096)
            game_state = pickle.loads(game_state_data)
        except Exception as e:
            print(f"Failed to receive data from server: {e}")
            continue

        # Update and draw game state
        screen.fill(WHITE)
        for troop in player_troops:
            troop.draw(screen)
        for troop_data in game_state.get('team_2_troops', []):
            enemy_troop = Troop(*troop_data, team=2)
            enemy_troop.draw(screen)
        pygame.display.update()

    except Exception as e:
        print(f"An error occurred: {e}")
        running = False

pygame.quit()
client_socket.close()
