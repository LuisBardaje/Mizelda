import pygame                              # Import pygame
import random                              # Import random
import os                                  # Import os (folders/files)
import sys                                 # Import sys (exit)
import math                                # Import math (knockback)

from settings import (                     # Import many settings
    WIDTH, HEIGHT, FPS, TILE, CHUNK_W, CHUNK_H,
    BIOMES, C_BG, C_UI, ENEMY_COUNT, RUPEE_COUNT
)

from camera import Camera                  # Import Camera class
from world import World                    # Import World class
from player import Player                  # Import Player class
from enemy import Enemy                    # Import Enemy class
from items import Rupee                    # Import Rupee class

# -----------------------------
# CREATE PLACEHOLDER PNG ASSETS
# -----------------------------
def ensure_assets():                       # Function to make PNGs automatically
    os.makedirs("assets", exist_ok=True)   # Create assets folder if missing

    def save_tile(path, color, border=None):          # Helper to save 32x32 tile
        surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)  # Create transparent surface
        surf.fill(color)                               # Fill with color
        if border:                                     # If border requested
            pygame.draw.rect(surf, border, surf.get_rect(), 2)  # Draw border
        pygame.image.save(surf, path)                  # Save PNG to disk

    biome_floor = {                                    # Floor color per biome
        "grass": (70, 170, 70),
        "ice": (170, 220, 255),
        "water": (50, 140, 220),
        "desert": (230, 200, 120),
        "castle": (160, 160, 160),
        "dark": (60, 60, 80),
    }

    biome_wall = {                                     # Wall color per biome
        "grass": (40, 90, 40),
        "ice": (120, 170, 220),
        "water": (20, 70, 120),
        "desert": (170, 140, 80),
        "castle": (110, 110, 110),
        "dark": (30, 30, 45),
    }

    for biome in BIOMES:                               # Loop each biome
        save_tile(f"assets/floor_{biome}.png", biome_floor[biome], border=(0, 0, 0, 60))  # Save floor tile
        save_tile(f"assets/wall_{biome}.png", biome_wall[biome], border=(0, 0, 0, 90))    # Save wall tile

    save_tile("assets/portal.png", (255, 255, 255), border=(0, 0, 0))  # Portal tile
    save_tile("assets/water_tile.png", (40, 120, 200), border=(0, 0, 0, 80))  # Water tile

    rupee = pygame.Surface((14, 14), pygame.SRCALPHA)   # Create rupee surface
    pygame.draw.polygon(rupee, (30, 220, 70), [(7, 0), (13, 7), (7, 13), (0, 7)])  # Diamond shape
    pygame.draw.polygon(rupee, (0, 0, 0, 120), [(7, 1), (12, 7), (7, 12), (1, 7)], 1)  # Outline
    pygame.image.save(rupee, "assets/rupee.png")        # Save rupee png

    enemy = pygame.Surface((22, 22), pygame.SRCALPHA)   # Create enemy surface
    enemy.fill((220, 70, 70))                           # Fill with red
    pygame.draw.rect(enemy, (0, 0, 0, 90), enemy.get_rect(), 2)  # Border
    pygame.image.save(enemy, "assets/enemy.png")        # Save enemy png

    for face in ["up", "down", "left", "right"]:        # Make 4 player sprites
        pl = pygame.Surface((24, 24), pygame.SRCALPHA)  # Create player surface
        pl.fill((240, 220, 60))                         # Yellow fill
        pygame.draw.rect(pl, (0, 0, 0, 90), pl.get_rect(), 2)  # Border

        if face == "up":                                # Direction marker up
            pygame.draw.polygon(pl, (0, 0, 0), [(12, 3), (8, 9), (16, 9)])
        elif face == "down":                            # Direction marker down
            pygame.draw.polygon(pl, (0, 0, 0), [(12, 21), (8, 15), (16, 15)])
        elif face == "left":                            # Direction marker left
            pygame.draw.polygon(pl, (0, 0, 0), [(3, 12), (9, 8), (9, 16)])
        else:                                           # Direction marker right
            pygame.draw.polygon(pl, (0, 0, 0), [(21, 12), (15, 8), (15, 16)])

        pygame.image.save(pl, f"assets/player_{face}.png")  # Save player sprite

