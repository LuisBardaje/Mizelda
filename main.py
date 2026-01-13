import pygame               # game library (graphics, input, sound)
import sys                  # for sys.exit()
import random               # for random enemy/pickup positions
import math                 # for boss projectile direction

pygame.init()               # start pygame

# -----------------------------
# SCREEN + TILE SETTINGS
# -----------------------------
TILE = 32                   # each tile is 32x32 pixels
ROOM_W = 16                 # room width in tiles
ROOM_H = 15                 # room height in tiles

WIDTH = ROOM_W * TILE       # screen width in pixels
HEIGHT = ROOM_H * TILE      # screen height in pixels

FPS = 60                    # frames per second

screen = pygame.display.set_mode((WIDTH, HEIGHT))  # create window
pygame.display.set_caption("Beginner NES Zelda")   # window title
clock = pygame.time.Clock()                        # for FPS control
font = pygame.font.SysFont(None, 20)               # small font for UI

# -----------------------------
# COLORS (for UI + buttons)
# -----------------------------
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BTN_GRAY = (90, 90, 90)

# -----------------------------
# LOAD IMAGES
# -----------------------------
def load_img(name, size):
    img = pygame.image.load(name).convert_alpha()      # load PNG with transparency
    return pygame.transform.scale(img, size)           # resize to size

# tiles
floor_img = load_img("floor.png", (TILE, TILE))        # floor tile
wall_img  = load_img("wall.png",  (TILE, TILE))        # wall tile

# hearts UI
heart_full  = load_img("heart_full.png",  (TILE, TILE)) # full heart
heart_empty = load_img("heart_empty.png", (TILE, TILE)) # empty heart

# pickups
rupee_img     = load_img("rupee.png",       (16, 16))   # small rupee
bomb_pick_img = load_img("bomb_pickup.png", (16, 16))   # small bomb pickup
arrow_pick_img= load_img("arrow_pickup.png",(16, 16))   # small arrow pickup

# combat
sword_img     = load_img("sword.png", (TILE, TILE))     # sword sprite
fireball_img  = load_img("fireball.png", (16, 16))      # boss projectile

# player NES-style 2-frame animation per direction
player_frames = {
    "down":  [load_img("p_down_0.png",(TILE,TILE)),  load_img("p_down_1.png",(TILE,TILE))],
    "up":    [load_img("p_up_0.png",(TILE,TILE)),    load_img("p_up_1.png",(TILE,TILE))],
    "left":  [load_img("p_left_0.png",(TILE,TILE)),  load_img("p_left_1.png",(TILE,TILE))],
    "right": [load_img("p_right_0.png",(TILE,TILE)), load_img("p_right_1.png",(TILE,TILE))],
}

# enemy animation (2-frame slime)
slime_frames = [
    load_img("slime_0.png",(TILE,TILE)),
    load_img("slime_1.png",(TILE,TILE))
]

# boss animation (2-frame, 64x64)
boss_frames = [
    load_img("boss_0.png",(64,64)),
    load_img("boss_1.png",(64,64))
]

# -----------------------------
# MAPS
# "1" = wall, "0" = floor
# -----------------------------
OVERWORLD = {
    (0,0): [
        "1111111111111111",
        "1000000000000001",
        "1000000000110001",
        "1000000000110001",
        "1000000000000001",
        "1000001111000001",
        "1000001001000001",
        "1000001111000001",
        "1000000000000001",
        "1000000000000001",
        "1000111000000001",
        "1000000000000001",
        "1000000000000001",
        "1000000000000001",
        "1111111111111111",
    ],
    (1,0): [
        "1111111111111111",
        "1000000000000001",
        "1000000000000001",
        "1000011111110001",
        "1000010000010001",
        "1000010000010001",
        "1000010000010001",
        "1000010000010001",
        "1000011111110001",
        "1000000000000001",
        "1000000000000001",
        "1000000000000001",
        "1000000000000001",
        "1000000000000001",
        "1111111111111111",
    ],
}

DUNGEON = {
    (0,0): [
        "1111111111111111",
        "1000000000000001",
        "1011110111111101",
        "1000010000000001",
        "1111010111111101",
        "1000010100000001",
        "1011110111111101",
        "1000000000000001",
        "1011111111111101",
        "1000000000000001",
        "1011110111111101",
        "1000010000000001",
        "1011110111111101",
        "1000000000000001",
        "1111111111111111",
    ]
}

# screen-to-screen neighbors
NEIGHBORS_OVERWORLD = {
    (0,0): {"right": (1,0)},
    (1,0): {"left": (0,0)}
}
NEIGHBORS_DUNGEON = {
    (0,0): {}
}

