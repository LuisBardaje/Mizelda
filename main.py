import pygame
import random
import math
import os

# ============================================================
# Zelda-like Mini Game (uses your provided assets)
# Controls:
#   WASD / Arrow Keys = Move
#   SPACE = Sword attack
# Goal:
#   Defeat each biome boss to unlock the portal to the next biome:
#   Forest -> Desert -> Ice -> Water -> Dark
# ============================================================

# -------------------------
# Basic settings
# -------------------------
FPS = 60

# We choose a "world tile size" of 48px so the floor tiles look good,
# and we scale 16x16 sprites up by 3x to match (16*3 = 48).
TILE = 48
SPRITE_SCALE = 3

VIEW_TILES_W = 20
VIEW_TILES_H = 12
SCREEN_W = VIEW_TILES_W * TILE
SCREEN_H = VIEW_TILES_H * TILE

# Big overworld size (in 48px tiles)
WORLD_W = 80
WORLD_H = 60

# -------------------------
# Biome IDs
# -------------------------
FOREST = 0
DESERT = 1
ICE = 2
WATER = 3
DARK = 4

BIOME_NAMES = {
    FOREST: "Forest of Moss",
    DESERT: "Sunburn Dunes",
    ICE: "Frostveil Fields",
    WATER: "Mirror Marsh",
    DARK: "Blackroot Keep",
}

# Biome progression order
BIOME_ORDER = [FOREST, DESERT, ICE, WATER, DARK]

# -------------------------
# Helpers
# -------------------------
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def load_image(path):
    img = pygame.image.load(path).convert_alpha()
    return img

def slice_sheet(sheet, frame_w, frame_h):
    """Return a list of frames cut from a sheet left-to-right, top-to-bottom."""
    frames = []
    sw, sh = sheet.get_size()
    for y in range(0, sh, frame_h):
        for x in range(0, sw, frame_w):
            frame = sheet.subsurface(pygame.Rect(x, y, frame_w, frame_h)).copy()
            frames.append(frame)
    return frames

def scale_img(img, scale):
    w, h = img.get_size()
    return pygame.transform.scale(img, (w * scale, h * scale))

# -------------------------
# Tile / world generation
# -------------------------
def biome_at(tx, ty):
    """
    Split the overworld into 5 biome regions.
    Layout (simple but effective):
      - Left side (x < 30): top = forest, bottom = ice
      - Middle (30 <= x < 60): top = desert, bottom = water
      - Right side (x >= 60): dark
    """
    if tx >= 60:
        return DARK
    if tx < 30:
        return FOREST if ty < 30 else ICE
    else:
        return DESERT if ty < 30 else WATER

# -------------------------
# Entities
# -------------------------
class Entity:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.vx = 0
        self.vy = 0
        self.hp = 1
        self.max_hp = 1
        self.alive = True

    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.alive = False