# -----------------------------
# LOAD SPRITES FROM DISK
# -----------------------------
def load_sprites():                                     # Load images into dictionary
    sprites = {                                         # Create sprite dict
        "floor": {},                                    # Floor tiles per biome
        "wall": {},                                     # Wall tiles per biome
        "portal": None,                                 # Portal sprite
        "water_tile": None,                             # Water sprite
        "rupee": None,                                  # Rupee sprite
        "enemy": None,                                  # Enemy sprite
        "player": {"up": None, "down": None, "left": None, "right": None},  # Player sprites
    }

    for biome in BIOMES:                                # Load biome tiles
        sprites["floor"][biome] = pygame.image.load(f"assets/floor_{biome}.png").convert_alpha()
        sprites["wall"][biome] = pygame.image.load(f"assets/wall_{biome}.png").convert_alpha()

    sprites["portal"] = pygame.image.load("assets/portal.png").convert_alpha()       # Load portal
    sprites["water_tile"] = pygame.image.load("assets/water_tile.png").convert_alpha()  # Load water tile
    sprites["rupee"] = pygame.image.load("assets/rupee.png").convert_alpha()         # Load rupee
    sprites["enemy"] = pygame.image.load("assets/enemy.png").convert_alpha()         # Load enemy

    for face in ["up", "down", "left", "right"]:         # Load player faces
        sprites["player"][face] = pygame.image.load(f"assets/player_{face}.png").convert_alpha()

    return sprites                                      # Return sprite dictionary

# -----------------------------
# FIND RANDOM WALKABLE SPOT
# -----------------------------
def find_walkable_spot(world, rnd):                     # Find a tile that is floor
    while True:                                         # Keep trying
        tx = rnd.randint(2, CHUNK_W - 3)                # Random tile X
        ty = rnd.randint(2, CHUNK_H - 3)                # Random tile Y
        if world.tile_at(tx, ty) == 0:                  # Must be floor
            return tx * TILE + 5, ty * TILE + 5         # Return pixel position

