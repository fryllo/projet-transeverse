from moteur import Game
import pyglet

game = Game()
pyglet.app.run()

pygame.init()
pygame.mixer.init()

pygame.mixer.music.load("PIANO.wav")
pygame.mixer.music.play(-1)