class Player(Entity):
    def __init__(self, x, y, walk_frames_by_dir, attack_frames):
        # Player is a 16x16 sprite scaled to 48x48 in the world
        super().__init__(x, y, TILE, TILE)

        self.speed = 220  # pixels/sec
        self.facing = "down"  # up/down/left/right

        self.walk_frames = walk_frames_by_dir
        self.attack_frames = attack_frames

        self.walk_anim_t = 0.0
        self.walk_frame_i = 0

        self.attacking = False
        self.attack_t = 0.0
        self.attack_frame_i = 0
        self.attack_cooldown = 0.0

        self.max_hp = 6
        self.hp = self.max_hp

        self.invuln_t = 0.0  # short invulnerability after being hit

    def update(self, dt, keys, world):
        # cooldown timers
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        if self.invuln_t > 0:
            self.invuln_t -= dt

        # movement input disabled during attack for a snappy zelda feel
        move_x = 0
        move_y = 0

        if not self.attacking:
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                move_x -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                move_x += 1
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                move_y -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                move_y += 1

        # set facing based on last direction pressed
        if move_x != 0 or move_y != 0:
            if abs(move_x) > abs(move_y):
                self.facing = "right" if move_x > 0 else "left"
            else:
                self.facing = "down" if move_y > 0 else "up"

        # normalize diagonal
        length = math.hypot(move_x, move_y)
        if length > 0:
            move_x /= length
            move_y /= length

        self.vx = move_x * self.speed
        self.vy = move_y * self.speed

        # move with collision (axis-separated)
        self.move_and_collide(dt, world)

        # animation
        if self.attacking:
            self.attack_t += dt
            # 4 frames total, play quickly
            frame_time = 0.06
            self.attack_frame_i = int(self.attack_t / frame_time)
            if self.attack_frame_i >= len(self.attack_frames):
                self.attacking = False
                self.attack_t = 0.0
                self.attack_frame_i = 0
        else:
            if length > 0:
                self.walk_anim_t += dt
                frame_time = 0.12
                self.walk_frame_i = int(self.walk_anim_t / frame_time) % 4
            else:
                self.walk_anim_t = 0.0
                self.walk_frame_i = 0

    def start_attack(self):
        if self.attacking:
            return
        if self.attack_cooldown > 0:
            return
        self.attacking = True
        self.attack_t = 0.0
        self.attack_frame_i = 0
        self.attack_cooldown = 0.25

    def sword_hitbox(self):
        """
        Return a rect in front of the player for sword hits.
        """
        r = self.rect.copy()
        reach = TILE // 2
        thickness = TILE // 2

        if self.facing == "up":
            return pygame.Rect(r.centerx - thickness//2, r.top - reach, thickness, reach)
        if self.facing == "down":
            return pygame.Rect(r.centerx - thickness//2, r.bottom, thickness, reach)
        if self.facing == "left":
            return pygame.Rect(r.left - reach, r.centery - thickness//2, reach, thickness)
        # right
        return pygame.Rect(r.right, r.centery - thickness//2, reach, thickness)

    def move_and_collide(self, dt, world):
        # move X
        self.rect.x += int(self.vx * dt)
        for wall in world.walls:
            if self.rect.colliderect(wall):
                if self.vx > 0:
                    self.rect.right = wall.left
                elif self.vx < 0:
                    self.rect.left = wall.right

        # move Y
        self.rect.y += int(self.vy * dt)
        for wall in world.walls:
            if self.rect.colliderect(wall):
                if self.vy > 0:
                    self.rect.bottom = wall.top
                elif self.vy < 0:
                    self.rect.top = wall.bottom

        # keep inside world bounds
        self.rect.x = clamp(self.rect.x, 0, WORLD_W * TILE - TILE)
        self.rect.y = clamp(self.rect.y, 0, WORLD_H * TILE - TILE)

    def draw(self, surf, cam):
        # pick sprite based on state
        if self.attacking:
            img = self.attack_frames[min(self.attack_frame_i, len(self.attack_frames)-1)]
        else:
            dir_frames = self.walk_frames[self.facing]
            img = dir_frames[self.walk_frame_i]

        # blink when invulnerable
        if self.invuln_t > 0 and int(self.invuln_t * 20) % 2 == 0:
            return

        surf.blit(img, (self.rect.x - cam[0], self.rect.y - cam[1]))

class Enemy(Entity):
    def __init__(self, x, y, frames_by_dir, biome_id, is_boss=False):
        super().__init__(x, y, TILE, TILE)
        self.frames = frames_by_dir
        self.facing = "down"
        self.anim_t = 0.0
        self.frame_i = 0

        self.biom = biome_id
        self.is_boss = is_boss

        self.speed = 120 if not is_boss else 140
        self.max_hp = 3 if not is_boss else 14
        self.hp = self.max_hp

        self.wander_t = random.uniform(0.4, 1.2)
        self.wander_dir = pygame.Vector2(0, 0)

        self.hit_flash_t = 0.0

    def update(self, dt, player, world):
        if self.hit_flash_t > 0:
            self.hit_flash_t -= dt

        # Simple AI:
        # - If player is close, chase.
        # - Otherwise wander.
        to_player = pygame.Vector2(player.rect.centerx - self.rect.centerx,
                                  player.rect.centery - self.rect.centery)
        dist = to_player.length()

        if dist < 260:
            if dist > 0:
                to_player.normalize_ip()
            vel = to_player * self.speed
        else:
            self.wander_t -= dt
            if self.wander_t <= 0:
                self.wander_t = random.uniform(0.6, 1.4)
                ang = random.uniform(0, math.tau)
                self.wander_dir = pygame.Vector2(math.cos(ang), math.sin(ang))
            vel = self.wander_dir * (self.speed * 0.6)

        self.vx = vel.x
        self.vy = vel.y

        # decide facing for animation
        if abs(self.vx) > abs(self.vy):
            self.facing = "right" if self.vx > 0 else "left"
        else:
            self.facing = "down" if self.vy > 0 else "up"

        self.move_and_collide(dt, world)

        # animation
        self.anim_t += dt
        frame_time = 0.14 if not self.is_boss else 0.10
        self.frame_i = int(self.anim_t / frame_time) % 4

    def move_and_collide(self, dt, world):
        # X
        self.rect.x += int(self.vx * dt)
        for wall in world.walls:
            if self.rect.colliderect(wall):
                if self.vx > 0:
                    self.rect.right = wall.left
                elif self.vx < 0:
                    self.rect.left = wall.right

        # Y
        self.rect.y += int(self.vy * dt)
        for wall in world.walls:
            if self.rect.colliderect(wall):
                if self.vy > 0:
                    self.rect.bottom = wall.top
                elif self.vy < 0:
                    self.rect.top = wall.bottom

        # keep inside world bounds
        self.rect.x = clamp(self.rect.x, 0, WORLD_W * TILE - TILE)
        self.rect.y = clamp(self.rect.y, 0, WORLD_H * TILE - TILE)

    def draw(self, surf, cam):
        img = self.frames[self.facing][self.frame_i]

        # quick flash effect when hit
        if self.hit_flash_t > 0:
            # tint by drawing a white copy (simple beginner trick)
            white = img.copy()
            white.fill((255, 255, 255, 140), special_flags=pygame.BLEND_RGBA_ADD)
            surf.blit(white, (self.rect.x - cam[0], self.rect.y - cam[1]))
        else:
            surf.blit(img, (self.rect.x - cam[0], self.rect.y - cam[1]))

# -------------------------
# World class
# -------------------------
class World:
    def __init__(self, tiles_floor_img, tiles_water_img, tiles_nature_img):
        self.tiles_floor = tiles_floor_img
        self.tiles_water = tiles_water_img
        self.tiles_nature = tiles_nature_img

        # Pre-cut biome ground tiles from TilesetFloor.png (48x48)
        # These coordinates are chosen to match your sheet layout.
        self.ground_tiles = {
            FOREST: self.cut_floor_tile(48, 144),  # grassy/dirt-ish
            DESERT: self.cut_floor_tile(0, 0),     # sandy
            ICE:    self.cut_floor_tile(0, 240),   # snow/ice
            WATER:  self.cut_floor_tile(0, 336),   # watery-looking pad
            DARK:   self.cut_floor_tile(192, 240), # dark ground
        }

        # A couple obstacle “stamps” from TilesetNature.png (48x48)
        self.tree_stamp = self.cut_nature_tile(0, 0)      # big tree top area
        self.rock_stamp = self.cut_nature_tile(240, 144)  # rocks

        self.walls = []       # list of pygame.Rect
        self.decals = []      # list of (image, x, y)
        self.portals = {}     # biome_id -> portal rect
        self.portal_active = {}  # biome_id -> bool

        self.generate_obstacles_and_portals()

    def cut_floor_tile(self, x, y):
        tile = self.tiles_floor.subsurface(pygame.Rect(x, y, 48, 48)).copy()
        return tile

    def cut_nature_tile(self, x, y):
        tile = self.tiles_nature.subsurface(pygame.Rect(x, y, 48, 48)).copy()
        return tile

    def generate_obstacles_and_portals(self):
        """
        Add some obstacles per biome + portals that unlock after bosses are defeated.
        """
        random.seed(7)

        # Portal locations (tile coords)
        # Each portal sends you to the next biome.
        portal_points = {
            FOREST: (24, 12),
            DESERT: (45, 12),
            ICE:    (24, 46),
            WATER:  (45, 46),
            DARK:   (70, 28),  # last biome portal is just "end marker"
        }

        for b, (tx, ty) in portal_points.items():
            r = pygame.Rect(tx * TILE, ty * TILE, TILE, TILE)
            self.portals[b] = r
            self.portal_active[b] = (b == FOREST)  # only forest portal starts "visible" (but locked until boss)

        # Make “walls” around the world edges
        edge_thickness = TILE
        self.walls.append(pygame.Rect(-edge_thickness, -edge_thickness, WORLD_W*TILE + 2*edge_thickness, edge_thickness))
        self.walls.append(pygame.Rect(-edge_thickness, WORLD_H*TILE, WORLD_W*TILE + 2*edge_thickness, edge_thickness))
        self.walls.append(pygame.Rect(-edge_thickness, 0, edge_thickness, WORLD_H*TILE))
        self.walls.append(pygame.Rect(WORLD_W*TILE, 0, edge_thickness, WORLD_H*TILE))

        # Sprinkle obstacles: trees/rocks (simple rectangles for collision)
        # We also place a matching decal image so it looks nice.
        for ty in range(WORLD_H):
            for tx in range(WORLD_W):
                b = biome_at(tx, ty)

                # Leave some open lanes: don't block too much
                if random.random() < 0.03 and b in (FOREST, ICE):
                    self.place_obstacle(self.tree_stamp, tx, ty, solid=True)
                elif random.random() < 0.02 and b in (DESERT, DARK):
                    self.place_obstacle(self.rock_stamp, tx, ty, solid=True)

        # Special: water biome should feel watery.
        # Add “blocked water” strips, leaving a bridge lane.
        for ty in range(32, 60):
            for tx in range(30, 60):
                if biome_at(tx, ty) == WATER:
                    # Make most of it non-walkable except a diagonal bridge corridor
                    if abs((tx - 30) - (ty - 32)) > 3:
                        self.walls.append(pygame.Rect(tx*TILE, ty*TILE, TILE, TILE))

    def place_obstacle(self, img, tx, ty, solid=True):
        x = tx * TILE
        y = ty * TILE
        self.decals.append((img, x, y))
        if solid:
            # Collision box smaller than full tile so it feels fair
            hit = pygame.Rect(x + 10, y + 12, TILE - 20, TILE - 18)
            self.walls.append(hit)

    def draw(self, surf, cam, font_small, bosses_defeated):
        # draw ground tiles
        start_tx = cam[0] // TILE
        start_ty = cam[1] // TILE
        end_tx = start_tx + VIEW_TILES_W + 2
        end_ty = start_ty + VIEW_TILES_H + 2

        for ty in range(start_ty, end_ty):
            if ty < 0 or ty >= WORLD_H:
                continue
            for tx in range(start_tx, end_tx):
                if tx < 0 or tx >= WORLD_W:
                    continue
                b = biome_at(tx, ty)
                tile = self.ground_tiles[b]
                surf.blit(tile, (tx*TILE - cam[0], ty*TILE - cam[1]))

        # decals (trees/rocks)
        for img, x, y in self.decals:
            sx = x - cam[0]
            sy = y - cam[1]
            if -TILE <= sx <= SCREEN_W and -TILE <= sy <= SCREEN_H:
                surf.blit(img, (sx, sy))

        # portals (draw simple animated rings)
        for b, rect in self.portals.items():
            # Portal to NEXT biome is active only after boss of that biome is defeated
            # (Dark portal is just an "ending pad".)
            is_unlocked = bosses_defeated.get(b, False)
            if b == DARK:
                is_unlocked = True

            # Always draw portal, but color changes when unlocked
            sx = rect.x - cam[0]
            sy = rect.y - cam[1]
            if -TILE <= sx <= SCREEN_W and -TILE <= sy <= SCREEN_H:
                if is_unlocked:
                    pygame.draw.rect(surf, (40, 255, 180), (sx+6, sy+6, TILE-12, TILE-12), 4)
                    txt = font_small.render("OPEN", True, (40, 255, 180))
                else:
                    pygame.draw.rect(surf, (255, 90, 90), (sx+6, sy+6, TILE-12, TILE-12), 4)
                    txt = font_small.render("LOCK", True, (255, 90, 90))
                surf.blit(txt, (sx+6, sy-18))

# -------------------------
# Game
# -------------------------
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Oasis Shards - Mini Zelda-like")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()

        # Fonts
        self.font = pygame.font.SysFont("consolas", 22)
        self.font_small = pygame.font.SysFont("consolas", 16)

        # Load assets
        self.assets_ok = True
        try:
            self.floor_img = load_image("TilesetFloor.png")
            self.nature_img = load_image("TilesetNature.png")
            self.water_img = load_image("TilesetWater.png")

            walk_sheet = load_image("Walk.png")
            attack_sheet = load_image("Attack.png")
            beast_sheet = load_image("Beast.png")
        except Exception as e:
            self.assets_ok = False
            self.load_error = str(e)
            return

        # Slice & scale player walk frames (Walk.png is 4x4 of 16x16)
        walk_frames = slice_sheet(walk_sheet, 16, 16)  # 16 frames
        walk_frames = [scale_img(f, SPRITE_SCALE) for f in walk_frames]

        # Map rows -> directions (common sprite layout)
        # row0=down, row1=left, row2=right, row3=up
        self.player_walk = {
            "down":  walk_frames[0:4],
            "left":  walk_frames[4:8],
            "right": walk_frames[8:12],
            "up":    walk_frames[12:16],
        }

        # Attack.png is 4 frames in one row
        attack_frames = slice_sheet(attack_sheet, 16, 16)
        attack_frames = [scale_img(f, SPRITE_SCALE) for f in attack_frames]

        # Slice & scale beast enemy frames (4x4)
        beast_frames = slice_sheet(beast_sheet, 16, 16)
        beast_frames = [scale_img(f, SPRITE_SCALE) for f in beast_frames]
        self.beast_anim = {
            "down":  beast_frames[0:4],
            "left":  beast_frames[4:8],
            "right": beast_frames[8:12],
            "up":    beast_frames[12:16],
        }

        # Build world
        self.world = World(self.floor_img, self.water_img, self.nature_img)

        # Player starts in Forest
        self.player = Player(8*TILE, 8*TILE, self.player_walk, attack_frames)

        # Boss flags
        self.bosses_defeated = {FOREST: False, DESERT: False, ICE: False, WATER: False, DARK: False}

        # Enemies list
        self.enemies = []
        self.spawn_enemies_and_bosses()

        # Small story popups
        self.message = "Find the Oasis Shards. Defeat each biome guardian to unlock the next portal."
        self.message_t = 6.0

    def spawn_enemies_and_bosses(self):
        random.seed(3)

        # Spawn regular enemies in each biome
        for _ in range(35):
            tx = random.randint(2, WORLD_W-3)
            ty = random.randint(2, WORLD_H-3)
            b = biome_at(tx, ty)
            x = tx*TILE
            y = ty*TILE

            # avoid spawning on portals
            too_close = False
            for pr in self.world.portals.values():
                if pr.collidepoint(x+TILE//2, y+TILE//2):
                    too_close = True
                    break
            if too_close:
                continue

            e = Enemy(x, y, self.beast_anim, b, is_boss=False)
            self.enemies.append(e)

        # Spawn one boss per biome (big HP)
        boss_spots = {
            FOREST: (18, 18),
            DESERT: (52, 18),
            ICE:    (18, 40),
            WATER:  (52, 40),
            DARK:   (70, 30),
        }
        for b, (tx, ty) in boss_spots.items():
            x = tx*TILE
            y = ty*TILE
            boss = Enemy(x, y, self.beast_anim, b, is_boss=True)
            self.enemies.append(boss)

    def current_biome(self):
        tx = self.player.rect.centerx // TILE
        ty = self.player.rect.centery // TILE
        return biome_at(tx, ty)

    def camera(self):
        # Center camera on player
        cx = self.player.rect.centerx - SCREEN_W//2
        cy = self.player.rect.centery - SCREEN_H//2
        cx = clamp(cx, 0, WORLD_W*TILE - SCREEN_W)
        cy = clamp(cy, 0, WORLD_H*TILE - SCREEN_H)
        return (cx, cy)

    def damage_player(self, dmg, knock_vec):
        if self.player.invuln_t > 0:
            return
        self.player.hp -= dmg
        self.player.invuln_t = 0.8

        # knockback (small)
        self.player.rect.x += int(knock_vec.x * 18)
        self.player.rect.y += int(knock_vec.y * 18)

        self.message = "Ouch! Watch your step."
        self.message_t = 1.6

        if self.player.hp <= 0:
            # simple restart
            self.player.hp = self.player.max_hp
            self.player.rect.topleft = (8*TILE, 8*TILE)
            self.message = "You fainted... and woke up at the forest edge."
            self.message_t = 3.0

    def handle_combat(self):
        # Player sword hits
        if self.player.attacking:
            sword = self.player.sword_hitbox()
            for e in self.enemies:
                if not e.alive:
                    continue
                if sword.colliderect(e.rect):
                    e.take_damage(1)
                    e.hit_flash_t = 0.12

                    # If boss dies, unlock its portal
                    if not e.alive and e.is_boss:
                        self.bosses_defeated[e.biom] = True
                        self.message = f"{BIOME_NAMES[e.biom]} guardian defeated! Portal unlocked."
                        self.message_t = 3.0

    def handle_enemy_collisions(self):
        # Enemies touching player
        for e in self.enemies:
            if not e.alive:
                continue
            if e.rect.colliderect(self.player.rect):
                knock = pygame.Vector2(self.player.rect.centerx - e.rect.centerx,
                                       self.player.rect.centery - e.rect.centery)
                if knock.length() > 0:
                    knock.normalize_ip()
                self.damage_player(1 if not e.is_boss else 2, knock)

    def handle_portals(self):
        # If player stands on a portal and it's unlocked, teleport to next biome
        b = self.current_biome()

        # Find portal you are currently standing on (if any)
        for biome_id, pr in self.world.portals.items():
            if self.player.rect.colliderect(pr):
                if biome_id == DARK:
                    # end pad
                    if self.bosses_defeated[WATER]:
                        self.message = "You reached Blackroot Keep... The Oasis Shards glow. You win!"
                        self.message_t = 6.0
                    else:
                        self.message = "The Keep is sealed by water magic. Defeat the Mirror Marsh guardian."
                        self.message_t = 3.0
                    return

                # Must defeat boss of this biome to open next portal
                if not self.bosses_defeated[biome_id]:
                    self.message = "Portal locked: defeat this biome guardian first!"
                    self.message_t = 1.4
                    return

                # Teleport to the portal in the next biome
                idx = BIOME_ORDER.index(biome_id)
                if idx < len(BIOME_ORDER) - 1:
                    next_b = BIOME_ORDER[idx + 1]
                    dst = self.world.portals[next_b]
                    self.player.rect.topleft = (dst.x, dst.y)

                    self.message = f"Entered: {BIOME_NAMES[next_b]}"
                    self.message_t = 2.2
                return

    def draw_hud(self, surf):
        # biome title
        b = self.current_biome()
        title = f"{BIOME_NAMES[b]}"
        t = self.font.render(title, True, (255, 255, 255))
        surf.blit(t, (10, 8))

        # hearts (6 max)
        for i in range(self.player.max_hp):
            x = 10 + i * 22
            y = 38
            filled = (i < self.player.hp)
            color = (255, 80, 80) if filled else (80, 30, 30)
            pygame.draw.rect(surf, color, (x, y, 18, 14))
            pygame.draw.rect(surf, (0, 0, 0), (x, y, 18, 14), 2)

        # objective line
        # Find the first biome that is not defeated yet
        target = None
        for bb in BIOME_ORDER[:-1]:
            if not self.bosses_defeated[bb]:
                target = bb
                break
        if target is None and self.bosses_defeated[WATER]:
            obj = "Objective: Step into Blackroot Keep (Dark portal)."
        else:
            obj = f"Objective: Defeat the guardian of {BIOME_NAMES[target]}."
        o = self.font_small.render(obj, True, (240, 240, 240))
        surf.blit(o, (10, SCREEN_H - 22))

        # message popup
        if self.message_t > 0:
            msg = self.font_small.render(self.message, True, (0, 0, 0))
            pad = 8
            box = pygame.Rect(10, SCREEN_H - 54, msg.get_width() + pad*2, 26)
            pygame.draw.rect(surf, (255, 255, 255), box)
            pygame.draw.rect(surf, (0, 0, 0), box, 2)
            surf.blit(msg, (box.x + pad, box.y + 5))

    def run(self):
        if not self.assets_ok:
            self.screen.fill((30, 30, 30))
            txt = self.font.render("Missing asset file:", True, (255, 255, 255))
            err = self.font_small.render(self.load_error, True, (255, 180, 180))
            self.screen.blit(txt, (20, 20))
            self.screen.blit(err, (20, 60))
            pygame.display.flip()
            # basic wait loop
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return

        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.player.start_attack()

            keys = pygame.key.get_pressed()

            # Update
            self.player.update(dt, keys, self.world)

            for e in self.enemies:
                if e.alive:
                    e.update(dt, self.player, self.world)

            # Combat & collisions
            self.handle_combat()
            self.handle_enemy_collisions()
            self.handle_portals()

            # message timer
            if self.message_t > 0:
                self.message_t -= dt

            # Cleanup dead enemies (keep bosses dead)
            self.enemies = [e for e in self.enemies if e.alive or e.is_boss]

            # Draw
            cam = self.camera()
            self.screen.fill((0, 0, 0))
            self.world.draw(self.screen, cam, self.font_small, self.bosses_defeated)

            # Enemies
            for e in self.enemies:
                if e.alive:
                    e.draw(self.screen, cam)

            # Player
            self.player.draw(self.screen, cam)

            # Sword debug (optional): uncomment to see hitbox
            # if self.player.attacking:
            #     s = self.player.sword_hitbox()
            #     pygame.draw.rect(self.screen, (255, 255, 0), (s.x-cam[0], s.y-cam[1], s.w, s.h), 2)

            # HUD
            self.draw_hud(self.screen)

            pygame.display.flip()

        pygame.quit()

# -------------------------
# Start
# -------------------------
if __name__ == "__main__":
    Game().run()