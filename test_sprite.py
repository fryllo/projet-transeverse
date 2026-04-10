import pyglet

window = pyglet.window.Window(500, 300, "Test Sprite")
dragon1 = pyglet.image.load("assets/dragon_frame1.png")
dragon2 = pyglet.image.load("assets/dragon_frame2.png")
dragon3 = pyglet.image.load("assets/dragon_frame3.png")

sprite = pyglet.sprite.Sprite(dragon1, x=200, y=100)
frames = [dragon1, dragon2, dragon3]
index = 0
timer = 0

@window.event
def on_draw():
    window.clear()
    sprite.draw()

def update(dt):
    global index, timer
    timer += dt
    if timer >= 0.25:
        timer = 0
        index = (index + 1) % len(frames)
        sprite.image = frames[index]

pyglet.clock.schedule_interval(update, 1 / 60)
pyglet.app.run()
