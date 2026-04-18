import math
import random as rd
import pygame

WIDTH, HEIGHT = 700, 700
FPS = 90
BG = (10, 12, 20)
WHITE = (235, 235, 235)


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def random_color():
    palette = [
        (220, 220, 220),
        (180, 200, 255),
        (255, 200, 150),
        (180, 255, 190),
        (255, 180, 220),
    ]
    return rd.choice(palette)


def resolve_bounce(a, b):
    dx = b._x - a._x
    dy = b._y - a._y
    dist = math.hypot(dx, dy)
    if dist == 0:
        dist = 0.01
        dx, dy = 0.01, 0.0
    overlap = a.radius + b.radius - dist
    if overlap <= 0: return
    nx, ny = dx / dist, dy / dist
    rvx, rvy = a._vx - b._vx, a._vy - b._vy
    rel_vel = rvx * nx + rvy * ny
    correction = overlap / 2 + 0.1
    a._x -= nx * correction
    a._y -= ny * correction
    b._x += nx * correction
    b._y += ny * correction
    if rel_vel > 0: return
    restitution, m1, m2 = 0.95, a.mass, b.mass
    j = -(1 + restitution) * rel_vel / (1 / m1 + 1 / m2)
    impulse_x, impulse_y = j * nx, j * ny
    a._vx += impulse_x / m1
    a._vy += impulse_y / m1
    b._vx -= impulse_x / m2
    b._vy -= impulse_y / m2


class Asteroid:
    def __init__(self, x, y, vx, vy, radius=18, color=(220, 220, 220)):
        self._x = float(x)
        self._y = float(y)
        self._vx = float(vx)
        self._vy = float(vy)
        self._radius = int(radius)
        self._color = color
        self._alive = True

    @property
    def alive(self):
        return self._alive

    @property
    def radius(self):
        return self._radius

    @property
    def mass(self):
        return self._radius * self._radius

    def update(self, dt, width, height, objects=None):
        self._x += self._vx * dt
        self._y += self._vy * dt
        if self._x - self._radius < 0:
            self._x = self._radius
            self._vx *= -1
        elif self._x + self._radius > width:
            self._x = width - self._radius
            self._vx *= -1
        if self._y - self._radius < 0:
            self._y = self._radius
            self._vy *= -1
        elif self._y + self._radius > height:
            self._y = height - self._radius
            self._vy *= -1

    def handle_collision(self, other):
        resolve_bounce(self, other)

    def draw(self, screen):
        pygame.draw.circle(screen, self._color, (int(self._x), int(self._y)), self._radius)


