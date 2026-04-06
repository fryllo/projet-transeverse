from moteur import Game
import pyglet
import pygame


pygame.mixer.init()
pygame.mixer.music.load("musique/PIANO.wav")
pygame.mixer.music.play(-1)
pygame.mixer.music.set_volume(0.5)
son_pas = pygame.mixer.Sound("musique/bruit_de_pas.wav")
son_saut = pygame.mixer.Sound("musique/saut.flac")

game = Game()
pyglet.app.run()

