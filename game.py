import sys
import os
import json
import random
import pygame
from sprites import Brick, Paddle, Ball, PowerUp


class Game:
    """A simple Brick Breaker (Breakout-like) game using OOP and Pygame.

    Controls:
    - Left/Right arrows to move paddle
    - Space to launch ball
    - R to restart after win/lose
    - P to pause
    """

    def __init__(self, width=800, height=600):
        pygame.init()
        pygame.display.set_caption("Block Buster - OOP Pygame")
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.fps = 60

        # Game state
        self.score = 0
        self.lives = 3
        self.running = True
        self.paused = False
        self.level = 1
        self.highscore = 0
        self.save_file = os.path.join(os.path.dirname(__file__), 'save.json')
        self._load_save()

        # sounds (optional)
        self.sounds = {}
        try:
            pygame.mixer.init()
            assets = os.path.join(os.path.dirname(__file__), 'assets')
            self.sounds['brick'] = pygame.mixer.Sound(os.path.join(assets, 'brick.wav')) if os.path.exists(os.path.join(assets, 'brick.wav')) else None
            self.sounds['paddle'] = pygame.mixer.Sound(os.path.join(assets, 'paddle.wav')) if os.path.exists(os.path.join(assets, 'paddle.wav')) else None
            self.sounds['powerup'] = pygame.mixer.Sound(os.path.join(assets, 'powerup.wav')) if os.path.exists(os.path.join(assets, 'powerup.wav')) else None
        except Exception:
            self.sounds = {}

        # Sprites
        self.all_sprites = pygame.sprite.Group()
        self.bricks = pygame.sprite.Group()
        self.paddle_group = pygame.sprite.Group()
        self.ball_group = pygame.sprite.Group()
        
        # powerup tuning
        self.POWERUP_SPAWN_CHANCE = 0.22  # probability a destroyed brick drops any powerup
        self.WIDEN_PROB = 0.7  # probability that a spawned powerup is a 'widen' (vs 'life')

        self._create_ui()

    def _load_save(self):
        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.highscore = int(data.get('highscore', 0))
        except Exception:
            self.highscore = 0

    def _save(self):
        try:
            with open(self.save_file, 'w', encoding='utf-8') as f:
                json.dump({'highscore': int(self.highscore)}, f)
        except Exception:
            pass

    def _create_ui(self):
        # Paddle
        self.paddle = Paddle(self.width // 2, self.height - 30)
        self.paddle_group.add(self.paddle)
        self.all_sprites.add(self.paddle)

        # Ball
        self.ball = Ball(self.width // 2, self.paddle.rect.top - 10)
        self.ball_group.add(self.ball)
        self.all_sprites.add(self.ball)

        # Bricks grid
        cols = min(14, 8 + self.level)  # increase columns slowly
        base_rows = min(8, 4 + (self.level - 1) // 1)  # increase rows with level
        rows = base_rows + 1  # extra blue row
        brick_w = self.width // cols
        brick_h = 24
        # colors list now includes point values per row (higher rows = more points)
        colors = [
            ((70, 130, 255), 60),   # blue top row
            ((200, 60, 60), 50),   # strong/high-value
            ((200, 120, 60), 40),
            ((200, 200, 60), 30),
            ((60, 200, 120), 20),
            ((170, 210, 255), 10),  # light blue, lower value
        ]
        for row in range(rows):
            for col in range(cols):
                x = col * brick_w
                y = 60 + row * brick_h
                color, pts = colors[row % len(colors)]
                brick = Brick(x + 2, y + 2, brick_w - 4, brick_h - 4, color, points=pts)
                self.bricks.add(brick)
                self.all_sprites.add(brick)

        # powerups group
        self.powerups = pygame.sprite.Group()

    def restart(self):
        # reset groups and state
        self.all_sprites.empty()
        self.bricks.empty()
        self.paddle_group.empty()
        self.ball_group.empty()
        self.score = 0
        self.lives = 3
        self.level = 1
        # resume game state
        self.paused = False
        self.running = True
        # recreate UI
        self._create_ui()

    def run(self):
        while self.running:
            dt = self.clock.tick(self.fps)
            self._handle_events()
            if not self.paused:
                self._update()
            self._draw()
        pygame.quit()
        sys.exit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.ball.launch()
                if event.key == pygame.K_r:
                    # restart on R
                    self.restart()
                if event.key == pygame.K_p:
                    self.paused = not self.paused

    def _update(self):
        keys = pygame.key.get_pressed()
        self.paddle.update(keys, self.width)

        # If ball is stuck to paddle, follow it
        if self.ball.stuck:
            self.ball.rect.centerx = self.paddle.rect.centerx
            self.ball.rect.bottom = self.paddle.rect.top - 2
        self.ball.update()

        # Wall collisions
        if self.ball.rect.left <= 0 or self.ball.rect.right >= self.width:
            self.ball.bounce_x()
        if self.ball.rect.top <= 0:
            self.ball.bounce_y()

        # Paddle collision
        if pygame.sprite.spritecollide(self.ball, self.paddle_group, False):
            # reflect based on where it hits the paddle
            offset = (self.ball.rect.centerx - self.paddle.rect.centerx) / (self.paddle.rect.width / 2)
            bounce_angle = offset * 60  # degrees
            # compute current speed magnitude
            current_speed = self.ball.vel.length() if self.ball.vel.length() != 0 else self.ball.speed
            # slightly stronger speed increase on paddle hit than before
            new_speed = min(14, current_speed * 1.05 + 0.2)
            # set new velocity keeping angle
            self.ball.vel = pygame.math.Vector2(new_speed, 0).rotate(-bounce_angle)
            # ensure it moves upward
            if self.ball.vel.y > 0:
                self.ball.vel.y *= -1

        # Brick collisions
        collided = pygame.sprite.spritecollide(self.ball, self.bricks, False)
        if collided:
            # bounce in y-direction on brick hit and remove brick
            self.ball.bounce_y()
            for brick in collided:
                dead = brick.hit()
                if dead:
                    # chance to spawn powerup (configured)
                    if random.random() < self.POWERUP_SPAWN_CHANCE:
                        pu_type = 'widen' if random.random() < self.WIDEN_PROB else 'life'
                        pu = PowerUp(brick.rect.centerx, brick.rect.centery, pu_type)
                        self.powerups.add(pu)
                        self.all_sprites.add(pu)
                    brick.kill()
                    # add points based on brick's assigned value
                    try:
                        self.score += int(brick.points)
                    except Exception:
                        self.score += 10
                    if self.sounds.get('brick'):
                        try:
                            self.sounds['brick'].play()
                        except Exception:
                            pass

        # Powerups movement and collisions
        for pu in list(self.powerups):
            pu.update()
            if pu.rect.top > self.height:
                pu.kill()
            if pygame.sprite.spritecollide(pu, self.paddle_group, False):
                # apply effect
                if pu.kind == 'widen':
                    # 1.5x width for 20 seconds
                    try:
                        self.paddle.widen(multiplier=1.5, duration_ms=20000)
                    except Exception:
                        pass
                elif pu.kind == 'life':
                    self.lives += 1
                try:
                    if self.sounds.get('powerup'):
                        self.sounds['powerup'].play()
                except Exception:
                    pass
                pu.kill()

        # bottom of screen -> lose life
        if self.ball.rect.top > self.height:
            self.lives -= 1
            if self.lives <= 0:
                self.paused = True
            else:
                # reset ball to paddle
                self.ball.stuck = True
                self.ball.vel = pygame.math.Vector2(0, 0)
                self.ball.rect.center = (self.paddle.rect.centerx, self.paddle.rect.top - 10)

        # win check -> next level
        if len(self.bricks) == 0:
            # increase level, increase ball speed a bit, rebuild bricks
            self.level += 1
            # increase ball base speed
            self.ball.speed = min(12, self.ball.speed + 0.7)
            # reset ball stuck to paddle and rebuild
            self.ball.stuck = True
            self.ball.vel = pygame.math.Vector2(0, 0)
            # create new layout
            self.all_sprites.empty()
            self.bricks.empty()
            self.paddle_group.empty()
            self.ball_group.empty()
            self._create_ui()

        # update highscore
        if self.score > self.highscore:
            self.highscore = self.score
            self._save()

        # check widen expiration
        try:
            now = pygame.time.get_ticks()
            if getattr(self.paddle, 'widened_until', 0) and now > self.paddle.widened_until:
                self.paddle.reset_width()
        except Exception:
            pass

    def _draw(self):
        self.screen.fill((24, 24, 30))
        self.all_sprites.draw(self.screen)

        # HUD
        font = pygame.font.SysFont(None, 28)
        score_surf = font.render(f"Score: {self.score}", True, (230, 230, 230))
        lives_surf = font.render(f"Lives: {self.lives}", True, (230, 230, 230))
        level_surf = font.render(f"Level: {self.level}", True, (230, 230, 230))
        hs_surf = font.render(f"High: {self.highscore}", True, (230, 230, 230))
        self.screen.blit(score_surf, (10, 10))
        self.screen.blit(level_surf, (10, 36))
        self.screen.blit(hs_surf, (self.width // 2 - hs_surf.get_width() // 2, 10))
        self.screen.blit(lives_surf, (self.width - lives_surf.get_width() - 10, 10))

        if self.paused:
            large = pygame.font.SysFont(None, 64)
            if len(self.bricks) == 0:
                text = "You Win! Press R to play again"
            else:
                text = "Game Over - Press R to restart"
            text_surf = large.render(text, True, (255, 255, 255))
            rect = text_surf.get_rect(center=(self.width // 2, self.height // 2))
            self.screen.blit(text_surf, rect)

        # Draw widen progress bar (if active)
        try:
            now = pygame.time.get_ticks()
            widened_until = getattr(self.paddle, 'widened_until', 0)
            duration = getattr(self.paddle, 'widened_duration_ms', 0)
            if widened_until and now < widened_until and duration > 0:
                remaining = max(0, widened_until - now)
                frac = max(0.0, min(1.0, remaining / duration))
                bar_w = int(self.paddle.rect.width)
                bar_h = 8
                bar_x = self.paddle.rect.left
                bar_y = self.paddle.rect.top - 12
                # background
                pygame.draw.rect(self.screen, (50, 50, 50), (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4))
                # filled portion (right-to-left fill)
                fill_w = int(bar_w * frac)
                pygame.draw.rect(self.screen, (100, 220, 100), (bar_x, bar_y, fill_w, bar_h))
                # outline
                pygame.draw.rect(self.screen, (200, 200, 200), (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4), 1)
                # seconds text
                sec = int((remaining + 999) / 1000)
                small = pygame.font.SysFont(None, 20)
                txt = small.render(f"{sec}s", True, (230, 230, 230))
                self.screen.blit(txt, (bar_x + bar_w + 6, bar_y - 2))
        except Exception:
            pass

        pygame.display.flip()
