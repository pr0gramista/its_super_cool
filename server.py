import json
import socket
import threading
import utils
import random
import pygame

from common.vector import Vector

current_id = 0


def get_id():
    global current_id
    current_id += 1
    return current_id


def get_smaller_team(players):
    red_team = [player for player in players if player.team == 0]
    blue_team = [player for player in players if player.team == 1]

    if len(red_team) > len(blue_team):
        return blue_team
    elif len(blue_team) > len(red_team):
        return red_team
    else:
        return random.choice([0, 1])  # Red or blue


class Ball():
    def __init__(self):
        self.position = Vector(0, 0, 0)
        self.velocity = Vector(0, 0, 0)
        self.grabbed = False
        self.grabbed_by = None
        self.__slow_factor_ground__ = 1.5

    def __slow_ground__(self, delta):
        self.velocity.x = self.__slow_single__(delta, self.velocity.x, self.__slow_factor_ground__)
        self.velocity.y = self.__slow_single__(delta, self.velocity.y, self.__slow_factor_ground__)
        self.velocity.z = self.__slow_single__(delta, self.velocity.z, self.__slow_factor_ground__)

    def update(self, delta):
        if self.grabbed == False:
            self.velocity.z -= delta * utils.gravity

            if self.position.z - 0.1 <= 0:
                self.__slow_ground__(delta)

            self.position.x += delta * self.velocity.x
            self.position.y += delta * self.velocity.y
            self.position.z += delta * self.velocity.z

            bounce_x, bounce_y, bounce_z = utils.bounce_to_map(*self.position.xyz())
            self.position.x, self.position.y, self.position.z = utils.cut_to_map(*self.position.xyz())

            self.velocity.x *= bounce_x
            self.velocity.y *= bounce_y
            self.velocity.z *= bounce_z
        else:
            self.position.x = self.grabbed_by.position.x
            self.position.y = self.grabbed_by.position.y
            self.position.z = self.grabbed_by.position.z + 0.25

    def __slow_single__(self, delta, v, slow_factor):
        if v > 0:
            v -= slow_factor * delta
            if v < 0:
                v = 0
        else:
            v += slow_factor * delta
            if v > 0:
                v = 0
        return 0

    def is_in_ring(self):
        return False


class PlayerHandler():
    def __init__(self, sock, server):
        self.sock = sock
        self.server = server
        self.legal_ids = []

        # Player data
        self.name = ''
        self.id = get_id()
        self.team = get_smaller_team(server.players)
        self.position = Vector(0, 0, 0)
        self.velocity = Vector(0, 0, 0)

    def error_me(self, data):
        print('Unrecognized operation {}'.format(data))

    def send(self, data):
        message = json.dumps(data).encode('utf-8')
        length = len(message).to_bytes(4, byteorder='big')
        try:
            self.sock.send(length + message)
        except ConnectionResetError:
            print('Player {} (id: {}) has suddenly disconnected.')

    def handle(self):
        while True:
            try:
                length = self.sock.recv(4)
                data = self.sock.recv(int.from_bytes(length, byteorder='big'))
                if data:
                    data = json.loads(data, encoding='utf-8')
                    if 'operation' in data and len(data['operation']) > 0:
                        getattr(self, 'handle_' + data['operation'])(data)
                else:
                    raise ('Client disconnected')
            except ConnectionResetError:
                print('Player {} (id: {}) disconnected'.format(self.name, self.id))
                self.server.players.remove(self)
                self.sock.close()
                return False

    def handle_join(self, data):
        self.name = data['name']

        self.server.tell_others(self, {
            'operation': 'player_joined',
            'id': self.id,
            'name': self.name,
            'team': self.team,
            'x': 0,
            'y': 0,
            'z': 0
        })

        self.send({
            'operation': 'joined',
            'name': self.name,
            'id': self.id,
            'team': self.team,
            'x': 0,
            'y': 0,
            'z': 0
        })

        # Send already existing players
        for player in self.server.players:
            if player is not self:
                print("id {} to id {}".format(player.id, self.id))
                self.send({
                    'operation': 'player_joined',
                    'name': player.name,
                    'id': player.id,
                    'team': player.team,
                    'x': player.position.x,
                    'y': player.position.y,
                    'z': player.position.z
                })
        print('Player {} (id: {}) joined the game'.format(self.name, self.id))

    def handle_move(self, data):
        self.position.x = data['x']
        self.position.y = data['y']
        self.position.z = data['z']
        self.velocity.x = data['vel_x']
        self.velocity.y = data['vel_y']
        self.velocity.z = data['vel_z']

        self.server.tell_others(self, {
            'operation': 'player_moved',
            'id': self.id,
            'x': self.position.x,
            'y': self.position.y,
            'z': self.position.z,
            'vel_x': self.velocity.x,
            'vel_y': self.velocity.y,
            'vel_z': self.velocity.z,
        })

    def handle_grab(self, data):
        if self.server.ball.grabbed == False and self.server.ball.position.dist(self.position) < 0.22:
            self.server.ball.grabbed = True
            self.server.ball.grabbed_by = self
            self.server.tell_everyone({
                'operation': 'ball_grabbed',
                'id': self.id
            })

    def handle_throw(self, data):
        if self.server.ball.grabbed and self.server.ball.grabbed_by == self.server.get_player_by_id(data['id']):
            self.server.ball.grabbed = False
            self.server.ball.grabbed_by = None

            self.server.ball.velocity.x = data['vel_x'] * (1 + data['power'] * 3)
            self.server.ball.velocity.y = data['vel_y'] * (1 + data['power'] * 3)
            self.server.ball.velocity.z = 0.25 * (1 + data['power'])

            self.server.tell_everyone({
                'operation': 'ball_thrown',
                'id': self.id,
                'vel_x': self.server.ball.velocity.x,
                'vel_y': self.server.ball.velocity.y,
                'vel_z': self.server.ball.velocity.z
            })


class Server():
    def __init__(self):
        self.players = []
        self.ball = Ball()
        self.blue_score = 0
        self.red_score = 0
        self.time = 0

        self.time_limit = 900
        self.score_limit = 9

        self.stage = 'LOBBY'

        host = ''
        port = 9525

        print("It's Super Cool Server")
        print('Listening at {}:{}'.format(host, port))

        self.server_socket = socket.socket()
        self.server_socket.bind((host, port))
        self.server_socket.listen()

        threading.Thread(target=self.game_logic).start()

    def get_player_by_id(self, id):
        for player in self.players:
            if player.id == id:
                return player
        return None

    def game_logic(self):
        clock = pygame.time.Clock()

        last_update = 0
        while True:
            tick = clock.tick(250)
            delta = tick / 1000

            self.ball.update(delta)

            last_update += tick
            if (last_update > 20):
                last_update = 0
                self.tell_everyone({
                    'operation': 'update_ball',
                    'x': self.ball.position.x,
                    'y': self.ball.position.y,
                    'z': self.ball.position.z,
                    'vel_x': self.ball.velocity.x,
                    'vel_y': self.ball.velocity.y,
                    'vel_z': self.ball.velocity.z
                })

    def run(self):
        while True:
            sock, address = self.server_socket.accept()
            sock.settimeout(60)

            new_player = PlayerHandler(sock, self)
            self.players.append(new_player)

            threading.Thread(target=new_player.handle).start()

    def tell_everyone(self, data):
        for player in self.players:
            player.send(data)

    def tell_others(self, origin, data):
        for player in self.players:
            if player is not origin:
                player.send(data)


if __name__ == "__main__":
    server = Server()
    server.run()
