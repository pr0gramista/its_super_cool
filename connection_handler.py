import json

from hero import Hero
from vector import Vector


class ConnectionHandler():
    def __init__(self, sock):
        self.sock = sock
        self.game = None
        self.id = 0

    def send(self, data):
        message = json.dumps(data).encode('utf-8')
        length = len(message).to_bytes(4, byteorder='big')
        self.sock.send(length + message)

    def join(self, name, input_handler, team):
        self.name = name
        self.input_handler = input_handler

        self.send({
            'operation': 'join',
            'name': name,
            'team': team
        })

    def grab(self, hero):
        self.send({
            'operation': 'grab',
            'id': hero.id
        })

    def throw(self, hero, power):
        self.send({
            'operation': 'throw',
            'id': hero.id,
            'vel_x': hero.velocity.x,
            'vel_y': hero.velocity.y,
            'vel_z': hero.velocity.z,
            'power': power
        })

    def throwing(self, hero, hold):
        self.send({
            'operation': 'throwing',
            'id': hero.id,
            'hold': hold
        })

    def beat(self, hero):
        self.send({
            'operation': 'beat',
            'id': hero.id
        })

    def handle(self):
        while True:
            try:
                length_bytes = self.sock.recv(4)
                length = int.from_bytes(length_bytes, byteorder='big')
                data = self.sock.recv(length)
                while len(data) < length:
                    data += self.sock.recv(length - len(data))
                if data:
                    data = json.loads(data, encoding='utf-8')
                    if 'operation' in data and len(data['operation']) > 0:
                        getattr(self, 'handle_' + data['operation'])(data)
                else:
                    raise ('Client disconnected')
            except ConnectionResetError:  # Todo
                self.sock.close()
                return False

    def handle_joined(self, data):
        print('Joined as {} (id: {})!'.format(self.name, data['id']))
        self.id = data['id']
        self.game.local_players.append(self.id)

        am_i_clone = self.game.get_hero(data['id'])
        if am_i_clone is not None:
            self.game.heroes.remove(am_i_clone)

        name = self.name
        input_handler = self.input_handler
        id = data['id']
        position = Vector(data['x'], data['y'], data['z'])
        team = data['team']

        new_hero = Hero(id, team)
        new_hero.name = name
        new_hero.position = position
        new_hero.input_handler = input_handler
        new_hero.connection_handler = self
        new_hero.game = self.game

        input_handler.id = id
        input_handler.hero = new_hero
        input_handler.connection_handler = self
        input_handler.game = self.game

        self.game.heroes.append(new_hero)
        self.game.input_handlers.append(input_handler)

    def handle_player_joined(self, data):
        if not self.game.is_local_player_id(data['id']):
            name = data['name']
            id = data['id']
            position = Vector(data['x'], data['y'], data['z'])
            team = data['team']

            #am_i_clone = self.game.get_hero(data['id'])
            #if am_i_clone is not None:
            #    self.game.heroes.remove(am_i_clone)

            print('Player {} (id: {}) joined'.format(name, id))

            new_hero = Hero(id, team)
            new_hero.name = name
            new_hero.position = position

            self.game.heroes.append(new_hero)

    def handle_player_moved(self, data):
        if self.game.is_local_player_id(data['id']) == False:
            hero = self.game.get_hero(data['id'])
            if hero:
                hero.position.x = data['x']
                hero.position.y = data['y']
                hero.position.z = data['z']
                hero.movement.x = data['vel_x']
                hero.movement.y = data['vel_y']
                hero.movement.z = data['vel_z']

    def handle_update_ball(self, data):
        ball = self.game.ball
        ball.position.x = data['x']
        ball.position.y = data['y']
        ball.position.z = data['z']
        ball.velocity.x = data['vel_x']
        ball.velocity.y = data['vel_y']
        ball.velocity.z = data['vel_z']

    def handle_ball_grabbed(self, data):
        hero = self.game.get_hero(data['id'])

        ball = self.game.ball
        ball.grabbed = True
        ball.grabbed_by = hero
        hero.holds_ball = True

        self.game.play_sound('hit2')

    def handle_ball_thrown(self, data):
        ball = self.game.ball
        ball.grabbed = False
        ball.grabbed_by = None

        for hero in self.game.heroes:
            hero.holds_ball = False
            hero.throws = False
            hero.hold = 0

        ball.velocity.x = data['vel_x']
        ball.velocity.y = data['vel_y']
        ball.velocity.z = data['vel_z']

        self.game.play_sound('swish')

    def handle_goal(self, data):
        if data['team'] == 0:
            self.game.points_astronauts = data['points']
        elif data['team'] == 1:
            self.game.points_aliens = data['points']
        self.game.play_sound('goal')

    def handle_player_throwing(self, data):
        hero = self.game.get_hero(data['id'])
        hero.throws = True
        hero.hold = data['hold']

        self.game.play_sound('swish')

    def handle_stun(self, data):
        hero = self.game.get_hero(data['id'])
        hero.stun(data['duration'])
        self.game.play_sound('stun')

    def handle_player_stunned(self, data):
        hero = self.game.get_hero(data['id'])
        hero.stun(data['duration'])
        self.game.play_sound('stun')

    def handle_play_sound(self, data):
        self.game.play_sound(data['sound'])

    def handle_player_disconnected(self, data):
        print('Player {} (id: {}) disconnected'.format(data['name'], data['id']))
        hero = self.game.get_hero(data['id'])
        self.game.heroes.remove(hero)
