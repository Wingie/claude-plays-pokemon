import pygame
import random
import os
import time

# Initialize pygame
pygame.init()

# Game constants
WIDTH, HEIGHT = 800, 600
PLAYER_RADIUS = 15
ENEMY_RADIUS = 15
FOOD_RADIUS = 10
PLAYER_SPEED = 20
ENEMY_SPEED = 3
NUM_ENEMIES = 3
NUM_FOOD = 5

# Colors
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BACKGROUND = (255, 255, 255)
WHITE = (255, 255, 255)

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = PLAYER_RADIUS
        self.speed = PLAYER_SPEED
        self.score = 0
    
    def move(self, direction):
        if direction == "up":
            self.y = max(self.radius, self.y - self.speed)
        elif direction == "down":
            self.y = min(HEIGHT - self.radius, self.y + self.speed)
        elif direction == "left":
            self.x = max(self.radius, self.x - self.speed)
        elif direction == "right":
            self.x = min(WIDTH - self.radius, self.x + self.speed)
    
    def draw(self, screen):
        pygame.draw.circle(screen, BLUE, (self.x, self.y), self.radius)
    
    def collides_with(self, other):
        distance = ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
        return distance < (self.radius + other.radius)

class Enemy:
    def __init__(self):
        self.x = random.randint(ENEMY_RADIUS, WIDTH - ENEMY_RADIUS)
        self.y = random.randint(ENEMY_RADIUS, HEIGHT - ENEMY_RADIUS)
        self.radius = ENEMY_RADIUS
        self.speed = ENEMY_SPEED
        self.direction = random.choice(["up", "down", "left", "right"])
        self.direction_change_timer = 0
    
    def move(self, player):
        # Simple AI: Sometimes move randomly, sometimes chase player
        self.direction_change_timer += 1
        
        # Change direction randomly or every few seconds
        if self.direction_change_timer > 60 or random.random() < 0.01:
            if random.random() < 0.7:  # 70% chance to chase player
                # Move towards player
                if self.x < player.x:
                    self.direction = "right"
                elif self.x > player.x:
                    self.direction = "left"
                elif self.y < player.y:
                    self.direction = "down"
                elif self.y > player.y:
                    self.direction = "up"
            else:  # 30% chance to move randomly
                self.direction = random.choice(["up", "down", "left", "right"])
            self.direction_change_timer = 0
        
        # Move in the current direction
        if self.direction == "up":
            self.y = max(self.radius, self.y - self.speed)
        elif self.direction == "down":
            self.y = min(HEIGHT - self.radius, self.y + self.speed)
        elif self.direction == "left":
            self.x = max(self.radius, self.x - self.speed)
        elif self.direction == "right":
            self.x = min(WIDTH - self.radius, self.x + self.speed)
    
    def draw(self, screen):
        pygame.draw.circle(screen, RED, (self.x, self.y), self.radius)

class Food:
    def __init__(self):
        self.x = random.randint(FOOD_RADIUS, WIDTH - FOOD_RADIUS)
        self.y = random.randint(FOOD_RADIUS, HEIGHT - FOOD_RADIUS)
        self.radius = FOOD_RADIUS
    
    def draw(self, screen):
        pygame.draw.circle(screen, GREEN, (self.x, self.y), self.radius)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Claude's Game")
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_over = False
        self.player = Player(WIDTH // 2, HEIGHT // 2)
        self.enemies = [Enemy() for _ in range(NUM_ENEMIES)]
        self.foods = [Food() for _ in range(NUM_FOOD)]
        self.font = pygame.font.SysFont(None, 36)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
    
    def update(self, direction=None):
        if self.game_over:
            return

        # Move the player if a direction is provided
        if direction:
            self.player.move(direction)
        
        # Move enemies
        for enemy in self.enemies:
            enemy.move(self.player)
            
            # Check collisions with player
            if self.player.collides_with(enemy):
                self.game_over = True
        
        # Check for food collisions
        for food in self.foods[:]:
            if self.player.collides_with(food):
                self.foods.remove(food)
                self.player.score += 1
                self.foods.append(Food())  # Add new food
    
    def draw(self):
        self.screen.fill(BACKGROUND)
        
        # Draw food
        for food in self.foods:
            food.draw(self.screen)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen)
        
        # Draw player
        self.player.draw(self.screen)
        
        # Draw score
        score_text = self.font.render(f"Score: {self.player.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Draw game over message if applicable
        if self.game_over:
            game_over_text = self.font.render("GAME OVER", True, WHITE)
            self.screen.blit(game_over_text, (WIDTH // 2 - 80, HEIGHT // 2 - 18))
        
        pygame.display.flip()
    
    def take_screenshot(self, filename):
        pygame.image.save(self.screen, filename)
    
    def run_claude_step(self, direction=None):
        """
        Run a single step of the game controlled by Claude
        Returns: game state (running, game_over, score)
        """
        if not self.running:
            return False, self.game_over, self.player.score
            
        self.handle_events()
        self.update(direction)
        self.draw()
        self.clock.tick(30)  # Cap at 30 FPS
        
        return self.running, self.game_over, self.player.score 