class Comet(Asteroid):
    def __init__(self, x, y, vx, vy, radius=14):
        super().__init__(x, y, vx, vy, radius=radius, color=(120, 190, 255))
        self._trail = []

    def update(self, dt, width, height, objects=None):
        self._trail.append((self._x, self._y))
        if len(self._trail) > 18: self._trail.pop(0)
        speed_boost = 1.00008
        self._vx *= speed_boost
        self._vy *= speed_boost
        super().update(dt, width, height, objects)

    def handle_collision(self, other):
        resolve_bounce(self, other)
        self._vx *= 1.05
        self._vy *= 1.05

    def draw(self, screen):
        trail_len = len(self._trail)
        for i, (tx, ty) in enumerate(self._trail):
            r = max(1, int(self._radius * (i + 1) / trail_len * 0.45))
            pygame.draw.circle(screen, (90, 150, 255), (int(tx), int(ty)), r)
        pygame.draw.circle(screen, self._color, (int(self._x), int(self._y)), self._radius)
        pygame.draw.circle(screen, (255, 255, 255), (int(self._x), int(self._y)), max(2, self._radius // 4), 1)


class BlackHole(Asteroid):
    def __init__(self, x, y, vx, vy, radius=24):
        super().__init__(x, y, vx, vy, radius=radius, color=(20, 20, 25))

    def update(self, dt, width, height, objects=None):
        if objects:
            for obj in objects:
                if obj is self or not obj.alive: continue
                dx, dy = self._x - obj._x, self._y - obj._y
                dist2 = dx * dx + dy * dy
                if dist2 <= 1: continue
                dist = math.sqrt(dist2)
                pull_range = 260
                if dist < pull_range:
                    gravity = 2_600_000 / dist2
                    obj._vx += (dx / dist) * gravity * dt
                    obj._vy += (dy / dist) * gravity * dt
                if dist < self._radius + obj.radius * 0.75:
                    obj._alive = False
                    self._radius = min(90, self._radius + max(1, obj.radius // 5))

        self._x += self._vx * dt * 0.15
        self._y += self._vy * dt * 0.15
        self._x = clamp(self._x, self._radius, width - self._radius)
        self._y = clamp(self._y, self._radius, height - self._radius)

    def handle_collision(self, other):
        if other.alive:
            other._alive = False
            self._radius = min(90, self._radius + max(1, other.radius // 5))

    def draw(self, screen):
        center = (int(self._x), int(self._y))
        pygame.draw.circle(screen, (0, 0, 0), center, self._radius)
        pygame.draw.circle(screen, (140, 70, 200), center, self._radius, 2)
        pygame.draw.circle(screen, (230, 230, 255), center, max(2, self._radius // 5))


def spawn_object(kind, x, y):
    angle = rd.random() * math.tau
    speed = rd.randint(70, 180)
    vx = math.cos(angle) * speed
    vy = math.sin(angle) * speed
    if kind == "asteroid":
        return Asteroid(x, y, vx, vy, radius=rd.randint(14, 24), color=random_color())
    if kind == "comet":
        return Comet(x, y, vx, vy, radius=rd.randint(10, 16))
    if kind == "blackhole":
        return BlackHole(x, y, rd.uniform(-10, 10), rd.uniform(-10, 10), radius=rd.randint(20, 28))


def random_spawn(kind=None):
    if kind is None: kind = rd.choice(["asteroid", "comet", "blackhole"])
    x, y = rd.randint(60, WIDTH - 60), rd.randint(60, HEIGHT - 60)
    return spawn_object(kind, x, y)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Game")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 20)
    big_font = pygame.font.SysFont("arial", 26)
    objects = []
    for _ in range(6):
        objects.append(random_spawn("asteroid"))
    for _ in range(2):
        objects.append(random_spawn("comet"))
    objects.append(random_spawn("blackhole"))
    selected = "asteroid"
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: selected = "asteroid"
                elif event.key == pygame.K_2: selected = "comet"
                elif event.key == pygame.K_3: selected = "blackhole"
                elif event.key == pygame.K_SPACE: objects.append(spawn_object(selected, WIDTH // 2, HEIGHT // 2))
                elif event.key == pygame.K_r: objects.append(random_spawn())
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                objects.append(spawn_object(selected, mx, my))
        for obj in objects:
            obj.update(dt, WIDTH, HEIGHT, objects)
        alive_objects = [o for o in objects if o.alive]
        for i in range(len(alive_objects)):
            a = alive_objects[i]
            for j in range(i + 1, len(alive_objects)):
                b = alive_objects[j]
                if not a.alive or not b.alive: continue
                dx, dy = b._x - a._x, b._y - a._y
                dist = math.hypot(dx, dy)
                if dist < a.radius + b.radius:
                    if isinstance(a, BlackHole): a.handle_collision(b)
                    elif isinstance(b, BlackHole): b.handle_collision(a)
                    else: a.handle_collision(b)
        objects = [o for o in objects if o.alive]
        screen.fill(BG)
        for obj in objects:
            obj.draw(screen)
        hud1 = f"Object now: {selected}"
        hud2 = f"Count of types: {len(objects)}"
        hud3 = "1/2/3 - type, LMB — create, SPACE — create in center, R — random"
        screen.blit(big_font.render("triple-A project", True, WHITE), (15, 12))
        screen.blit(font.render(hud1, True, WHITE), (15, 48))
        screen.blit(font.render(hud2, True, WHITE), (15, 72))
        screen.blit(font.render(hud3, True, WHITE), (15, HEIGHT - 32))
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()