# -*- coding: utf-8 -*-
import math
import random
import sys
from pygame import Rect

# Configurações iniciais
WIDTH = 800
HEIGHT = 600

GRID_SIZE = 50
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE

COLOR_BG = (10, 10, 30)
COLOR_WALL = (90, 40, 0)

HERO_SPEED = 240
HERO_MOVE_COOLDOWN = 0.12
OBSTACLE_RATE = 0.25
ENEMY_COUNT = 5

STATE_MENU = 0
STATE_GAME = 1
STATE_OVER = 2
STATE_WIN = 3

# Estados do jogo
game_state = STATE_MENU
game_map = []

hero = None
enemies = []
treasure_pos = None
treasure_actor = None
background_tile = None

music_enabled = True

menu_buttons = {
    "start": Rect(WIDTH // 2 - 100, HEIGHT // 2 - 60, 200, 50),
    "music": Rect(WIDTH // 2 - 100, HEIGHT // 2 + 10, 200, 50),
    "exit": Rect(WIDTH // 2 - 100, HEIGHT // 2 + 80, 200, 50),
}

ASSET_SOUNDS = ["bg_music", "click_sound", "death_sound", "win_sound"]
ASSET_IMAGES = [
    "background",
    "sheriff_1", "sheriff_2", "sheriff_3",
    "python_1", "python_2", "python_3", "python_4", "python_5",
    "treasure_chest"
]

# Sistema de som
def play_sound(name):
    """Executa apenas efeitos sonoros, não música."""
    if not music_enabled:
        return
    try:
        snd = getattr(sounds, name)
        snd.set_volume(1.0)
        snd.play()
    except Exception as e:
        print(f"[sound error] {name} -> {e}")


def toggle_music():
    global music_enabled

    music_enabled = not music_enabled

    if music_enabled:
        try:
            music.set_volume(1.0)
            music.play("bg_music")
        except Exception as e:
            print(f"[music error] toggle -> {e}")
    else:
        try:
            music.stop()
        except:
            pass

# Fundo
def load_background():
    global background_tile
    try:
        background_tile = Actor("background")
        background_tile.anchor = (0, 0)
    except:
        background_tile = None


def draw_background_tiled():
    if not background_tile:
        screen.fill(COLOR_BG)
        return

    w = background_tile.width
    h = background_tile.height

    for y in range(0, HEIGHT, h):
        for x in range(0, WIDTH, w):
            background_tile.topleft = (x, y)
            background_tile.draw()

# Personagens
class Character:
    def __init__(self, grid_pos, frames, speed):
        self.grid_pos = list(grid_pos)
        self.frames = frames
        self.speed = float(speed)

        try:
            self.actor = Actor(frames[0])
            self.actor.pos = self._grid_to_pixel(grid_pos)
        except Exception as e:
            print(f"[actor load error] {frames[0]}: {e}")
            self.actor = None

        self.anim_index = 0
        self.anim_timer = 0
        self.anim_speed = 0.12

        self.target_pos = self._grid_to_pixel(grid_pos)
        self.moving = False

    def _grid_to_pixel(self, pos):
        return (
            pos[0] * GRID_SIZE + GRID_SIZE // 2,
            pos[1] * GRID_SIZE + GRID_SIZE // 2
        )

    def move_to_grid(self, new_pos):
        if self.moving:
            return

        x, y = new_pos
        if not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):
            return
        if game_map[y][x] == 1:
            return

        dx = abs(x - self.grid_pos[0])
        dy = abs(y - self.grid_pos[1])
        if dx + dy == 1:
            self.grid_pos = [x, y]
            self.target_pos = self._grid_to_pixel((x, y))
            self.moving = True

    def update_movement(self, dt):
        if not self.moving or not self.actor:
            return

        cx, cy = self.actor.pos
        tx, ty = self.target_pos

        dx = tx - cx
        dy = ty - cy
        dist = math.hypot(dx, dy)

        if dist <= self.speed * dt:
            self.actor.pos = (tx, ty)
            self.moving = False
        else:
            self.actor.x += dx * (self.speed * dt) / dist
            self.actor.y += dy * (self.speed * dt) / dist

    def update_animation(self, dt):
        if not self.actor:
            return

        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer -= self.anim_speed
            self.anim_index = (self.anim_index + 1) % len(self.frames)
            self.actor.image = self.frames[self.anim_index]

    def draw(self):
        if self.actor:
            self.actor.draw()


class Hero(Character):
    def __init__(self, pos):
        super().__init__(pos, ["sheriff_1", "sheriff_2", "sheriff_3"], HERO_SPEED)
        self.cooldown = 0

    def handle_input(self, kb, dt):
        if self.moving:
            return

        self.cooldown = max(0, self.cooldown - dt)
        if self.cooldown > 0:
            return

        new = list(self.grid_pos)
        moved = True

        if kb.left:
            new[0] -= 1
        elif kb.right:
            new[0] += 1
        elif kb.up:
            new[1] -= 1
        elif kb.down:
            new[1] += 1
        else:
            moved = False

        if moved:
            self.move_to_grid(new)
            self.cooldown = HERO_MOVE_COOLDOWN

    def update(self, dt, kb):
        self.update_animation(dt)
        self.update_movement(dt)
        self.handle_input(kb, dt)


class Enemy(Character):
    def __init__(self, pos):
        super().__init__(
            pos,
            ["python_1", "python_2", "python_3", "python_4", "python_5"],
            140
        )
        self.move_interval = 1.2
        self.move_timer = random.uniform(0.3, 1.2)

    def patrol(self):
        directions = [(1,0),(-1,0),(0,1),(0,-1)]
        random.shuffle(directions)

        for dx, dy in directions:
            nx = self.grid_pos[0] + dx
            ny = self.grid_pos[1] + dy
            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                if game_map[ny][nx] == 0:
                    self.move_to_grid([nx, ny])
                    return

    def update(self, dt):
        self.update_animation(dt)
        self.update_movement(dt)

        if not self.moving:
            self.move_timer -= dt
            if self.move_timer <= 0:
                self.patrol()
                self.move_timer = self.move_interval

# Gerador de mapa
def create_map():
    """
    Gera o mapa até existir um caminho entre hero → tesouro.
    Usa flood fill (BFS) para garantir caminho.
    """
    while True:
        temp = []
        for y in range(GRID_HEIGHT):
            row = []
            for x in range(GRID_WIDTH):
                if x in (0, GRID_WIDTH-1) or y in (0, GRID_HEIGHT-1):
                    row.append(1)
                elif random.random() < OBSTACLE_RATE:
                    row.append(1)
                else:
                    row.append(0)
            temp.append(row)

        def rand_free():
            while True:
                x = random.randint(1, GRID_WIDTH - 2)
                y = random.randint(1, GRID_HEIGHT - 2)
                if temp[y][x] == 0:
                    return (x, y)

        hero_pos = rand_free()
        treasure = rand_free()

        queue = [hero_pos]
        visited = {hero_pos}

        while queue:
            cx, cy = queue.pop(0)
            if (cx, cy) == treasure:
                global treasure_pos
                treasure_pos = treasure
                return temp, hero_pos

            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = cx+dx, cy+dy
                if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                    if temp[ny][nx] == 0 and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny))


