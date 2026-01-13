import pygame                         # Import pygame

class Rupee:                          # Rupee class
    def __init__(self, x, y):         # Constructor
        self.rect = pygame.Rect(x, y, 14, 14)  # Rupee hitbox

    def draw(self, screen, camera, sprite):    # Draw rupee
        if sprite:
            screen.blit(sprite, (self.rect.x - camera.pos.x, self.rect.y - camera.pos.y))
        else:
            pygame.draw.rect(screen, (30, 220, 70), camera.apply_rect(self.rect))