# entrance tile: if player steps on tile (14,13) in overworld (0,0) => go dungeon
ENTRANCE_TILE = (14, 13)            # tile position to enter dungeon
ENTRANCE_FROM = ("overworld",(0,0)) # where entrance exists

# -----------------------------
# GAME STATE
# -----------------------------
world = "overworld"                 # current world: "overworld" or "dungeon"
room = (0,0)                        # current room coordinate

player = pygame.Rect(2*TILE+3, 2*TILE+3, 26, 26)  # player hitbox rect
speed = 3                                          # movement speed
facing = "down"                                    # player direction

max_hp = 6                         # max hearts
hp = 6                             # current hearts

# inventory
rupees = 0                         # money
bombs = 0                          # bombs count
arrows = 0                         # arrows count
has_bow = True                     # bow enabled

# sword attack
sword_rect = pygame.Rect(0,0,28,28)  # sword hitbox
sword_timer = 0                      # how long sword stays active
attack_cd = 0                        # cooldown between swings

# projectiles/items in the world
placed_bombs = []   # list of {"rect": Rect, "timer": int}
arrows_fired = []   # list of {"rect": Rect, "vx": int, "vy": int, "life": int}
fireballs = []      # list of {"rect": Rect, "vx": int, "vy": int, "life": int}

# animation controls
walk_frame = 0       # 0 or 1
walk_tick = 0        # counter for switching frames

# room content
pickups = []         # list of {"kind": str, "rect": Rect}
enemies = []         # list of {"rect": Rect, "hp": int, "anim": int}
boss = None          # None or {"rect": Rect, "hp": int, "anim": int, "cooldown": int}

# -----------------------------
# MOBILE BUTTONS (mouse/touch)
# -----------------------------
btn_left  = pygame.Rect(20, HEIGHT-60, 60, 40)          # left button rect
btn_right = pygame.Rect(90, HEIGHT-60, 60, 40)          # right button rect
btn_up    = pygame.Rect(WIDTH-140, HEIGHT-80, 60, 40)   # up button rect
btn_down  = pygame.Rect(WIDTH-140, HEIGHT-40, 60, 40)   # down button rect
btn_a     = pygame.Rect(WIDTH-70, HEIGHT-80, 50, 50)    # A (sword)
btn_b     = pygame.Rect(WIDTH-70, HEIGHT-25, 50, 25)    # B (item)

# -----------------------------
# MAP HELPERS
# -----------------------------
def get_map():                                         # get current tile map
    if world == "overworld":
        return OVERWORLD[room]
    return DUNGEON[room]

def get_neighbors():                                   # get neighbor rooms
    if world == "overworld":
        return NEIGHBORS_OVERWORLD.get(room, {})
    return NEIGHBORS_DUNGEON.get(room, {})

def blocked(rect):                                     # check if rect hits walls
    m = get_map()
    for y, row in enumerate(m):
        for x, t in enumerate(row):
            if t == "1":                               # wall tile
                wall = pygame.Rect(x*TILE, y*TILE, TILE, TILE)
                if rect.colliderect(wall):
                    return True
    return False

def draw_map():                                        # draw tiles
    m = get_map()
    for y, row in enumerate(m):
        for x, t in enumerate(row):
            img = wall_img if t == "1" else floor_img
            screen.blit(img, (x*TILE, y*TILE))

# -----------------------------
# ROOM CONTENT LOADER
# -----------------------------
def load_room():                                       # spawn things for room
    global pickups, enemies, boss, fireballs, placed_bombs, arrows_fired

    pickups = []                                       # clear old pickups
    enemies = []                                       # clear old enemies
    boss = None                                        # clear boss

    fireballs = []                                     # clear boss shots
    placed_bombs = []                                  # clear bombs
    arrows_fired = []                                  # clear arrows

    # --- Overworld room (0,0) ---
    if world == "overworld" and room == (0,0):
        spawn_pickups = [("rupee",(7,7)), ("bomb",(3,11)), ("arrow",(12,4))]
        spawn_enemies = [(5,5), (10,10)]
    # --- Overworld room (1,0) ---
    elif world == "overworld" and room == (1,0):
        spawn_pickups = [("rupee",(2,2)), ("rupee",(13,12))]
        spawn_enemies = [(8,7)]
    # --- Dungeon room (0,0) with boss ---
    elif world == "dungeon" and room == (0,0):
        spawn_pickups = [("rupee",(2,12)), ("bomb",(13,2))]
        spawn_enemies = [(7,7), (11,11)]
        boss = {"rect": pygame.Rect(7*TILE, 3*TILE, 64, 64), "hp": 12, "anim": 0, "cooldown": 60}
    else:
        spawn_pickups = []
        spawn_enemies = []

    # convert pickups to rect objects
    pickups = [{"kind": k, "rect": pygame.Rect(tx*TILE+8, ty*TILE+8, 16, 16)} for k,(tx,ty) in spawn_pickups]

    # convert enemies to rect objects
    enemies = [{"rect": pygame.Rect(tx*TILE+3, ty*TILE+3, 26, 26), "hp": 2, "anim": 0} for (tx,ty) in spawn_enemies]

