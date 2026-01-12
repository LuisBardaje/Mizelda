import pygame, sys, json, os


pygame.init()
# pygame.mixer.init()


# ---------------- SETTINGS ----------------
TILE_SIZE = 32
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
FPS = 60


screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mizelda")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)


# ---------------- COLORS ----------------
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (120, 120, 120)


def load_sprite(path, size=(32,32)):
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(img, size)


# REQUIRED FILES (create simple PNGs if missing)
player_img = load_sprite("zelda.png")
enemy_img = load_sprite("enemies2.png")
sword_img = load_sprite("sword2.png")
tile_wall = load_sprite("walls2.png")
tile_floor = load_sprite("rocks2.png")


MAPS = [
    [
    "11111111111111111111",
    "10000000000000000001",
    "10000000001111100001",
    "10000000000000100001",
    "10001111100000100001",
    "10000000100000000001",
    "10000000100001111111",
    "10000000000000000001",
    "10000111111110000001",
    "10000000000010000001",
    "10000000000010000001",
    "10000011111000000001",
    "10000000000000011111",
    "10000000000000000001",
    "10000111111111111111",
    ],
]


MAP_WIDTH = len(MAPS[0][0]) * TILE_SIZE
MAP_HEIGHT = len(MAPS[0]) * TILE_SIZE


# ---------------- PLAYER ----------------
player = pygame.Rect(100, 100, 28, 28)
player_speed = 4
player_hp = 6
max_hp = 6
facing = "down"


# Sword
sword_rect = pygame.Rect(0,0,32,32)
sword_timer = 0


# ---------------- ENEMIES ----------------
enemies = [pygame.Rect(300,300,28,28), pygame.Rect(400,200,28,28)]


# ---------------- CAMERA ----------------
camera_x = 0
camera_y = 0

# ---------------- FUNCTIONS ----------------
def draw_map():
    for y,row in enumerate(MAPS[0]):
        for x,tile in enumerate(row):
            draw_x = x*TILE_SIZE - camera_x
            draw_y = y*TILE_SIZE - camera_y
            if tile == "1":
                screen.blit(tile_wall,(draw_x,draw_y))
            else:
                screen.blit(tile_floor,(draw_x,draw_y))


def can_move(rect):
    for y,row in enumerate(MAPS[0]):
        for x,tile in enumerate(row):
            if tile == "1":
                wall = pygame.Rect(x*TILE_SIZE,y*TILE_SIZE,TILE_SIZE,TILE_SIZE)
                if rect.colliderect(wall):
                    return False
    return True




def attack():
    global sword_timer
    sword_timer = 10
    if facing == "up": sword_rect.topleft = (player.x, player.y-32)
    if facing == "down": sword_rect.topleft = (player.x, player.y+32)
    if facing == "left": sword_rect.topleft = (player.x-32, player.y)
    if facing == "right": sword_rect.topleft = (player.x+32, player.y)


# ---------------- GAME LOOP ----------------
running = True
while running:
    clock.tick(FPS)


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                attack()


    keys = pygame.key.get_pressed()
    dx = dy = 0


    if keys[pygame.K_w]: dy = -player_speed; facing = "up"
    if keys[pygame.K_s]: dy = player_speed; facing = "down"
    if keys[pygame.K_a]: dx = -player_speed; facing = "left"
    if keys[pygame.K_d]: dx = player_speed; facing = "right"


    new_rect = player.move(dx,dy)
    if can_move(new_rect): player = new_rect


    # Camera follows player
    camera_x = player.x - SCREEN_WIDTH//2
    camera_y = player.y - SCREEN_HEIGHT//2


    # Sword hit detection
    if sword_timer > 0:
        sword_timer -= 1
        for e in enemies[:]:
            if sword_rect.colliderect(e):
                enemies.remove(e)


    # Draw
    screen.fill(BLACK)
    draw_map()


    for e in enemies:
        screen.blit(enemy_img,(e.x-camera_x,e.y-camera_y))


    screen.blit(player_img,(player.x-camera_x,player.y-camera_y))


    if sword_timer > 0:
        screen.blit(sword_img,(sword_rect.x-camera_x,sword_rect.y-camera_y))


    screen.blit(font.render(f"HP: {player_hp}",True,WHITE),(10,10))


    pygame.display.flip()


pygame.quit()
sys.exit()

