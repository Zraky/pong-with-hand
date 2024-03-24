import pygame
import sys
import random
import mediapipe as mp
import numpy as np
import cv2

pygame.init()

SCREEN_WIDTH = 1300
SCREEN_HEIGHT = 975

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

clock = pygame.time.Clock()
score = [0, 0]
ball_use = 1
hand_number = []

cooldown = 5
class Player(pygame.sprite.Sprite):
    def __init__(self, x, size, speed, color):
        super().__init__()
        self.rect = pygame.Rect(x, (SCREEN_HEIGHT - size)/2, 60, size)
        self.speed = speed
        self.color = color

    def move(self, dt, hand_poss):
        if hand_poss[1] < self.rect.centery and self.rect.top > 0:
            self.rect.y -= self.speed * dt
        if hand_poss[1] > self.rect.centery and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.y += self.speed * dt

    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)

    def update(self, dt, hand_poss):
        self.move(dt, hand_poss)
        self.draw()

player_group = pygame.sprite.Group()

class Ball(pygame.sprite.Sprite):
    def __init__(self, size, color, speed, start_movement):
        super().__init__()
        self.rect = pygame.Rect(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, size, size)
        self.color = color
        self.speed = speed
        self.x_direction = start_movement
        self.y_direction = 1
        self.speed_x = speed
        self.speed_y = 0

    def move(self, dt):
        vector = pygame.Vector2(self.speed_x, self.speed_y)
        normalized_vector = vector.normalize()

        self.rect.x += self.speed_x * normalized_vector[0] * dt * self.x_direction
        self.rect.y += self.speed_y * normalized_vector[1] * dt * self.y_direction

    def bounce(self):
        if self.rect.top <= 0:
            self.rect.top = 0
            self.y_direction = 1

        elif self.rect.bottom >= SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
            self.y_direction = -1

        for player in player_group:
            collisions = pygame.sprite.collide_rect(self, player)
            if collisions:
                if self.x_direction == 1:
                    self.x_direction = -1
                    self.rect.right = player.rect.left

                else:
                    self.x_direction = 1
                    self.rect.left = player.rect.right

                difference = -(self.rect.centery - player.rect.centery) * 3
                self.speed_y -= difference
                if self.speed_y > self.speed_x * 2:
                    self.speed_y = self.speed_x * 2
                if difference > 0:
                    self.y_direction = -1
                elif difference < 0:
                    self.y_direction = 1
                self.speed_x += self.speed_x * 0.05

        if self.rect.right > SCREEN_WIDTH:
            score[0] += 1
            self.kill()
        elif self.rect.left < 0:
            score[1] += 1
            self.kill()
    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)

    def update(self, dt):
        self.move(dt)
        self.bounce()
        self.draw()

ball_group = pygame.sprite.Group()

for i in range(ball_use):
    x = random.randint(1, 2)
    if x == 1:
        service = 1
    else:
        service = -1
    ball = Ball(10, (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255)), random.randint(300, 700), service)

    ball_group.add(ball)
class Hand_draw():
    def __init__(self, screen_width, screen_height):
        self.cap = cv2.VideoCapture(0)
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands()
        self.mpDraw = mp.solutions.drawing_utils
        self.screen_width = screen_width
        self.screen_height = screen_height

    def update(self):
        global hand_number
        success, img = self.cap.read()
        img = cv2.resize(img, (self.screen_width, self.screen_height))  # Resize the image
        self.img = img
        results = self.hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        hand_number = []

        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                for i, lm in enumerate(handLms.landmark):
                    h, w, c = img.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    if i == 8:
                        hand_number.append([self.screen_width - cx, cy])
                self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)

    def draw(self, screen):
        img = np.rot90(cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB))
        pygame_img = pygame.surfarray.make_surface(img)
        screen.blit(pygame_img, (0, 0))

hand = Hand_draw(SCREEN_WIDTH, SCREEN_HEIGHT)


police = pygame.font.SysFont(str(None), 50)
police_fps = pygame.font.SysFont(str(None), 20)

while True:
    screen.fill("#000000")
    hand.update()
    hand.draw(screen)
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    if len(player_group) != len(hand_number):
        for player in player_group:
            player.kill()
        for i in range(len(hand_number)):
            if len(player_group) % 2 == 0:
                player_1 = Player(20, 200, 300, (255, 0, 0))
                player_group.add(player_1)
            else:
                player_2 = Player(SCREEN_WIDTH - (60 + 20 + 20 * len(player_group)), 200, 300, (0, 0, 255))
                player_group.add(player_2)

    hand_number_sort = sorted(hand_number)

    for i, player in enumerate(player_group):
        if i < len(hand_number):
            player.update(dt, hand_number_sort[i])
        else:
            player.update(dt, [player.rect.x, player.rect.y])

    for ball in ball_group:
        ball.update(dt)

    screen.blit((police.render(f"équipe bleu : {score[1]}", 1, (0, 0, 255))), (SCREEN_WIDTH/2 - 90, 0))
    screen.blit((police.render(f"équipe rouge : {score[0]}", 1, (255, 0, 0))), (SCREEN_WIDTH/2 - 100, 30))
    screen.blit((police_fps.render(f"FPS : {round(1/dt, 2)}", 1, (255, 255, 255))), (10, 10))

    if pygame.key.get_pressed()[pygame.K_r]:
        score = [0, 0]
        cooldown = 30
        for ball in ball_group:
            ball.kill()

    if len(ball_group) == 0:
        cooldown -= 1 * dt
        if cooldown > 0:
            screen.blit((police.render(f"prochain jeux dans {round(cooldown, 2)}", 1, (255, 255, 255))), (SCREEN_WIDTH / 2 - 130, SCREEN_HEIGHT / 2))
        else:
            x = random.randint(1, 2)
            if x == 1:
                service = 1
            else:
                service = -1
            ball = Ball(20, (255, 255, 255), random.randint(300, 500), service)
            ball_group.add(ball)
            cooldown = 5
    pygame.display.flip()

pygame.quit()
sys.exit()