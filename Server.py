import socket
import threading
import pickle
import numpy as np
import random

# Game settings
HOST = '0.0.0.0'  # Server binds to all available interfaces
PORT = 12345
players = {}
player_positions = {}
player_health = {}
traps = []
rubies = []
bullets = []
game_running = True
movement_logs = {}
trap_types = ["slow", "damage", "stun"]  # Different trap types

def handle_client(conn, addr):
    global game_running
    print(f"Connected by {addr}")
    players[addr] = conn
    player_positions[addr] = np.array([0.0, 0.0])  # Initialize player position
    player_health[addr] = 5  # Initialize player health

    while game_running:
        try:
            data = conn.recv(4096)
            if not data:
                break
            player_positions[addr], player_health[addr], bullets = pickle.loads(data)
            log_movement(addr, player_positions[addr])  # Log movement
            broadcast_game_state()
        except ConnectionResetError:
            break

    conn.close()
    del players[addr]
    del player_positions[addr]
    del player_health[addr]
    print(f"Disconnected {addr}")

def log_movement(addr, position):
    if addr not in movement_logs:
        movement_logs[addr] = []
    movement_logs[addr].append(position.tolist())  # Log as a list for easier serialization

def broadcast_game_state():
    game_state = (player_positions, player_health, traps, rubies, bullets, movement_logs)
    for player in players:
        try:
            data = pickle.dumps(game_state)
            players[player].sendall(data)
        except:
            pass

def spawn_ruby():
    ruby_position = np.array([random.uniform(-10, 10), random.uniform(-10, 10)])
    rubies.append(ruby_position)

def place_trap():
    trap_pos = np.array([random.uniform(-10, 10), random.uniform(-10, 10)])
    trap_type = random.choice(trap_types)
    traps.append((trap_pos, trap_type))

def check_bullet_collision():
    for bullet in bullets:
        for addr in player_positions.keys():
            if addr != 'J' and np.linalg.norm(player_positions[addr] - bullet) < 0.5:
                print(f"{addr} was hit by a bullet!")
                player_health[addr] -= 1  # Decrease health
                bullets.remove(bullet)  # Remove bullet after hit

def main():
    global game_running
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(10)  # Allow multiple connections
    print("Server started, waiting for players...")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

        if len(players) >= 2:
            print("Players connected, starting the game.")
            break

    # Randomly place multiple rubies
    for _ in range(5):  # Spawn 5 rubies at the start
        spawn_ruby()

    # Game loop
    while game_running:
        for addr in list(player_positions.keys()):
            # Check if Jussi has collected a ruby
            if addr == 'J':
                for ruby in rubies:
                    if np.linalg.norm(player_positions[addr] - ruby) < 0.5:
                        print(f"{addr} collected a ruby!")
                        rubies.remove(ruby)  # Remove collected ruby
                        spawn_ruby()  # Respawn ruby at a new location
                        break

            # Check for player health
            if player_health[addr] <= 0:
                print(f"{addr} has been eliminated.")
                player_positions[addr] = np.array([random.uniform(-10, 10), random.uniform(-10, 10)])  # Respawn
                player_health[addr] = 5  # Reset health

            # Check for traps
            for trap in traps:
                trap_pos, trap_type = trap
                if np.linalg.norm(player_positions[addr] - trap_pos) < 0.5:
                    print(f"{addr} stepped on a {trap_type} trap!")
                    if trap_type == "slow":
                        player_positions[addr] += (0.1, 0.1)  # Slow down effect
                    elif trap_type == "damage":
                        player_health[addr] -= 1  # Damage effect
                    elif trap_type == "stun":
                        print(f"{addr} is stunned!")
                    break

        check_bullet_collision()  # Check for bullet collisions

        # Randomly place traps periodically
        if random.random() < 0.1:
            place_trap()

    for conn in players.values():
        conn.close()

if __name__ == "__main__":
    main()
