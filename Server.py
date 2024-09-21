import pygame
import socket
import pickle
import numpy as np

# Game settings
HOST = 'SERVER_IP_ADDRESS'  # Replace with the server's IP address
PORT = 12345

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Mörköpeli: Jussi vs Mörkö')

# Load images
player_texture = pygame.image.load('jussi.png')  # Load Jussi image
monster_texture = pygame.image.load('morko.png')  # Load Mörkö image
ruby_texture = pygame.image.load('ruby.png')  # Load ruby image
trap_texture = pygame.image.load('trap.png')  # Load trap image

# Initialize sound
pygame.mixer.init()
background_music = pygame.mixer.Sound('background_music.mp3')
background_music.play(-1)  # Loop the background music
collect_sound = pygame.mixer.Sound('collect.wav')  # Sound for collecting ruby
trap_sound = pygame.mixer.Sound('trap.wav')  # Sound for trap activation
shoot_sound = pygame.mixer.Sound('shoot.wav')  # Sound for shooting

# Initialize socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

player_type = input("Enter 'J' for Jussi, 'M' for Mörkö: ").strip().upper()
position = np.array([0.0, 0.0])
health = 5
flashlight_on = True
bullets = []  # List to hold bullet positions
movement_log = []

def update_position():
    global position
    data = pickle.dumps((position, health, bullets))
    sock.sendall(data)

def draw_flashlight():
    if flashlight_on:
        flashlight_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(flashlight_surface, (255, 255, 255, 150), (WIDTH // 2, HEIGHT // 2), 200)
        screen.blit(flashlight_surface, (0, 0))

def draw_ui():
    # Draw health bar
    pygame.draw.rect(screen, (255, 0, 0), (10, 10, 100, 10))  # Background
    pygame.draw.rect(screen, (0, 255, 0), (10, 10, 100 * (health / 5), 10))  # Health
    font = pygame.font.SysFont(None, 36)
    text = font.render(f'Health: {health}', True, (255, 255, 255))
    screen.blit(text, (120, 10))

def main():
    global position, health
    clock = pygame.time.Clock()
    players = {}
    traps = []
    rubies = []
    movement_log = []

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sock.close()
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:  # Toggle flashlight
                    flashlight_on = not flashlight_on
                if event.key == pygame.K_SPACE and player_type == 'J':  # Jussi shoots
                    bullet = position.copy()
                    bullets.append(bullet)  # Add bullet to the list
                    shoot_sound.play()  # Play shooting sound

        keys = pygame.key.get_pressed()
        if player_type == 'J':
            if keys[pygame.K_a]:
                position[0] -= 0.1
            if keys[pygame.K_d]:
                position[0] += 0.1
            if keys[pygame.K_w]:
                position[1] -= 0.1
            if keys[pygame.K_s]:
                position[1] += 0.1
        elif player_type == 'M':
            if players:
                jussi_position = players.get('J', np.array([0, 0]))
                direction = jussi_position - position
                if np.linalg.norm(direction) > 0:
                    direction /= np.linalg.norm(direction)  # Normalize
                    position += direction * 0.05  # Mörkö's speed

        # Update bullet positions
        for bullet in bullets:
            bullet[0] += 0.5  # Move bullet to the right

        update_position()

        # Receive updated positions and game state from server
        try:
            data = sock.recv(4096)
            players, traps, rubies, movement_logs = pickle.loads(data)
            if player_type in movement_logs:
                movement_log = movement_logs[player_type]  # Get own movement log
        except:
            pass

        screen.fill((0, 0, 0))  # Clear the screen
        draw_flashlight()  # Draw flashlight effect
        draw_ui()  # Draw the UI

        for addr, pos in players.items():
            if addr == player_type:  # Draw the controlled player
                screen.blit(player_texture, (pos[0] + WIDTH // 2 - 25, pos[1] + HEIGHT // 2 - 25))
            else:  # Draw the monster
                screen.blit(monster_texture, (pos[0] + WIDTH // 2 - 25, pos[1] + HEIGHT // 2 - 25))

        # Draw rubies
        for ruby in rubies:
            screen.blit(ruby_texture, (ruby[0] + WIDTH // 2 - 15, ruby[1] + HEIGHT // 2 - 15))

        # Draw traps
        for trap_pos, trap_type in traps:
            screen.blit(trap_texture, (trap_pos[0] + WIDTH // 2 - 10, trap_pos[1] + HEIGHT // 2 - 10))

        # Draw bullets
        for bullet in bullets:
            pygame.draw.circle(screen, (255, 255, 0), (bullet[0] + WIDTH // 2, bullet[1] + HEIGHT // 2), 5)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