# -----------------------------
# MAIN GAME FUNCTION
# -----------------------------
def main():                                             # Main function
    pygame.init()                                       # Initialize pygame

    screen = pygame.display.set_mode((WIDTH, HEIGHT))   # Create window
    pygame.display.set_caption("Beginner Zelda: 6 Biomes + Portals")  # Window title
    clock = pygame.time.Clock()                         # Clock for FPS
    font = pygame.font.SysFont(None, 24)                # Font for UI text

    ensure_assets()                                     # Create assets PNGs
    sprites = load_sprites()                            # Load sprites into memory

    world = World()                                     # Create world (all biomes inside)
    camera = Camera()                                   # Create camera

    spawn_x = (CHUNK_W // 2) * TILE + 4                 # Spawn at center X
    spawn_y = (CHUNK_H // 2) * TILE + 4                 # Spawn at center Y
    player = Player(spawn_x, spawn_y, sprites)          # Create player

    rnd = random.Random(999)                            # Random generator for spawns
    enemies = []                                        # Enemy list
    rupees = []                                         # Rupee list

    def respawn_entities():                             # Function to spawn enemies+rupees
        enemies.clear()                                 # Remove old enemies
        rupees.clear()                                  # Remove old rupees

        for _ in range(ENEMY_COUNT):                    # Spawn enemies
            x, y = find_walkable_spot(world, rnd)       # Find floor spot
            enemies.append(Enemy(x, y, sprites))        # Add enemy

        for _ in range(RUPEE_COUNT):                    # Spawn rupees
            x, y = find_walkable_spot(world, rnd)       # Find floor spot
            rupees.append(Rupee(x + 6, y + 6))          # Add rupee

    respawn_entities()                                  # Spawn first time

    running = True                                      # Loop flag
    while running:                                      # Main game loop
        clock.tick(FPS)                                 # Limit FPS

        for event in pygame.event.get():                # Read events
            if event.type == pygame.QUIT:               # Window closed
                running = False                         # Stop loop

            if event.type == pygame.KEYDOWN:            # Key pressed
                if event.key == pygame.K_ESCAPE:        # ESC pressed
                    running = False                     # Quit game
                if event.key == pygame.K_SPACE:         # SPACE pressed
                    player.swing_sword()                # Attack

        keys = pygame.key.get_pressed()                 # Get held keys
        player.update(keys, world)                      # Update player movement

        for e in enemies:                               # Update enemies
            if e.hp > 0:                                # Only alive
                e.update(world)                         # Move enemy

        if player.sword_active > 0:                     # If sword exists
            for e in enemies:                           # Check all enemies
                if e.hp > 0 and e.hit_cd == 0 and player.sword_rect.colliderect(e.rect):
                    e.hp -= 1                           # Damage enemy
                    e.hit_cd = 20                       # Enemy invul frames

        for e in enemies:                               # Enemy touches player
            if e.hp > 0 and e.hit_cd == 0 and e.rect.colliderect(player.rect):
                player.hp -= 1                          # Player takes damage
                e.hit_cd = 30                           # Stop spam damage

                dx = player.rect.centerx - e.rect.centerx   # Knockback direction X
                dy = player.rect.centery - e.rect.centery   # Knockback direction Y
                mag = max(1, math.hypot(dx, dy))            # Distance (avoid 0)
                player.move_and_collide(int((dx / mag) * 18), int((dy / mag) * 18), world)  # Push back

        for r in rupees[:]:                             # Loop copy of rupees
            if r.rect.colliderect(player.rect):         # If player touches rupee
                rupees.remove(r)                        # Remove rupee
                player.rupees += 1                      # Add to score

        p_tx = player.rect.centerx // TILE              # Player tile X
        p_ty = player.rect.centery // TILE              # Player tile Y

        if world.tile_at(p_tx, p_ty) == 3:              # If standing on portal tile
            world.next_biome()                          # Switch biome
            player.rect.topleft = (spawn_x, spawn_y)    # Reset to center
            respawn_entities()                          # Respawn enemies/rupees

        if player.hp <= 0:                              # If player died
            player.hp = 5                               # Reset HP
            player.rupees = 0                           # Reset rupees
            player.rect.topleft = (spawn_x, spawn_y)    # Reset position

        world_w_px, world_h_px = world.world_size_px()  # World size pixels
        camera.update(player.rect, world_w_px, world_h_px)  # Update camera

        screen.fill(C_BG)                               # Clear screen background
        world.draw(screen, camera, sprites)             # Draw tiles

        for r in rupees:                                # Draw rupees
            r.draw(screen, camera, sprites["rupee"])    # Draw rupee sprite

        for e in enemies:                               # Draw enemies
            if e.hp > 0:                                # Only alive
                e.draw(screen, camera)                  # Draw enemy

        player.draw(screen, camera)                     # Draw player

        ui = f"Biome: {world.biome_name}   HP: {player.hp}   Rupees: {player.rupees}   (Stand on PORTAL to change biome)"
        screen.blit(font.render(ui, True, C_UI), (10, 10))   # Draw UI line

        tip = "Move: WASD/Arrows | Attack: SPACE | Quit: ESC"
        screen.blit(font.render(tip, True, C_UI), (10, 34))  # Draw help line

        pygame.display.flip()                           # Update screen

    pygame.quit()                                       # Close pygame
    sys.exit()                                          # Exit program

if __name__ == "__main__":                              # If this file is run directly
    main()                                              # Run main()