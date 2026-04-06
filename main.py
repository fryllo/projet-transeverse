from moteur import Game
import pyglet

pygame.init()
pygame.mixer.init()

pygame.mixer.music.load("PIANO.wav")
pygame.mixer.music.play(-1)

game = Game()
pyglet.app.run()

