from moteur import Game
from npc import NPC
import pyglet

musique = pyglet.media.load("musique/MG.mp3", streaming=False)


player_musique = pyglet.media.Player()
player_musique.queue(musique)
player_musique.loop = True
player_musique.volume = 0.5
player_musique.play()

son_pas = pyglet.media.load("musique/bruit_de_pas.wav", streaming=False)
son_saut = pyglet.media.load("musique/saut.flac", streaming=False)

game = Game()
game._player_musique = player_musique
pyglet.app.run()

