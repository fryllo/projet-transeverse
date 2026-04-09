from moteur import Game
import pyglet



musique = pyglet.media.load("musique/PIANO.wav")
player_musique = pyglet.media.Player()
player_musique.queue(musique)
player_musique.loop = True
player_musique.volume = 0.5
player_musique.play()

son_pas = pyglet.media.load("musique/bruit_de_pas.wav", streaming=False)
son_saut = pyglet.media.load("musique/saut.flac", streaming=False)

game = Game()
pyglet.app.run()

