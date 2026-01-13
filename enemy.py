import pygame                       # Import pygame
import random                       # Import random
from settings import TILE           # Import tile size

class Enemy:                        # Enemy class
    def __init__(self, x, y, sprites):            # Constructor
        self.rect = pygame.Rect(x, y, 22, 22)     # Enemy hitbox
        self.speed = 2                             # Enemy speed
        self.hp = 2                                # Enemy health
        self.hit_cd = 0                            # Hit cooldown (prevents spam damage)
        self.change_timer = random.randint(25, 80) # Timer until direction changes
        self.dir = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))  # Random dir

        if self.dir.length() > 0:                  # If not zero vector
            self.dir = self.dir.normalize()        # Normalize direction

        self.sprites = sprites                     # Sprite dictionary

    def touch_block(self, world):                  # Check collision with blocked tiles
        left = self.rect.left // TILE              # Left tile index
        right = self.rect.right // TILE            # Right tile index
        top = self.rect.top // TILE                # Top tile index
        bottom = self.rect.bottom // TILE          # Bottom tile index

        for ty in range(top, bottom + 1):          # Loop nearby tiles Y
            for tx in range(left, right + 1):      # Loop nearby tiles X
                if world.tile_blocked(tx, ty):     # If blocked tile
                    tile_rect = pygame.Rect(tx * TILE, ty * TILE, TILE, TILE)  # Tile rect
                    if self.rect.colliderect(tile_rect):  # If overlapping
                        return True                # Collision happened
        return False                               # No collision

    def update(self, world):                       # Update enemy movement
        self.change_timer -= 1                     # Decrease timer
        if self.change_timer <= 0:                 # If timer ends
            self.change_timer = random.randint(25, 80)  # Reset timer
            self.dir = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))  # New dir
            if self.dir.length() > 0:              # If not zero
                self.dir = self.dir.normalize()    # Normalize

        dx = int(self.dir.x * self.speed)          # Movement X
        dy = int(self.dir.y * self.speed)          # Movement Y

        self.rect.x += dx                           # Apply X movement
        if self.touch_block(world):                 # If collided
            self.rect.x -= dx                       # Undo X
            self.dir.x *= -1                        # Bounce

        self.rect.y += dy                           # Apply Y movement
        if self.touch_block(world):                 # If collided
            self.rect.y -= dy                       # Undo Y
            self.dir.y *= -1                        # Bounce

        if self.hit_cd > 0:                         # If cooldown active
            self.hit_cd -= 1                        # Decrease it

    def draw(self, screen, camera):                 # Draw enemy
        img = self.sprites["enemy"]                 # Enemy sprite
        if img:
            screen.blit(img, (self.rect.x - camera.pos.x, self.rect.y - camera.pos.y))
        else:
            pygame.draw.rect(screen, (220, 70, 70), camera.apply_rect(self.rect))