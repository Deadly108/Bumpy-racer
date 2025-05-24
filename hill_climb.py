import pygame
import sys
import math
import random
import os

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
GRAVITY = 0.5

# Colors
GROUND_COLOR = (100, 80, 60)
SKY_COLOR = (135, 206, 235)
CAR_COLOR = (200, 0, 0)
WHEEL_COLOR = (30, 30, 30)
FUEL_COLOR = (50, 200, 50)
FUEL_BG_COLOR = (100, 100, 100)
COIN_COLOR = (255, 215, 0)
CLOUD_COLOR = (255, 255, 255)

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hill Climb Racing Clone")
clock = pygame.time.Clock()

# Load or create images
def create_car_image():
    car_img = pygame.Surface((80, 40), pygame.SRCALPHA)
    # Car body
    pygame.draw.rect(car_img, (180, 0, 0), (5, 5, 70, 20), border_radius=5)
    # Windshield
    pygame.draw.polygon(car_img, (200, 230, 255), [(55, 5), (70, 5), (65, -5), (50, -5)])
    # Windows
    pygame.draw.rect(car_img, (200, 230, 255), (30, 5, 20, 10))
    # Headlights
    pygame.draw.rect(car_img, (255, 255, 200), (70, 10, 5, 5))
    # Exhaust pipe
    pygame.draw.rect(car_img, (50, 50, 50), (0, 15, 5, 5))
    return car_img

def create_wheel_image(radius):
    wheel_img = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    # Outer tire
    pygame.draw.circle(wheel_img, (30, 30, 30), (radius, radius), radius)
    # Inner rim
    pygame.draw.circle(wheel_img, (150, 150, 150), (radius, radius), radius-4)
    # Hub
    pygame.draw.circle(wheel_img, (80, 80, 80), (radius, radius), radius/2)
    # Spokes
    for i in range(6):
        angle = i * math.pi / 3
        x1 = radius + (radius/2) * math.cos(angle)
        y1 = radius + (radius/2) * math.sin(angle)
        x2 = radius + (radius-4) * math.cos(angle)
        y2 = radius + (radius-4) * math.sin(angle)
        pygame.draw.line(wheel_img, (30, 30, 30), (x1, y1), (x2, y2), 2)
    return wheel_img

def create_coin_image(radius):
    coin_img = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    # Outer circle
    pygame.draw.circle(coin_img, COIN_COLOR, (radius, radius), radius)
    # Inner circle
    pygame.draw.circle(coin_img, (255, 235, 0), (radius, radius), radius-2)
    # Dollar sign
    font = pygame.font.SysFont(None, radius*2)
    text = font.render("$", True, (255, 255, 255))
    text_rect = text.get_rect(center=(radius, radius))
    coin_img.blit(text, text_rect)
    return coin_img

