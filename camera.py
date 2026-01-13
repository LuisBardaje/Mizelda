import pygame                               # Import pygame
from settings import WIDTH, HEIGHT, clamp   # Import screen size + clamp helper

class Camera:                               # Camera class (tracks the view offset)
    def __init__(self):                     # Constructor
        self.pos = pygame.Vector2(0, 0)     # Camera position offset (x,y)

    def update(self, target_rect, world_px_w, world_px_h):     # Follow target (player)
        self.pos.x = target_rect.centerx - WIDTH // 2          # Center camera on player X
        self.pos.y = target_rect.centery - HEIGHT // 2         # Center camera on player Y

        max_x = max(0, world_px_w - WIDTH)                     # Max camera X
        max_y = max(0, world_px_h - HEIGHT)                    # Max camera Y

        self.pos.x = clamp(self.pos.x, 0, max_x)               # Clamp camera X to world
        self.pos.y = clamp(self.pos.y, 0, max_y)               # Clamp camera Y to world

    def apply_rect(self, rect):                                 # Convert world rect -> screen rect
        return pygame.Rect(                                     # Return a new rect
            rect.x - self.pos.x,                                # Move rect left by camera X
            rect.y - self.pos.y,                                # Move rect up by camera Y
            rect.w,                                             # Keep width
            rect.h                                              # Keep height
        )