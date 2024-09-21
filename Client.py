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
        self.path = []
        self.team = team

    def move(self):
        if self.path:
            next_pos = self.path.pop(0)
            self.x, self.y = next_pos[0] * TROOP_SIZE, next_pos[1] * TROOP_SIZE

    def draw(self, screen):
        color = TROOP_TYPES[self.troop_type]['color']
        pygame.draw.rect(screen, color, (self.x, self.y, TROOP_SIZE, TROOP_SIZE))
        if self.selected:
            pygame.draw.rect(screen, GREEN, (self.x, self.y, TROOP_SIZE, TROOP_SIZE), 2)
        pygame.draw.rect(screen, RED, (self.x, self.y - 10, TROOP_SIZE, 5))
        pygame.draw.rect(screen, GREEN, (self.x, self.y - 10, TROOP_SIZE * (self.health / TROOP_HEALTH), 5))

    def attack(self, other):
        if self.health > 0 and other.health > 0:
            distance = ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
            if distance < TROOP_TYPES[self.troop_type]['range']:
                other.health -= TROOP_TYPES[self.troop_type]['damage']

def ai_behavior(ai_troops, enemy_troops):
    for ai in ai_troops:
        if ai.health > 0:
            # AI selects the closest enemy
            target = min((troop for troop in enemy_troops if troop.health > 0), key=lambda t: ((t.x - ai.x) ** 2 + (t.y - ai.y) ** 2) ** 0.5, default=None)
            if target:
                if ai.x < target.x:
                    ai.x += TROOP_TYPES[ai.troop_type]['speed']
                elif ai.x > target.x:
                    ai.x -= TROOP_TYPES[ai.troop_type]['speed']
                if ai.y < target.y:
                    ai.y += TROOP_TYPES[ai.troop_type]['speed']
                elif ai.y > target.y:
                    ai.y -= TROOP_TYPES[ai.troop_type]['speed']
                ai.attack(target)

# Connect to server
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 12345))

# Determine team based on connection order
team = 1 if client_socket.recv(1) == b'1' else 2

# Create player and AI troops
if team == 1:
    player_troops = [Troop(random.randint(0, 15) * TROOP_SIZE, random.randint(0, 10) * TROOP_SIZE, random.choice(['infantry', 'archer', 'cavalry']), team) for _ in range(3)]
    ai_troops = [Troop(random.randint(0, 15) * TROOP_SIZE, random.randint(0, 10) * TROOP_SIZE, random.choice(['infantry', 'archer', 'cavalry']), team) for _ in range(2)]
else:
    player_troops = [Troop(random.randint(16, 30) * TROOP_SIZE, random.randint(0, 10) * TROOP_SIZE, random.choice(['infantry', 'archer', 'cavalry']), team) for _ in range(3)]
    ai_troops = [Troop(random.randint(16, 30) * TROOP_SIZE, random.randint(0, 10) * TROOP_SIZE, random.choice(['infantry', 'archer', 'cavalry']), team) for _ in range(2)]

# Main game loop
running = True
selected_troop = None
while running:
    pygame.time.delay(100)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for troop in player_troops:
                if troop.x < mouse_pos[0] < troop.x + TROOP_SIZE and troop.y < mouse_pos[1] < troop.y + TROOP_SIZE:
                    selected_troop = troop
                    troop.selected = True
                    troop.path = []  # Clear any existing path
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

    # AI troop behavior
    ai_behavior(ai_troops, game_state['team_2_troops'] if team == 1 else game_state['team_1_troops'])

    # Player troop attack
    for player in player_troops:
        for enemy in (game_state['team_2_troops'] if team == 1 else game_state['team_1_troops']):
            player.attack(enemy)

    # Send player and AI troops data to the server
    try:
        data_to_send = {'team_1_troops' if team == 1 else 'team_2_troops': [(troop.x, troop.y, troop.troop_type, troop.health) for troop in player_troops + ai_troops]}
        client_socket.sendall(pickle.dumps(data_to_send))
    except:
        print("Server disconnected")
        break

    # Receive game state from the server
    try:
        game_state_data = client_socket.recv(4096)
        game_state = pickle.loads(game_state_data)
    except:
        continue

    # Update and draw game state
    screen.fill(WHITE)
    for troop in player_troops + ai_troops:
        troop.draw(screen)
    for troop_data in (game_state['team_2_troops'] if team == 1 else game_state['team_1_troops']):
        enemy_troop = Troop(*troop_data, team=2 if team == 1 else 1)
        enemy_troop.draw(screen)
    for obs in game_state['obstacles']:
        pygame.draw.rect(screen, BROWN, (obs[0] * TROOP_SIZE, obs[1] * TROOP_SIZE, TROOP_SIZE, TROOP_SIZE))
    for point in game_state['strategic_points']:
        pygame.draw.circle(screen, GREEN, (point[0] * TROOP_SIZE + TROOP_SIZE // 2, point[1] * TROOP_SIZE + TROOP_SIZE // 2), TROOP_SIZE // 2)
    pygame.display.update()

pygame.quit()
client_socket.close()
