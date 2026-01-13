import random                                          # For random map generation
import pygame                                          # For Rect objects
from settings import TILE, CHUNK_W, CHUNK_H, BIOMES, SEED  # Import settings

# Floor color per biome (used only if sprite missing)
BIOME_FLOOR_COLOR = {                                  # Dictionary for biome floor colors
    "grass": (70, 170, 70),
    "ice": (170, 220, 255),
    "water": (40, 120, 200),
    "desert": (230, 200, 120),
    "castle": (160, 160, 160),
    "dark": (60, 60, 80),
}

# Wall color per biome (used only if sprite missing)
BIOME_WALL_COLOR = {                                   # Dictionary for biome wall colors
    "grass": (40, 90, 40),
    "ice": (120, 170, 220),
    "water": (20, 70, 120),
    "desert": (170, 140, 80),
    "castle": (110, 110, 110),
    "dark": (30, 30, 45),
}

class World:                                           # World class holds maps for each biome
    def __init__(self):                                # Constructor
        self.biome_index = 0                           # Start at first biome
        self.biome_name = BIOMES[self.biome_index]     # Current biome name
        self.maps = {}                                 # Dictionary: biome -> 2D grid
        self.generate_all_biomes()                     # Build all biomes now

    def generate_all_biomes(self):                     # Generate all maps
        for i, biome in enumerate(BIOMES):             # Loop through each biome name
            rnd = random.Random(SEED + i * 999)        # Create a separate random generator
            grid = self.generate_map(rnd, biome)       # Generate that biome's map grid
            self.maps[biome] = grid                    # Store the map grid

    def generate_map(self, rnd, biome):                # Create one biome map
        grid = [[0 for _ in range(CHUNK_W)] for _ in range(CHUNK_H)]  # Start all floor

        # Add random noise for walls/water
        for y in range(CHUNK_H):                       # Loop rows
            for x in range(CHUNK_W):                   # Loop columns
                r = rnd.random()                       # Random float 0..1
                if r < 0.10:                           # 10% chance
                    grid[y][x] = 2 if biome == "water" else 1  # More water in water biome
                elif r < 0.20:                         # Next 10%
                    grid[y][x] = 1                     # Wall
                else:                                   # Otherwise
                    grid[y][x] = 0                     # Floor

        # Smooth map to create blobs
        for _ in range(4):                              # Repeat smoothing 4 times
            new = [[grid[y][x] for x in range(CHUNK_W)] for y in range(CHUNK_H)]  # Copy grid
            for y in range(CHUNK_H):                    # Loop rows
                for x in range(CHUNK_W):                # Loop columns
                    counts = {0: 0, 1: 0, 2: 0, 3: 0}    # Count types in neighbors
                    for oy in (-1, 0, 1):               # Neighbor y offset
                        for ox in (-1, 0, 1):           # Neighbor x offset
                            ny = y + oy                 # Neighbor y
                            nx = x + ox                 # Neighbor x
                            if 0 <= ny < CHUNK_H and 0 <= nx < CHUNK_W:  # Inside map?
                                counts[grid[ny][nx]] += 1  # Count neighbor tile type
                    best = max(counts, key=counts.get)  # Pick most common type
                    new[y][x] = best                    # Set smoothed tile
            grid = new                                  # Replace grid with smoothed grid

        # Make borders walls so player can’t leave map
        for x in range(CHUNK_W):                         # Loop top/bottom edges
            grid[0][x] = 1                               # Top border wall
            grid[CHUNK_H - 1][x] = 1                     # Bottom border wall
        for y in range(CHUNK_H):                         # Loop left/right edges
            grid[y][0] = 1                               # Left border wall
            grid[y][CHUNK_W - 1] = 1                     # Right border wall

        # Create safe spawn area in center
        cx = CHUNK_W // 2                                # Center tile X
        cy = CHUNK_H // 2                                # Center tile Y
        for yy in range(cy - 3, cy + 4):                 # 7x7 area vertically
            for xx in range(cx - 3, cx + 4):             # 7x7 area horizontally
                grid[yy][xx] = 0                         # Force floor

        # Place portals (type 3) at edge centers
        self.place_portals(grid)                         # Put portals into this grid

        return grid                                      # Return the finished map

    def place_portals(self, grid):                       # Put portals into the grid
        cx = CHUNK_W // 2                                # Center X tile
        cy = CHUNK_H // 2                                # Center Y tile

        grid[1][cx] = 3                                  # Portal near top edge
        grid[CHUNK_H - 2][cx] = 3                        # Portal near bottom edge
        grid[cy][1] = 3                                  # Portal near left edge
        grid[cy][CHUNK_W - 2] = 3                        # Portal near right edge

        # Make sure tiles near portals are walkable
        grid[2][cx] = 0                                  # Just below top portal
        grid[CHUNK_H - 3][cx] = 0                        # Just above bottom portal
        grid[cy][2] = 0                                  # Just right of left portal
        grid[cy][CHUNK_W - 3] = 0                        # Just left of right portal

    def next_biome(self):                                # Switch to next biome
        self.biome_index = (self.biome_index + 1) % len(BIOMES)  # Wrap around biomes
        self.biome_name = BIOMES[self.biome_index]       # Update biome name

    def tile_at(self, tx, ty):                           # Get tile type at tile coords
        if tx < 0 or ty < 0 or tx >= CHUNK_W or ty >= CHUNK_H:  # Out of bounds?
            return 1                                     # Treat as wall
        return self.maps[self.biome_name][ty][tx]         # Return tile type from map

    def tile_blocked(self, tx, ty):                      # Check if tile blocks movement
        t = self.tile_at(tx, ty)                         # Get tile type
        return t in (1, 2)                               # Walls and water block movement

    def world_size_px(self):                             # Get world size in pixels
        return CHUNK_W * TILE, CHUNK_H * TILE            # Convert tiles -> pixels

    def draw(self, screen, camera, sprites):             # Draw the world (only visible tiles)
        start_tx = int(camera.pos.x // TILE)             # Leftmost visible tile X
        start_ty = int(camera.pos.y // TILE)             # Topmost visible tile Y
        end_tx = int((camera.pos.x + screen.get_width()) // TILE) + 1   # Right bound
        end_ty = int((camera.pos.y + screen.get_height()) // TILE) + 1  # Bottom bound

        start_tx = max(0, start_tx)                      # Clamp start X
        start_ty = max(0, start_ty)                      # Clamp start Y
        end_tx = min(CHUNK_W, end_tx)                    # Clamp end X
        end_ty = min(CHUNK_H, end_ty)                    # Clamp end Y

        for ty in range(start_ty, end_ty):               # Loop visible rows
            for tx in range(start_tx, end_tx):           # Loop visible columns
                t = self.maps[self.biome_name][ty][tx]   # Tile type
                x = tx * TILE                            # Tile pixel X
                y = ty * TILE                            # Tile pixel Y

                # Choose sprite depending on tile type
                if t == 0:                               # Floor
                    img = sprites["floor"][self.biome_name]
                elif t == 1:                             # Wall
                    img = sprites["wall"][self.biome_name]
                elif t == 2:                             # Water
                    img = sprites["water_tile"]
                else:                                    # Portal
                    img = sprites["portal"]

                # Draw sprite if exists
                if img:
                    screen.blit(img, (x - camera.pos.x, y - camera.pos.y))  # Draw image
                else:
                    # Fallback colored rectangle if sprite missing
                    if t == 0:
                        color = BIOME_FLOOR_COLOR[self.biome_name]
                    elif t == 1:
                        color = BIOME_WALL_COLOR[self.biome_name]
                    elif t == 2:
                        color = (40, 120, 200)
                    else:
                        color = (255, 255, 255)

                    r = pygame.Rect(x - camera.pos.x, y - camera.pos.y, TILE, TILE)  # Tile rect
                    pygame.draw.rect(screen, color, r)     # Draw colored tile