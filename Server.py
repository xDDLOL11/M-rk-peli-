import socket
import threading
import pickle
import random

# Server configuration
HOST = 'localhost'
PORT = 12345

# Troop properties
TROOP_SIZE = 20
TROOP_HEALTH = 100

# Troop types
TROOP_TYPES = {
    'infantry': {'range': 30, 'damage': 10, 'speed': 3},
    'archer': {'range': 60, 'damage': 5, 'speed': 2},
    'cavalry': {'range': 20, 'damage': 15, 'speed': 5}
}

# Game state
game_state = {
    'team_1_troops': [
        {'x': random.randint(0, 15) * TROOP_SIZE, 'y': random.randint(0, 10) * TROOP_SIZE, 'troop_type': random.choice(['infantry', 'archer', 'cavalry']), 'health': TROOP_HEALTH}
        for _ in range(5)
    ],
    'team_2_troops': [
        {'x': random.randint(16, 30) * TROOP_SIZE, 'y': random.randint(0, 10) * TROOP_SIZE, 'troop_type': random.choice(['infantry', 'archer', 'cavalry']), 'health': TROOP_HEALTH}
        for _ in range(5)
    ],
    'obstacles': [
        (random.randint(5, 25), random.randint(0, 15)) for _ in range(10)
    ],
    'strategic_points': [
        (random.randint(5, 25), random.randint(0, 15)) for _ in range(3)
    ]
}

def handle_client(client_socket, address, team):
    print(f"Connection from {address} has been established!")
    while True:
        try:
            # Receive data from the client
            data = client_socket.recv(4096)
            if not data:
                break

            # Deserialize received data
            player_data = pickle.loads(data)
            if team == 1:
                game_state['team_1_troops'] = player_data['team_1_troops']
            else:
                game_state['team_2_troops'] = player_data['team_2_troops']

            # Send updated game state to client
            client_socket.sendall(pickle.dumps(game_state))

        except Exception as e:
            print(f"Error: {e}")
            break

    client_socket.close()
    print(f"Connection from {address} has been closed.")

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(2)  # Listen for up to 2 clients
    print(f"Server listening on {HOST}:{PORT}")

    team = 1
    while True:
        client_socket, address = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, address, team))
        client_thread.start()
        team = 2 if team == 1 else 1

if __name__ == '__main__':
    start_server()
