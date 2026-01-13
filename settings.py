import pygame                       # Import pygame (we use it for Rect and key constants)

# -----------------------------
# WINDOW SETTINGS
# -----------------------------
WIDTH = 960                         # Window width in pixels
HEIGHT = 540                        # Window height in pixels
FPS = 60                            # Frames per second (game speed)

# -----------------------------
# TILE + MAP SETTINGS
# -----------------------------
TILE = 32                           # Tile size (32x32 pixels)
CHUNK_W = 40                        # Number of tiles across (map width in tiles)
CHUNK_H = 40                        # Number of tiles down (map height in tiles)

# -----------------------------
# PLAYER SETTINGS
# -----------------------------
PLAYER_SPEED = 3                    # Player speed per frame
PLAYER_SIZE = 24                    # Player rectangle size (hitbox size)

# -----------------------------
# SPAWN SETTINGS
# -----------------------------
ENEMY_COUNT = 14                    # How many enemies to spawn
RUPEE_COUNT = 40                    # How many rupees to spawn

# -----------------------------
# RANDOM SEED
# -----------------------------
SEED = 12345                        # Seed for consistent map generation

# -----------------------------
# BIOMES (6 WORLDS)
# -----------------------------
BIOMES = ["grass", "ice", "water", "desert", "castle", "dark"]  # Names of biomes

# -----------------------------
# TILE TYPES (IN THE MAP GRID)
# -----------------------------
# 0 = floor (walkable)
# 1 = wall (blocked)
# 2 = water (blocked)
# 3 = portal (walkable, changes biome)

# -----------------------------
# UI COLORS
# -----------------------------
C_BG = (0, 0, 0)                    # Background color
C_UI = (20, 20, 20)                 # UI text color

# -----------------------------
# HELPER: CLAMP FUNCTION
# -----------------------------
def clamp(v, a, b):                 # v is the value, a is min, b is max
    return max(a, min(b, v))        # Keep v inside the [a..b] range