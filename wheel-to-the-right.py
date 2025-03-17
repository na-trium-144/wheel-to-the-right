import pyxel
from typing import List, Optional


class Phase:
    def update(self, app: "App") -> "Phase":
        raise NotImplementedError


class Enemy:
    x: int
    y: int
    exists: bool
    exploded_at: Optional[int]
    max_explode_radius: float

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.exists = True
        self.exploded_at = None

    def update(self, app: "App"):
        if (
            app.bullet_y is not None
            and abs(app.player_x - self.x) < 6
            and abs(app.bullet_y - self.y) < 6
        ):
            self.exploded_at = pyxel.frame_count
            app.bullet_y = None
            app.combo += 1
            app.score += app.combo
            self.max_explode_radius = 5 + 7 / app.combo

        if self.exploded_at is not None and pyxel.frame_count - self.exploded_at > 10:
            self.exists = False
            self.exploded_at = None

    @property
    def exploding(self) -> bool:
        return self.exploded_at is not None

    def exploding_radius(self) -> float:
        if self.exploded_at is None:
            return 0
        return (pyxel.frame_count - self.exploded_at) / 10 * self.max_explode_radius


class App:
    phase: "Phase"
    score: int
    combo: int
    stage: int
    enemies: List["Enemy"]
    player_x: float
    player_vx: float
    bullet_y: Optional[int]

    def __init__(self):
        self.bullet_y = None
        self.enemies = [Enemy(64, 32), Enemy(32, 16), Enemy(96, 16)]
        self.score = 0
        self.stage = 1
        self.combo = 0
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
        pyxel.text(2, 2, f"Score{self.score:5d}", 7)
        if self.combo:
            pyxel.text(128 - 4 * 9, 2, f"{self.combo:3d} Combo", 7)
        for e in self.enemies:
            if e.exploding:
                pyxel.circ(e.x, e.y, e.exploding_radius(), 8)
            elif e.exists:
                pyxel.rect(e.x - 3, e.y - 3, 6, 6, 14)
        if isinstance(self.phase, Fire) and self.bullet_y is not None:
            pyxel.rect(self.player_x - 2, self.bullet_y - 3, 4, 6, 10)
        pyxel.rect(self.player_x - 4, 120, 8, 8, 6)
        if isinstance(self.phase, Ready):
            pyxel.text(64 - 4 * 9 / 2, 80, f"Stage:{self.stage:3d}", 7)
            pyxel.text(64 - 4 * 22 / 2, 80 + 10, "Hold [Space] to start!", 7)


class Ready(Phase):
    def __init__(self, app: "App"):
        app.player_x = 4
        app.player_vx = 0

    def update(self, app: "App") -> "Phase":
        if pyxel.btnp(pyxel.KEY_SPACE):
            return Moving(app)
        return self


class Moving(Phase):
    def __init__(self, app: "App"):
        pass

    def update(self, app: "App") -> "Phase":
        if pyxel.btn(pyxel.KEY_SPACE):
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
    stopped_frame: int

    def __init__(self, app: "App"):
        app.bullet_y = 128
        app.combo = 0

    def update(self, app: "App") -> "Phase":
        if app.bullet_y is not None:
            app.bullet_y -= 3
            if app.bullet_y < -10:
                app.bullet_y = None
        for e in app.enemies:
            e.update(app)
        if app.bullet_y is not None or any(e.exploding for e in app.enemies):
            self.stopped_frame = pyxel.frame_count
            return self
        if pyxel.frame_count - self.stopped_frame < 20:
            return self
        return Ready(app)


if __name__ == "__main__":
    App().run()
