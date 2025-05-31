import random
import math
import pgzrun
from pygame import Rect

WIDTH = 800
HEIGHT = 450

game_state = 'menu'  # estados: menu, playing
sound_on = False
damage_pending = False
game_message = ""

# Botões do menu
start_button = Rect((WIDTH // 2 - 80, 150), (140, 35))
sound_button = Rect((WIDTH // 2 - 70, 210), (140, 35))
exit_button = Rect((WIDTH // 2 - 80, 270), (140, 35))


def rects_collide(x1, y1, w1, h1, x2, y2, w2, h2):
    """Colisão retangular (AABB)."""
    return (
        x1 < x2 + w2 and
        x1 + w1 > x2 and
        y1 < y2 + h2 and
        y1 + h1 > y2
    )


class Portal:
    def __init__(self, pos):
        self.x, self.y = pos
        self.opened = False

    def draw(self):
        sprite = 'portal_open' if self.opened else 'portal_closed'
        screen.blit(sprite, (self.x, self.y))

    def collide(self, hero):
        return abs(hero.x - self.x) < 40 and abs(hero.y - self.y) < 40


class Platform:
    def __init__(self, x, y, w):
        self.x = x
        self.y = y
        self.w = w

    def draw(self):
        for i in range(self.w // 40):
            screen.blit('platform', (self.x + i * 40, self.y))

    def collide(self, x, y, w, h):
        return (
            x + w > self.x and x < self.x + self.w and
            y + h > self.y and y < self.y + 20
        )


class Key:
    def __init__(self, pos):
        self.x, self.y = pos
        self.collected = False

    def draw(self):
        if not self.collected:
            screen.blit('key', (self.x, self.y))

    def collide(self, hero):
        return abs(hero.x - self.x) < 30 and abs(hero.y - self.y) < 30


class Hero:
    def __init__(self, pos):
        self.x, self.y = pos
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.state = 'idle'  # idle, run, jump
        self.anim_timer = 0
        self.anim_index = 0
        self.direction = 1  # 1: right, -1: left
        self.sprites = {
            'idle': ['hero_idle_1', 'hero_idle_2', 'hero_idle_3'],
            'run': ['hero_run_1', 'hero_run_2', 'hero_run_3'],
            'jump': ['hero_jump_1'],
            'idle_left': [
                'hero_idle_left_1', 'hero_idle_left_2', 'hero_idle_left_3'
            ],
            'run_left': [
                'hero_run_left_1', 'hero_run_left_2', 'hero_run_left_3'
            ],
            'jump_left': ['hero_jump_left_1']
        }

    def update(self, platforms):
        keys = keyboard
        self.vx = 0
        if keys.left:
            self.vx = -4
            self.direction = -1
        if keys.right:
            self.vx = 4
            self.direction = 1

        # Movement state
        if self.vx != 0 and self.on_ground:
            self.state = 'run'
        elif self.on_ground:
            self.state = 'idle'

        if keys.up and self.on_ground:
            self.vy = -12
            self.on_ground = False
            self.state = 'jump'

        self.vy += 0.6
        if self.vy > 10:
            self.vy = 10
        self.x += self.vx
        self.y += self.vy
        self.on_ground = False
        for plat in platforms:
            if plat.collide(self.x, self.y + 32, 32, 32) and self.vy >= 0:
                self.y = plat.y - 32
                self.vy = 0
                self.on_ground = True
                if self.state == 'jump':
                    self.state = 'idle'

        # Animation
        self.anim_timer += 1
        if self.state == 'idle':
            if self.anim_timer > 10:
                self.anim_timer = 0
                self.anim_index = (
                    self.anim_index + 1
                ) % len(self.sprites['idle'])
        elif self.state == 'run':
            if self.anim_timer > 6:
                self.anim_timer = 0
                self.anim_index = (
                    self.anim_index + 1
                ) % len(self.sprites['run'])
        else:  # jump
            self.anim_index = 0

        if self.x < 0: # Limites da tela
            self.x = 0
        if self.x > WIDTH - 32:
            self.x = WIDTH - 32
        if self.y < 0:
            self.y = 0
        if self.y > HEIGHT - 32:
            self.y = HEIGHT - 32

    def draw(self):
        if self.direction == 1:
            sprite_list = self.sprites[self.state]
        else:
            sprite_list = self.sprites[self.state + '_left']
        sprite_name = sprite_list[self.anim_index % len(sprite_list)]
        screen.blit(sprite_name, (self.x, self.y))


class Enemy:
    def __init__(self, pos, patrol_range):
        self.x, self.y = pos
        self.start_x = pos[0]
        self.patrol_range = patrol_range
        self.vx = 0.9
        self.anim_index = 0
        self.anim_timer = 0
        self.sprites = [
            'enemy_walk_1', 'enemy_walk_2', 'enemy_walk_3'
        ]

    def update(self):
        self.x += self.vx
        if self.x < self.start_x or self.x > self.start_x + self.patrol_range:
            self.vx *= -1
        self.anim_timer += 1
        if self.anim_timer > 10:
            self.anim_timer = 0
            self.anim_index = (
                self.anim_index + 1
            ) % len(self.sprites)

    def draw(self):
        screen.blit(self.sprites[self.anim_index], (self.x, self.y))


class Boss:
    def __init__(self, pos, patrol_range):
        self.x, self.y = pos
        self.start_x = pos[0]
        self.patrol_range = patrol_range
        self.vx = 0.6
        self.anim_index = 0
        self.anim_timer = 0
        self.sprites_left = [
            'boss_walk_1', 'boss_walk_2', 'boss_walk_3'
        ]  # sprites virados para a esquerda
        self.sprites_right = [
            'boss_walk_right_1', 'boss_walk_right_2', 'boss_walk_right_3'
        ]  # sprites para a direita

    def update(self):
        self.x += self.vx
        if self.x < self.start_x or self.x > self.start_x + self.patrol_range:
            self.vx *= -1
        self.anim_timer += 1
        if self.anim_timer > 12:
            self.anim_timer = 0
            self.anim_index = (
                self.anim_index + 1
            ) % len(self.sprites_left)

    def draw(self):
        if self.vx >= 0:
            sprite = self.sprites_right[self.anim_index]
        else:
            sprite = self.sprites_left[self.anim_index]
        screen.blit(sprite, (self.x, self.y))


platforms = [
    Platform(0, 430, 800),      # chão (base do cenário)
    Platform(200, 320, 160),    # plataforma central baixa
    Platform(450, 250, 120),    # plataforma central alta
    Platform(700, 180, 160),    # plataforma direita superior
    Platform(600, 370, 120),    # plataforma direita baixa
    Platform(0, 100, 120),      # plataforma do portal (superior esquerda)
    Platform(120, 200, 100),    # plataforma intermediária para acessar o portal
]

# Herói sobre o chão (plataforma y=430, altura sprite=32)
hero = Hero((50, 398))  # 430 - 32 = 398

# Portal no canto superior esquerdo (plataforma y=100, altura sprite=32)
portal = Portal((0, 48))  # 100 - 32 = 68

# Chaves em plataformas diferentes 
keys_list = [
    Key((220, 288)),  # 320 - 32 = 288
    Key((480, 218)),  # 250 - 32 = 218
    Key((720, 148)),  # 180 - 32 = 148
]

# Inimigos sobre as plataformas (enemy: 16x16)
enemies = [
    Enemy((220, 304), 100),   # 320 - 16 = 304
    Enemy((480, 234), 100),   # 250 - 16 = 234
]

# Boss sobre a plataforma (boss: 36x36)
bosses = [
    Boss((700, 144), 60),    # 180 - 36 = 144
]


def draw():
    screen.clear()
    if game_state == 'menu':
        screen.blit('menu_bg', (0, 0))
        draw_menu()
    elif game_state == 'playing':
        screen.blit('game_bg', (0, 0))
        for plat in platforms:
            plat.draw()
        for key in keys_list:
            key.draw()
        for enemy in enemies:
            enemy.draw()
        for boss in bosses:
            boss.draw()
        portal.draw()
        hero.draw()
        # HUD das chaves
        screen.draw.text(
            f"Keys: {sum(k.collected for k in keys_list)}/3",
            (10, 10), fontsize=32, color="black"
        )


def death_reset():
    reset_game("death")


def update():
    global damage_pending
    if game_state == 'playing' and not damage_pending:
        hero.update(platforms)
        for enemy in enemies:
            enemy.update()
        for boss in bosses:
            boss.update()
        # Colisão com inimigos usando AABB
        for enemy in enemies:
            if rects_collide(
                hero.x, hero.y, 32, 32,
                enemy.x, enemy.y, 16, 16
            ):
                damage_pending = True
                if sound_on:
                    sounds.damage.play()
                clock.schedule(death_reset, 0.5)
                return
        for boss in bosses:
            if abs(hero.x - boss.x) < 24 and abs(hero.y - boss.y) < 24:
                damage_pending = True
                if sound_on:
                    sounds.damage.play()
                clock.schedule(death_reset, 0.5)
                return
        # Coleta das chaves
        for key in keys_list:
            if not key.collected and key.collide(hero):
                key.collected = True
                if sound_on:
                    sounds.key.play()
        # Portal só abre se todas as chaves forem coletadas
        portal.opened = all(key.collected for key in keys_list)
        # Vitória se encostar no portal aberto
        if portal.opened and portal.collide(hero):
            reset_game("win")


def draw_menu():
    screen.draw.text(
        "Mushroom Revolt", center=(WIDTH // 2, 70),
        fontsize=36, color="white"
    )
    if game_message:
        screen.draw.text(
            game_message, center=(WIDTH // 2, 130),
            fontsize=24, color="white"
        )
    screen.draw.text(
        "Start Game", center=start_button.center,
        fontsize=28, color="dimgray"
    )
    sound_text = "Sound: ON" if sound_on else "Sound: OFF"
    screen.draw.text(
        sound_text, center=sound_button.center,
        fontsize=28, color="dimgray"
    )
    screen.draw.text(
        "Exit", center=exit_button.center,
        fontsize=28, color="dimgray"
    )


def on_mouse_down(pos):
    global game_state, sound_on

    if game_state == 'menu':
        if start_button.collidepoint(pos):
            if sound_on:
                sounds.bgm.stop()
                sounds.bgm.play(-1)
                sounds.bgm.set_volume(0.3)
                sounds.click.play()
            game_state = 'playing'

        elif sound_button.collidepoint(pos):
            sound_on = not sound_on
            if sound_on:
                sounds.bgm.stop()
                sounds.bgm.play(-1)
                sounds.bgm.set_volume(0.3)
                sounds.click.play()
            else:
                sounds.bgm.stop()

        elif exit_button.collidepoint(pos):
            if sound_on:
                sounds.click.play()
            exit()


def reset_game(reason=""):
    global game_state, damage_pending, game_message
    hero.x, hero.y = 50, 398
    for key in keys_list:
        key.collected = False
    game_state = 'menu'
    if reason == "death":
        game_message = "Game Over! Kinako foi contaminado! :C"
    elif reason == "win":
        game_message = "You Win! Kinako voltou para casa! :D"
    else:
        game_message = ""
    damage_pending = False


pgzrun.go()