load_room()                                            # start by loading first room

# -----------------------------
# ACTIONS (SWORD + ITEMS)
# -----------------------------
def swing_sword():                                     # A button / SPACE
    global sword_timer, attack_cd

    if attack_cd > 0:                                  # if still cooling down, stop
        return

    attack_cd = 12                                     # set cooldown
    sword_timer = 8                                    # sword exists for 8 frames

    if facing == "up":
        sword_rect.topleft = (player.x, player.y - 28)  # sword above player
    elif facing == "down":
        sword_rect.topleft = (player.x, player.y + 28)  # sword below player
    elif facing == "left":
        sword_rect.topleft = (player.x - 28, player.y)  # sword left of player
    else:
        sword_rect.topleft = (player.x + 28, player.y)  # sword right of player

def use_item():                                        # B button / CTRL / E
    global bombs, arrows

    if bombs > 0:                                      # use bomb first if available
        bombs -= 1                                     # reduce bombs
        placed_bombs.append({"rect": pygame.Rect(player.centerx-8, player.centery-8, 16, 16), "timer": 90})
        return

    if has_bow and arrows > 0:                         # else shoot arrow if possible
        arrows -= 1                                    # reduce arrows
        vx = vy = 0                                    # arrow direction

        if facing == "up":    vy = -6
        if facing == "down":  vy = 6
        if facing == "left":  vx = -6
        if facing == "right": vx = 6

        arrows_fired.append({"rect": pygame.Rect(player.centerx-6, player.centery-6, 12, 12),
                             "vx": vx, "vy": vy, "life": 60})

def damage_player(amount=1):                           # lose hearts
    global hp, world, room

    hp -= amount                                       # reduce HP
    if hp <= 0:                                        # if dead, restart
        hp = max_hp
        world = "overworld"
        room = (0,0)
        player.x, player.y = 2*TILE+3, 2*TILE+3
        load_room()

# -----------------------------
# TRANSITIONS
# -----------------------------
def check_dungeon_entrance():                          # step on entrance tile => dungeon
    global world, room

    tx = player.centerx // TILE                        # tile x under player center
    ty = player.centery // TILE                        # tile y under player center

    if (world, room) == ENTRANCE_FROM and (tx,ty) == ENTRANCE_TILE:
        world = "dungeon"                              # switch world
        room = (0,0)                                   # dungeon start room
        player.x, player.y = 1*TILE+3, 1*TILE+3         # spawn point
        load_room()                                    # load dungeon room content

def check_edge_transition():                            # walk off screen => next room
    global room

    n = get_neighbors()                                 # neighbor dictionary

    if player.left < 0 and "left" in n:                 # left transition
        room = n["left"]
        player.left = 0
        load_room()

    if player.right > WIDTH and "right" in n:           # right transition
        room = n["right"]
        player.right = WIDTH
        load_room()

