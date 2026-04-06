import pygame

pygame.init()
pygame.mixer.init()

# Charger les sons
son_bonus = pygame.mixer.Sound("sons/bonus.wav")
pygame.mixer.music.load("musique/fond.mp3")

# Lancer la musique
pygame.mixer.music.play(-1)



