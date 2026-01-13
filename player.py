import pygame                                # Import pygame
import math                                  # Import math (for knockback if needed)
from settings import TILE, PLAYER_SPEED, PLAYER_SIZE  # Import settings

class Player:                                # Player class
    def __init__(self, x, y, sprites):       # Constructor
        self.rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)  # Player hitbox
        self.speed = PLAYER_SPEED            # Movement speed
        self.facing = "down"                 # Starting facing direction
        self.hp = 5                          # Health points
        self.rupees = 0                      # Rupees collected

        self.sword_cd = 0                    # Sword cooldown timer
        self.sword_active = 0                # Sword active timer
        self.sword_rect = pygame.Rect(0, 0, 0, 0)  # Sword hitbox

        self.sprites = sprites               # Sprite dictionary (images)

    def move_and_collide(self, dx, dy, world):   # Move player with collision
        if dx != 0:                              # If moving in X
            self.rect.x += dx                    # Move X
            self.resolve_collisions(world, "x")  # Fix collisions for X

        if dy != 0:                              # If moving in Y
            self.rect.y += dy                    # Move Y
            self.resolve_collisions(world, "y")  # Fix collisions for Y

    def resolve_collisions(self, world, axis):   # Push player out of blocked tiles
        left = self.rect.left // TILE            # Left tile index
        right = self.rect.right // TILE          # Right tile index
        top = self.rect.top // TILE              # Top tile index
        bottom = self.rect.bottom // TILE        # Bottom tile index

        for ty in range(top, bottom + 1):        # Loop tiles in Y range
            for tx in range(left, right + 1):    # Loop tiles in X range
                if world.tile_blocked(tx, ty):   # If tile blocks movement
                    tile_rect = pygame.Rect(tx * TILE, ty * TILE, TILE, TILE)  # Tile rect
                    if self.rect.colliderect(tile_rect):  # If overlapping
                        if axis == "x":          # If fixing X
                            if self.rect.centerx > tile_rect.centerx:  # Player on right side?
                                self.rect.left = tile_rect.right       # Push right
                            else:                                       # Player on left side
                                self.rect.right = tile_rect.left       # Push left
                        else:                   # If fixing Y
                            if self.rect.centery > tile_rect.centery:  # Player below?
                                self.rect.top = tile_rect.bottom       # Push down
                            else:                                       # Player above
                                self.rect.bottom = tile_rect.top       # Push up

    def swing_sword(self):                       # Create sword hitbox
        if self.sword_cd > 0:                    # If still cooling down
            return                               # Don’t swing again yet

        self.sword_cd = 18                       # Set cooldown frames
        self.sword_active = 10                   # Sword exists for 10 frames

        # Place sword rectangle based on facing direction
        if self.facing == "up":
            self.sword_rect = pygame.Rect(self.rect.centerx - 10, self.rect.top - 20, 20, 20)
        elif self.facing == "down":
            self.sword_rect = pygame.Rect(self.rect.centerx - 10, self.rect.bottom, 20, 20)
        elif self.facing == "left":
            self.sword_rect = pygame.Rect(self.rect.left - 20, self.rect.centery - 10, 20, 20)
        else:  # right
            self.sword_rect = pygame.Rect(self.rect.right, self.rect.centery - 10, 20, 20)

    def update(self, keys, world):               # Update each frame
        dx = 0                                   # X movement
        dy = 0                                   # Y movement

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= self.speed
            self.facing = "up"
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += self.speed
            self.facing = "down"
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= self.speed
            self.facing = "left"
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += self.speed
            self.facing = "right"

        # Diagonal fix (so diagonal isn't faster)
        if dx != 0 and dy != 0:
            dx = int(dx * 0.7071)
            dy = int(dy * 0.7071)

        self.move_and_collide(dx, dy, world)     # Move with collision

        if self.sword_cd > 0:
            self.sword_cd -= 1
        if self.sword_active > 0:
            self.sword_active -= 1
        else:
            self.sword_rect.size = (0, 0)

    def draw(self, screen, camera):              # Draw player
        img = self.sprites["player"][self.facing]  # Choose sprite based on facing
        if img:
            screen.blit(img, (self.rect.x - camera.pos.x, self.rect.y - camera.pos.y))
        else:
            pygame.draw.rect(screen, (240, 220, 60), camera.apply_rect(self.rect))

        # Draw sword hitbox outline (for learning)
        if self.sword_active > 0:
            sr = camera.apply_rect(self.sword_rect)
            pygame.draw.rect(screen, (255, 255, 255), sr, 2)