# -----------------------------
# MAIN LOOP
# -----------------------------
running = True
while running:
    clock.tick(FPS)                                     # limit FPS

    # --- EVENTS ---
    for event in pygame.event.get():                     # get events
        if event.type == pygame.QUIT:                    # if user closes window
            running = False

        if event.type == pygame.KEYDOWN:                 # key press
            if event.key == pygame.K_SPACE:              # SPACE = sword
                swing_sword()
            if event.key == pygame.K_LCTRL or event.key == pygame.K_e:  # CTRL/E = item
                use_item()

    # --- INPUT (keyboard + touch) ---
    keys = pygame.key.get_pressed()                      # get held keys
    dx = dy = 0                                          # movement deltas

    if keys[pygame.K_w]: dy = -speed; facing = "up"
    if keys[pygame.K_s]: dy = speed;  facing = "down"
    if keys[pygame.K_a]: dx = -speed; facing = "left"
    if keys[pygame.K_d]: dx = speed;  facing = "right"

    if pygame.mouse.get_pressed()[0]:                    # mouse pressed (touch)
        mx, my = pygame.mouse.get_pos()                  # mouse position
        if btn_left.collidepoint(mx,my):  dx = -speed; facing = "left"
        if btn_right.collidepoint(mx,my): dx = speed;  facing = "right"
        if btn_up.collidepoint(mx,my):    dy = -speed; facing = "up"
        if btn_down.collidepoint(mx,my):  dy = speed;  facing = "down"
        if btn_a.collidepoint(mx,my):     swing_sword()
        if btn_b.collidepoint(mx,my):     use_item()

    # --- MOVE PLAYER (axis separated) ---
    nr = player.move(dx, 0)                              # test horizontal move
    if not blocked(nr):                                  # if no wall
        player = nr                                      # apply move

    nr = player.move(0, dy)                              # test vertical move
    if not blocked(nr):                                  # if no wall
        player = nr                                      # apply move

    # --- TRANSITIONS ---
    check_dungeon_entrance()                             # overworld -> dungeon
    check_edge_transition()                              # screen-to-screen rooms

    # --- ANIMATION ---
    moving = (dx != 0 or dy != 0)                        # is player moving?
    if moving:
        walk_tick += 1                                  # count frames
        if walk_tick >= 10:                              # every 10 frames
            walk_tick = 0                                # reset counter
            walk_frame = 1 - walk_frame                  # flip 0<->1
    else:
        walk_frame = 0                                   # idle frame
        walk_tick = 0

    # --- COOLDOWNS ---
    if attack_cd > 0:                                    # reduce cooldown
        attack_cd -= 1
    if sword_timer > 0:                                  # reduce sword time
        sword_timer -= 1

    # --- PICKUPS ---
    for p in pickups[:]:                                 # loop copy so we can remove
        if player.colliderect(p["rect"]):                # if player touches pickup
            if p["kind"] == "rupee":
                rupees += 1
            elif p["kind"] == "bomb":
                bombs += 1
            else:
                arrows += 5
            pickups.remove(p)

    # --- ENEMIES (simple chase) ---
    for e in enemies:
        e["anim"] = (e["anim"] + 1) % 30                 # enemy animation timer

        vx = 1 if player.x > e["rect"].x else -1 if player.x < e["rect"].x else 0
        vy = 1 if player.y > e["rect"].y else -1 if player.y < e["rect"].y else 0

        nr = e["rect"].move(vx, 0)                       # try move X
        if not blocked(nr):
            e["rect"] = nr

        nr = e["rect"].move(0, vy)                       # try move Y
        if not blocked(nr):
            e["rect"] = nr

        if e["rect"].colliderect(player):                # enemy hits player
            damage_player(1)

    # --- BOSS (moves + shoots) ---
    if boss:
        boss["anim"] = (boss["anim"] + 1) % 30           # boss animation timer
        boss["cooldown"] -= 1                            # reduce shoot timer

        boss_speed = 1 if boss["hp"] > 6 else 2          # phase 2 faster when hp <= 6

        vx = boss_speed if player.centerx > boss["rect"].centerx else -boss_speed
        vy = boss_speed if player.centery > boss["rect"].centery else -boss_speed

        nr = boss["rect"].move(vx, 0)                    # try move X
        if not blocked(nr):
            boss["rect"] = nr

        nr = boss["rect"].move(0, vy)                    # try move Y
        if not blocked(nr):
            boss["rect"] = nr

        if boss["cooldown"] <= 0:                        # time to shoot?
            boss["cooldown"] = 60 if boss["hp"] > 6 else 35

            dxp = player.centerx - boss["rect"].centerx  # vector to player
            dyp = player.centery - boss["rect"].centery
            dist = max(1, math.hypot(dxp, dyp))          # length (avoid /0)
            ux, uy = dxp/dist, dyp/dist                  # unit direction

            spd = 3 if boss["hp"] > 6 else 4             # projectile speed
            fireballs.append({"rect": pygame.Rect(boss["rect"].centerx, boss["rect"].centery, 16, 16),
                              "vx": int(ux*spd), "vy": int(uy*spd), "life": 180})

        if boss["rect"].colliderect(player):             # boss hits player
            damage_player(1)

    # --- FIREBALLS ---
    for fb in fireballs[:]:
        fb["life"] -= 1                                  # reduce life
        fb["rect"].x += fb["vx"]                         # move X
        fb["rect"].y += fb["vy"]                         # move Y

        if fb["life"] <= 0 or blocked(fb["rect"]):       # delete if expired/hit wall
            fireballs.remove(fb)
            continue

        if fb["rect"].colliderect(player):               # hit player
            fireballs.remove(fb)
            damage_player(1)

    # --- BOMBS (explode after timer) ---
    for b in placed_bombs[:]:
        b["timer"] -= 1                                  # countdown
        if b["timer"] == 0:                              # explode now
            ex = pygame.Rect(b["rect"].centerx-32, b["rect"].centery-32, 64, 64)  # blast area

            for e in enemies[:]:
                if ex.colliderect(e["rect"]):            # blast kills enemies
                    enemies.remove(e)

            if boss and ex.colliderect(boss["rect"]):    # blast damages boss
                boss["hp"] -= 4
                if boss["hp"] <= 0:
                    boss = None

            placed_bombs.remove(b)                       # remove bomb after explosion

    # --- ARROWS ---
    for a in arrows_fired[:]:
        a["life"] -= 1                                   # reduce arrow life
        a["rect"].x += a["vx"]                            # move X
        a["rect"].y += a["vy"]                            # move Y

        if a["life"] <= 0 or blocked(a["rect"]):         # remove if expired/hit wall
            arrows_fired.remove(a)
            continue

        for e in enemies[:]:
            if a["rect"].colliderect(e["rect"]):         # arrow hits enemy
                e["hp"] -= 1
                if e["hp"] <= 0:
                    enemies.remove(e)
                arrows_fired.remove(a)
                break

        if boss and a in arrows_fired and a["rect"].colliderect(boss["rect"]):  # arrow hits boss
            boss["hp"] -= 1
            arrows_fired.remove(a)
            if boss["hp"] <= 0:
                boss = None

    # --- SWORD HIT ---
    if sword_timer > 0:                                   # only when sword active
        for e in enemies[:]:
            if sword_rect.colliderect(e["rect"]):         # sword hits enemy
                e["hp"] -= 1
                if e["hp"] <= 0:
                    enemies.remove(e)

        if boss and sword_rect.colliderect(boss["rect"]): # sword hits boss
            boss["hp"] -= 1
            if boss["hp"] <= 0:
                boss = None

    # ---------------- DRAW ----------------
    screen.fill(BLACK)                                    # clear screen
    draw_map()                                            # draw room

    for p in pickups:                                     # draw pickups
        img = rupee_img if p["kind"] == "rupee" else bomb_pick_img if p["kind"] == "bomb" else arrow_pick_img
        screen.blit(img, p["rect"].topleft)

    for e in enemies:                                     # draw enemies
        img = slime_frames[0 if e["anim"] < 15 else 1]
        screen.blit(img, e["rect"].topleft)

    if boss:                                              # draw boss
        img = boss_frames[0 if boss["anim"] < 15 else 1]
        screen.blit(img, boss["rect"].topleft)

    for fb in fireballs:                                  # draw fireballs
        screen.blit(fireball_img, fb["rect"].topleft)

    pimg = player_frames[facing][walk_frame]              # choose player frame
    screen.blit(pimg, player.topleft)                     # draw player

    if sword_timer > 0:                                   # draw sword
        screen.blit(sword_img, sword_rect.topleft)

    for i in range(max_hp):                               # draw hearts
        img = heart_full if i < hp else heart_empty
        screen.blit(img, (i*TILE, 0))

    ui = f"Rupees:{rupees}  Bombs:{bombs}  Arrows:{arrows}"# inventory text
    screen.blit(font.render(ui, True, WHITE), (10, HEIGHT-18))

    # draw mobile buttons
    pygame.draw.rect(screen, BTN_GRAY, btn_left, 2)
    pygame.draw.rect(screen, BTN_GRAY, btn_right, 2)
    pygame.draw.rect(screen, BTN_GRAY, btn_up, 2)
    pygame.draw.rect(screen, BTN_GRAY, btn_down, 2)
    pygame.draw.rect(screen, BTN_GRAY, btn_a, 2)
    pygame.draw.rect(screen, BTN_GRAY, btn_b, 2)

    screen.blit(font.render("<", True, WHITE), (btn_left.x+22, btn_left.y+10))
    screen.blit(font.render(">", True, WHITE), (btn_right.x+22, btn_right.y+10))
    screen.blit(font.render("^", True, WHITE), (btn_up.x+24, btn_up.y+8))
    screen.blit(font.render("v", True, WHITE), (btn_down.x+24, btn_down.y+8))
    screen.blit(font.render("A", True, WHITE), (btn_a.x+18, btn_a.y+14))
    screen.blit(font.render("B", True, WHITE), (btn_b.x+18, btn_b.y+2))

    pygame.display.flip()                                 # show frame

pygame.quit()                                             # close pygame
sys.exit()                             