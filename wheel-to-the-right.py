import pyxel
from typing import List, Optional


class Phase:
    def update(self, app: "App") -> "Phase":
        raise NotImplementedError


class Enemy:
    x: int
    y: int
    exists: bool

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.exists = True

    def update(self, app: "App"):
        if (
            app.bullet_y is not None
            and abs(app.player_x - self.x) < 6
            and abs(app.bullet_y - self.y) < 6
        ):
            self.exists = False
            app.bullet_y = None


class App:
    phase: "Phase"
    enemies: List["Enemy"]
    player_x: float
    player_vx: float
    bullet_y: Optional[int]

    def __init__(self):
        self.bullet_y = None
        self.enemies = [Enemy(64, 32), Enemy(32, 16), Enemy(96, 16)]

        self.phase = Ready(self)
        pyxel.init(128, 128, title="Hello Pyxel")

    def run(self):
        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        self.phase = self.phase.update(self)

    def draw(self):
        pyxel.cls(0)
        for e in self.enemies:
            if e.exists:
                pyxel.rect(e.x - 3, e.y - 3, 6, 6, 14)
        if isinstance(self.phase, Fire) and self.bullet_y is not None:
            pyxel.rect(self.player_x - 2, self.bullet_y - 3, 4, 6, 10)
        pyxel.rect(self.player_x - 4, 120, 8, 8, 6)
        if isinstance(self.phase, Ready):
            pyxel.text(64 - (4 * 13 - 1) / 2, 64 - 5 / 2, "[F] to start!", 7)


class Ready(Phase):
    def __init__(self, app: "App"):
        app.player_x = 4
        app.player_vx = 0

    def update(self, app: "App") -> "Phase":
        if pyxel.btnp(pyxel.KEY_F):
            return Moving(app)
        return self


class Moving(Phase):
    def __init__(self, app: "App"):
        pass

    def update(self, app: "App") -> "Phase":
        if pyxel.btn(pyxel.KEY_F):
            app.player_vx = min(app.player_vx + 0.1, 1.5)
            app.player_x += app.player_vx
            return self
        return Stop(app)


class Stop(Phase):
    stopped_frame: int

    def __init__(self, app: "App"):
        self.stopped_frame = pyxel.frame_count

    def update(self, app: "App") -> "Phase":
        if app.player_vx > 0:
            app.player_x += app.player_vx
            app.player_vx -= 0.1
            self.stopped_frame = pyxel.frame_count
            return self
        if pyxel.frame_count - self.stopped_frame < 20:
            return self
        return Fire(app)


class Fire(Phase):

    def __init__(self, app: "App"):
        app.bullet_y = 128

    def update(self, app: "App") -> "Phase":
        if app.bullet_y is not None:
            app.bullet_y -= 3
            if app.bullet_y < -10:
                app.bullet_y = None
        for e in app.enemies:
            e.update(app)
        if app.bullet_y is None:
            return Ready(app)
        return self


if __name__ == "__main__":
    App().run()
