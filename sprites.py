import pygame
import random


class Brick(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, color, points=10, hits=1):
        super().__init__()
        # simple filled rectangle (original style)
        self.image = pygame.Surface((w, h))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.hits = hits
        self.points = points

    def hit(self):
        self.hits -= 1
        return self.hits <= 0


class Paddle(pygame.sprite.Sprite):
    def __init__(self, x, y, w=100, h=16, speed=7, color=(200, 200, 200)):
        super().__init__()
        self.base_width = w
        self.base_height = h
        self.base_color = color
        self.image = pygame.Surface((w, h))
        self.image.fill(color)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.speed = speed
        # widen state
        self.widened_until = 0
        self.widened_duration_ms = 0
        # keep a copy of base image for resets
        self._base_image = self.image.copy()

    def update(self, keys, screen_width):
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        # keep on screen
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > screen_width:
            self.rect.right = screen_width

    def widen(self, multiplier=1.5, duration_ms=10000):
        now = pygame.time.get_ticks()
        new_w = int(self.base_width * multiplier)
        try:
            self.image = pygame.transform.scale(self._base_image, (new_w, self.base_height))
            # preserve bottom center
            mid = self.rect.midbottom
            self.rect = self.image.get_rect(midbottom=mid)
            self.widened_duration_ms = duration_ms
            self.widened_until = max(self.widened_until, now + duration_ms)
        except Exception:
            # fallback: do nothing
            pass

    def reset_width(self):
        try:
            mid = self.rect.midbottom
            self.image = self._base_image.copy()
            self.rect = self.image.get_rect(midbottom=mid)
            self.widened_until = 0
            self.widened_duration_ms = 0
        except Exception:
            pass


class Ball(pygame.sprite.Sprite):
    def __init__(self, x, y, radius=8, color=(255, 255, 255)):
        super().__init__()
        self.radius = radius
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.rect = self.image.get_rect(center=(x, y))
        self.vel = pygame.math.Vector2(0, 0)
        # slightly increased base speed
        self.speed = 4.5
        self.stuck = True

    def launch(self):
        if self.stuck:
            angle = random.uniform(-60, -120)
            # create initial velocity with base speed
            self.vel = pygame.math.Vector2(self.speed, 0).rotate(angle)
            self.stuck = False

    def update(self):
        if not self.stuck:
            self.rect.x += int(self.vel.x)
            self.rect.y += int(self.vel.y)

    def set_speed(self, speed):
        # keep direction but change magnitude
        if self.vel.length() == 0:
            self.vel = pygame.math.Vector2(speed, -abs(speed))
        else:
            self.vel = self.vel.normalize() * speed

    def bounce_x(self):
        self.vel.x *= -1

    def bounce_y(self):
        self.vel.y *= -1


class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, kind='widen'):
        super().__init__()
        self.kind = kind
        self.image = pygame.Surface((20, 20))
        if kind == 'widen':
            self.image.fill((255, 200, 50))
        else:
            self.image.fill((50, 200, 100))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 3

    def update(self):
        self.rect.y += self.speed