class Cloud:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = random.randint(60, 120)
        self.height = random.randint(30, 50)
        self.speed = random.uniform(0.2, 0.5)
        
    def update(self):
        self.x += self.speed
        if self.x > WIDTH + 200:
            self.x = -self.width - random.randint(0, 100)
            
    def draw(self, screen, camera_x):
        # Apply parallax effect (clouds move slower than terrain)
        parallax_x = self.x - camera_x * 0.2
        
        # Only draw if visible
        if -self.width < parallax_x < WIDTH:
            # Draw multiple circles for cloud shape
            for i in range(3):
                x_offset = i * (self.width // 3)
                pygame.draw.circle(screen, CLOUD_COLOR, 
                                  (int(parallax_x + x_offset), int(self.y)), 
                                  self.height // 2)
            pygame.draw.circle(screen, CLOUD_COLOR, 
                              (int(parallax_x + self.width // 2), int(self.y - 10)), 
                              self.height // 2)

class Mountain:
    def __init__(self, x, height):
        self.x = x
        self.height = height
        self.width = random.randint(300, 500)
        self.color = (70, 80, 90)
        
    def draw(self, screen, camera_x):
        # Apply parallax effect (mountains move slower than terrain)
        parallax_x = self.x - camera_x * 0.5
        
        # Only draw if visible
        if -self.width < parallax_x < WIDTH:
            # Draw triangle for mountain
            points = [
                (parallax_x, HEIGHT),
                (parallax_x + self.width // 2, HEIGHT - self.height),
                (parallax_x + self.width, HEIGHT)
            ]
            pygame.draw.polygon(screen, self.color, points)
            
            # Draw snow cap
            snow_points = [
                (parallax_x + self.width // 2 - 20, HEIGHT - self.height + 20),
                (parallax_x + self.width // 2, HEIGHT - self.height),
                (parallax_x + self.width // 2 + 20, HEIGHT - self.height + 20)
            ]
            pygame.draw.polygon(screen, (255, 255, 255), snow_points)

class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 15
        self.collected = False
        self.image = create_coin_image(self.radius)
        self.animation_counter = 0
        
    def update(self):
        # Simple bobbing animation
        self.animation_counter += 0.1
        
    def draw(self, screen, camera_x):
        if not self.collected:
            # Apply bobbing effect
            bob_offset = math.sin(self.animation_counter) * 3
            
            # Draw coin with animation
            screen.blit(self.image, (self.x - camera_x - self.radius, 
                                    self.y - self.radius + bob_offset))

class Wheel:
    def __init__(self, x_offset, radius=15):
        self.x_offset = x_offset
        self.radius = radius
        self.x = 0
        self.y = 0
        self.prev_y = 0
        self.velocity_y = 0
        self.rotation = 0  # For wheel rotation animation
        
        # Suspension properties
        self.spring_strength = 0.3
        self.damping = 0.6
        self.suspension_height = 20
        self.suspension_compression = 0
        
        # Create wheel image
        self.image = create_wheel_image(radius)

class Car:
    def __init__(self):
        self.width = 80
        self.height = 40
        self.x = 200
        self.y = 300
        self.angle = 0
        self.speed = 0
        self.acceleration = 0
        self.max_speed = 10
        self.fuel = 100
        self.fuel_consumption = 0.1
        self.score = 0
        self.distance = 0
        self.max_distance = 0
        
        # Create wheels with suspension
        self.back_wheel = Wheel(20)
        self.front_wheel = Wheel(self.width - 20)
        
        # Car body offset from wheels
        self.body_offset_y = 10
        
        # Angular velocity for smoother rotation
        self.angular_velocity = 0
        self.angular_damping = 0.1
        
        # Create car body image
        self.image = create_car_image()
        
    def update(self, terrain, gas, brake, coins):
        # Apply gas and brake
        if gas and self.fuel > 0:
            self.acceleration = 0.2
            self.fuel -= self.fuel_consumption
        elif brake:
            self.acceleration = -0.2
        else:
            self.acceleration = 0
        
        # Update speed
        self.speed += self.acceleration
        self.speed *= 0.98  # Friction
        
        # Limit speed
        if self.speed > self.max_speed:
            self.speed = self.max_speed
        elif self.speed < -self.max_speed / 2:
            self.speed = -self.max_speed / 2
            
        # Move car forward based on speed and angle
        prev_x = self.x
        self.x += self.speed * math.cos(self.angle)
        
        # Update distance traveled
        self.distance += abs(self.x - prev_x)
        self.max_distance = max(self.max_distance, self.x)
        
        # Update wheel positions
        self.back_wheel.x = self.x + self.back_wheel.x_offset
        self.front_wheel.x = self.x + self.front_wheel.x_offset
        
        # Find terrain height at wheel positions
        back_terrain_height = terrain.get_height(self.back_wheel.x)
        front_terrain_height = terrain.get_height(self.front_wheel.x)
        
        # Apply suspension physics to back wheel
        self.apply_suspension(self.back_wheel, back_terrain_height)
        
        # Apply suspension physics to front wheel
        self.apply_suspension(self.front_wheel, front_terrain_height)
        
        # Calculate target angle based on wheel positions
        dx = self.front_wheel.x - self.back_wheel.x
        dy = self.front_wheel.y - self.back_wheel.y
        target_angle = math.atan2(dy, dx)
        
        # Smoothly rotate car towards target angle
        angle_diff = target_angle - self.angle
        # Normalize angle difference to be between -π and π
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi
            
        # Apply angular velocity with spring-like behavior
        self.angular_velocity += angle_diff * 0.1
        self.angular_velocity *= (1 - self.angular_damping)
        self.angle += self.angular_velocity
        
        # Update car body position based on wheels and suspension
        wheel_center_y = (self.back_wheel.y + self.front_wheel.y) / 2
        self.y = wheel_center_y - self.height / 2 - self.body_offset_y
        
        # Update wheel rotation based on speed
        if abs(self.speed) > 0.1:
            rotation_speed = self.speed / self.back_wheel.radius
            self.back_wheel.rotation += rotation_speed
            self.front_wheel.rotation += rotation_speed
        
        # Check for coin collection
        for coin in coins:
            if not coin.collected:
                # Calculate distance between car center and coin
                car_center_x = self.x + self.width / 2
                car_center_y = self.y + self.height / 2
                distance = math.sqrt((car_center_x - coin.x)**2 + (car_center_y - coin.y)**2)
                
                if distance < self.width / 2 + coin.radius:
                    coin.collected = True
                    self.score += 10
                    self.fuel = min(100, self.fuel + 10)  # Bonus fuel
        
        # Check if car is out of fuel
        if self.fuel <= 0:
            self.fuel = 0
    
    def apply_suspension(self, wheel, terrain_height):
        # Save previous position for velocity calculation
        wheel.prev_y = wheel.y
        
        # Calculate rest position (where wheel would be with no suspension compression)
        rest_position = terrain_height - wheel.radius
        
        # Calculate spring force (proportional to displacement from rest position)
        spring_displacement = rest_position - wheel.y
        spring_force = spring_displacement * wheel.spring_strength
        
        # Apply damping force (proportional to velocity)
        damping_force = wheel.velocity_y * wheel.damping
        
        # Calculate total force and resulting acceleration
        total_force = spring_force - damping_force
        
        # Update wheel velocity and position
        wheel.velocity_y += total_force
        wheel.y += wheel.velocity_y
        
        # Limit wheel position to not go below terrain
        if wheel.y > rest_position:
            wheel.y = rest_position
            wheel.velocity_y *= -0.3  # Bounce effect
        
        # Calculate suspension compression for visualization
        wheel.suspension_compression = min(wheel.suspension_height, 
                                          max(0, spring_displacement))
            
    def draw(self, screen, camera_x):
        # Draw suspension springs
        self.draw_suspension(screen, camera_x, self.back_wheel)
        self.draw_suspension(screen, camera_x, self.front_wheel)
        
        # Draw wheels with rotation
        for wheel in [self.back_wheel, self.front_wheel]:
            # Rotate wheel image
            rotated_wheel = pygame.transform.rotate(wheel.image, math.degrees(wheel.rotation) % 360)
            wheel_rect = rotated_wheel.get_rect(center=(wheel.x - camera_x, wheel.y))
            screen.blit(rotated_wheel, wheel_rect)
        
        # Draw car body
        # Create a rotated copy of the car image
        rotated_car = pygame.transform.rotate(self.image, -math.degrees(self.angle))
        car_rect = rotated_car.get_rect(center=(self.x + self.width/2 - camera_x, self.y + self.height/2))
        screen.blit(rotated_car, car_rect)
    
    def draw_suspension(self, screen, camera_x, wheel):
        # Calculate suspension attachment point on car body
        body_x = self.x + wheel.x_offset - camera_x
        body_y = self.y + self.height
        
        # Rotate attachment point around car center
        center_x = self.x + self.width / 2 - camera_x
        center_y = self.y + self.height / 2
        
        # Translate point to origin
        tx = body_x - center_x
        ty = body_y - center_y
        
        # Rotate point
        rx = tx * math.cos(self.angle) - ty * math.sin(self.angle)
        ry = tx * math.sin(self.angle) + ty * math.cos(self.angle)
        
        # Translate point back
        body_x = rx + center_x
        body_y = ry + center_y
        
        # Draw suspension spring (zigzag line)
        wheel_x = wheel.x - camera_x
        wheel_y = wheel.y
        
        # Calculate number of zigzags based on compression
        zigzags = 5
        zigzag_width = 4
        
        # Draw zigzag spring
        points = []
        for i in range(zigzags * 2 + 1):
            t = i / (zigzags * 2)
            x = body_x + (wheel_x - body_x) * t
            y = body_y + (wheel_y - body_y) * t
            
            # Add zigzag effect
            if i % 2 == 1:
                x += zigzag_width
            elif i > 0 and i < zigzags * 2:
                x -= zigzag_width
                
            points.append((x, y))
            
        # Draw the spring
        if len(points) > 1:
            pygame.draw.lines(screen, (100, 100, 100), False, points, 2)
        
    def draw_fuel_meter(self, screen):
        # Draw fuel meter background
        pygame.draw.rect(screen, FUEL_BG_COLOR, (20, 20, 150, 20))
        
        # Draw fuel level
        fuel_width = int(self.fuel * 1.5)
        pygame.draw.rect(screen, FUEL_COLOR, (20, 20, fuel_width, 20))
        
        # Draw fuel text
        font = pygame.font.SysFont(None, 24)
        fuel_text = font.render(f"FUEL: {int(self.fuel)}%", True, (255, 255, 255))
        screen.blit(fuel_text, (25, 22))
    
    def draw_score(self, screen):
        # Draw score and distance
        font = pygame.font.SysFont(None, 24)
        score_text = font.render(f"SCORE: {self.score}", True, (255, 255, 255))
        screen.blit(score_text, (20, 50))
        
        # Convert distance to meters (1 pixel = 0.1 meters)
        distance_m = int(self.distance * 0.1)
        distance_text = font.render(f"DISTANCE: {distance_m}m", True, (255, 255, 255))
        screen.blit(distance_text, (20, 80))

class Terrain:
    def __init__(self, width):
        self.width = width
        self.points = []
        self.checkpoints = []  # Store positions of mountain peaks
        self.generate_terrain()
        
    def generate_terrain(self):
        # Generate terrain points with smoother transitions
        x = 0
        y = HEIGHT // 2
        
        # Use Perlin noise-like approach for smoother terrain
        segment_length = 5  # Smaller segments for smoother curves
        num_control_points = self.width // 200 + 1
        control_points = []
        
        # Generate control points
        for i in range(num_control_points):
            if i == 0:
                control_points.append((0, HEIGHT // 2))
            else:
                # Create varied heights but ensure they're not too extreme
                new_y = HEIGHT // 2 + random.randint(-100, 100)
                # Keep terrain within reasonable bounds
                new_y = max(HEIGHT // 4, min(HEIGHT * 3 // 4, new_y))
                control_points.append((i * 200, new_y))
                
                # Add mountain peaks as checkpoints
                if i > 1 and control_points[i-1][1] < control_points[i-2][1] and control_points[i-1][1] < new_y:
                    self.checkpoints.append(control_points[i-1])
        
        # Generate smooth curves between control points using cubic interpolation
        for i in range(len(control_points) - 1):
            x1, y1 = control_points[i]
            x2, y2 = control_points[i + 1]
            
            # Add small hills and bumps between control points
            segment_count = (x2 - x1) // segment_length
            
            for j in range(segment_count):
                t = j / segment_count
                
                # Cubic interpolation for smoother curves
                # Add some small variations for bumps
                bump = math.sin(t * math.pi * 4) * 5 * random.random()
                
                # Cubic formula: a*t^3 + b*t^2 + c*t + d
                # Simplified version for our needs
                y = y1 * (1 - t) + y2 * t + bump
                
                self.points.append((x1 + j * segment_length, y))
        
    def get_height(self, x):
        # Find the height of the terrain at position x
        if x < 0:
            return self.points[0][1]
        
        for i in range(len(self.points) - 1):
            if self.points[i][0] <= x < self.points[i + 1][0]:
                # Linear interpolation between points
                x1, y1 = self.points[i]
                x2, y2 = self.points[i + 1]
                
                if x2 == x1:  # Avoid division by zero
                    return y1
                
                t = (x - x1) / (x2 - x1)
                return y1 + t * (y2 - y1)
        
        # If x is beyond the last point
        return self.points[-1][1]
    
    def draw(self, screen, camera_x):
        # Draw terrain
        terrain_points = []
        
        for x, y in self.points:
            if 0 <= x - camera_x <= WIDTH:
                terrain_points.append((x - camera_x, y))
        
        if terrain_points:
            # Add points at the bottom of the screen to fill the terrain
            terrain_points.append((terrain_points[-1][0], HEIGHT))
            terrain_points.append((terrain_points[0][0], HEIGHT))
            
            # Draw terrain with gradient
            pygame.draw.polygon(screen, GROUND_COLOR, terrain_points)
            
            # Draw grass on top of terrain
            for i in range(len(terrain_points) - 3):
                x, y = terrain_points[i]
                if i % 10 == 0:  # Draw grass every few points
                    grass_height = random.randint(3, 7)
                    pygame.draw.line(screen, (50, 150, 50), (x, y), (x, y - grass_height), 1)

def generate_coins(terrain, num_coins):
    coins = []
    
    # Place coins at interesting locations
    for checkpoint in terrain.checkpoints:
        x, y = checkpoint
        # Place coin above the peak
        coins.append(Coin(x, y - 50))
    
    # Add some random coins
    for _ in range(num_coins - len(terrain.checkpoints)):
        x = random.randint(500, terrain.width - 500)
        y = terrain.get_height(x) - random.randint(50, 100)
        coins.append(Coin(x, y))
    
    return coins

def main():
    # Create game objects
    terrain = Terrain(10000)  # 10000 pixels wide terrain
    car = Car()
    camera_x = 0
    
    # Create background elements
    clouds = [Cloud(random.randint(-200, WIDTH+200), random.randint(50, 150)) for _ in range(5)]
    mountains = [Mountain(i * 300, random.randint(100, 200)) for i in range(10)]
    
    # Create coins
    coins = generate_coins(terrain, 20)
    
    # Game loop
    running = True
    game_over = False
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Get keyboard input
        keys = pygame.key.get_pressed()
        gas = keys[pygame.K_RIGHT] or keys[pygame.K_UP]
        brake = keys[pygame.K_LEFT] or keys[pygame.K_DOWN]
        
        # Update game objects if not game over
        if not game_over:
            car.update(terrain, gas, brake, coins)
            
            # Update clouds
            for cloud in clouds:
                cloud.update()
                
            # Update coins
            for coin in coins:
                coin.update()
            
            # Check if game is over
            if car.fuel <= 0:
                game_over = True
        
        # Update camera to follow car
        camera_x = car.x - WIDTH // 3
        
        # Draw everything
        # Sky gradient
        for y in range(HEIGHT):
            # Create gradient from sky blue to darker blue
            color_value = max(80, 235 - y // 2)
            pygame.draw.line(screen, (135, 206, color_value), (0, y), (WIDTH, y))
        
        # Draw mountains in background
        for mountain in mountains:
            mountain.draw(screen, camera_x)
            
        # Draw clouds
        for cloud in clouds:
            cloud.draw(screen, camera_x)
        
        # Draw terrain
        terrain.draw(screen, camera_x)
        
        # Draw coins
        for coin in coins:
            coin.draw(screen, camera_x)
        
        # Draw car
        car.draw(screen, camera_x)
        
        # Draw UI elements
        car.draw_fuel_meter(screen)
        car.draw_score(screen)
        
        # Display game over if out of fuel
        if game_over:
            # Semi-transparent overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            screen.blit(overlay, (0, 0))
            
            font = pygame.font.SysFont(None, 72)
            game_over_text = font.render("GAME OVER", True, (255, 0, 0))
            screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 3))
            
            font = pygame.font.SysFont(None, 48)
            score_text = font.render(f"Final Score: {car.score}", True, (255, 255, 255))
            screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
            
            distance_m = int(car.distance * 0.1)
            distance_text = font.render(f"Distance: {distance_m}m", True, (255, 255, 255))
            screen.blit(distance_text, (WIDTH // 2 - distance_text.get_width() // 2, HEIGHT // 2 + 50))
            
            font = pygame.font.SysFont(None, 36)
            restart_text = font.render("Press R to restart", True, (255, 255, 255))
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 100))
            
            if keys[pygame.K_r]:
                # Reset game
                car = Car()
                coins = generate_coins(terrain, 20)
                game_over = False
        
        # Update display
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
