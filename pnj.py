import pygame
import moteur.py
pygame.init()

screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# Joueur
player = pygame.Rect(100, 100, 40, 40)

# PNJ
pnj = pygame.Rect(400, 300, 40, 40)

font = pygame.font.SysFont(None, 30)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Déplacement du joueur
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:  player.x -= 3
    if keys[pygame.K_RIGHT]: player.x += 3
    if keys[pygame.K_UP]:    player.y -= 3
    if keys[pygame.K_DOWN]:  player.y += 3

    screen.fill((20, 20, 20))

    # Dessiner joueur et PNJ
    pygame.draw.rect(screen, (0, 150, 255), player)
    pygame.draw.rect(screen, (255, 200, 0), pnj)

    # Interaction : si le joueur est proche
    if player.colliderect(pnj.inflate(50, 50)):
        text = font.render("Bonjour !", True, (255, 255, 255))
        screen.blit(text, (pnj.x - 20, pnj.y - 30))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()