# Iniciando o jogo
def init_game():
    global game_map, hero, enemies, treasure_actor, game_state

    game_map, hero_start = create_map()
    load_background()

    tx, ty = treasure_pos
    treasure_actor = Actor("treasure_chest")
    treasure_actor.pos = (tx * GRID_SIZE + GRID_SIZE//2, ty * GRID_SIZE + GRID_SIZE//2)

    hero = Hero(hero_start)

    enemies.clear()
    occupied = {hero_start, treasure_pos}
    for _ in range(ENEMY_COUNT):
         while True:
            x = random.randint(1, GRID_WIDTH-2)
            y = random.randint(1, GRID_HEIGHT-2)
            if game_map[y][x] == 0 and (x,y) not in occupied:
                occupied.add((x,y))
                enemies.append(Enemy([x,y]))
                break

    if music_enabled:
        try:
            music.set_volume(1.0)
            music.play("bg_music")
        except Exception as e:
            print(f"[music play error] {e}")

    game_state = STATE_GAME


# Desenho
def draw_menu():
    screen.fill(COLOR_BG)
    screen.draw.text(
        "PYTHON DUNGEON",
        center=(WIDTH//2, HEIGHT//4),
        fontsize=72,
        color="gold"
    )

    for key, rect in menu_buttons.items():
        screen.draw.filled_rect(rect, (150, 50, 50))

        if key == "start":
            txt = "COMECAR O JOGO"
        elif key == "music":
            txt = "MUSICA: LIGADO" if music_enabled else "MUSICA: DESLIGADO"
        else:
            txt = "SAIR"

        screen.draw.text(txt, center=rect.center, color="white")


def draw_game():
    draw_background_tiled()

    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if game_map[y][x] == 1:
                r = Rect(x*GRID_SIZE, y*GRID_SIZE, GRID_SIZE, GRID_SIZE)
                screen.draw.filled_rect(r, COLOR_WALL)

    if treasure_actor:
        treasure_actor.draw()

    if hero:
        hero.draw()

    for e in enemies:
        e.draw()


def draw():
    if game_state == STATE_MENU:
        draw_menu()
    elif game_state == STATE_GAME:
        draw_game()
    elif game_state == STATE_OVER:
        screen.fill("black")
        screen.draw.text(
            "VOCE FOI PEGO!",
            center=(WIDTH//2, HEIGHT//2),
            fontsize=60,
            color="red"
        )
        screen.draw.text(
            "ENTER = VOLTAR AO MENU",
            center=(WIDTH//2, HEIGHT//2+60),
            fontsize=28
        )
    elif game_state == STATE_WIN:
        screen.fill("black")
        screen.draw.text(
            "VOCE ENCONTROU O TESOURO!",
            center=(WIDTH//2, HEIGHT//2),
            fontsize=60,
            color="gold"
        )
        screen.draw.text(
            "ENTER = VOLTAR AO MENU",
            center=(WIDTH//2, HEIGHT//2+60),
            fontsize=28
        )


# Lógica do jogo
def update(dt):
    global game_state, treasure_pos, treasure_actor

    if game_state != STATE_GAME:
        return

    if music_enabled:
        try:
            if not music.get_busy():
                music.play("bg_music")
        except Exception:
            pass 

    hero.update(dt, keyboard)

    for e in enemies:
        e.update(dt)
        if hero.grid_pos == e.grid_pos:
            play_sound("death_sound")
            game_state = STATE_OVER
            return

    if treasure_pos and hero.grid_pos == list(treasure_pos):
        play_sound("win_sound")
        treasure_pos = None
        treasure_actor = None
        game_state = STATE_WIN


# Inputs
def on_key_down(key):
    global game_state

    if key == keys.RETURN and game_state in (STATE_OVER, STATE_WIN):
        game_state = STATE_MENU


def on_mouse_down(pos, button):
    if game_state != STATE_MENU:
        return

    if button != mouse.LEFT:
        return

    if menu_buttons["start"].collidepoint(pos):
        play_sound("click_sound")
        init_game()

    elif menu_buttons["music"].collidepoint(pos):
        play_sound("click_sound")
        toggle_music()

    elif menu_buttons["exit"].collidepoint(pos):
        play_sound("click_sound")
        sys.exit()