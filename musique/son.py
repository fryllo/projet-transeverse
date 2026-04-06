import pygame

pygame.mixer.init()

# Charger les sons
son_pas = pygame.mixer.Sound("musique/bruit_de_pas.wav")
son_saut = pygame.mixer.Sound("musique/saut.flac")

# Tu peux aussi régler les volumes ici
son_pas.set_volume(0.5)
son_saut.set_volume(0.7)