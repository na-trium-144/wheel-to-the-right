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

    def hit(self, app: "App"):
        if self.exists and not self.exploding:
            pyxel.play(1, 2)
            self.exploded_at = pyxel.frame_count
            app.bullet_y = None
            app.combo += 1
            app.combo_slidein = pyxel.frame_count
            app.score += app.combo
            self.max_explode_radius = 5 + 7 / app.combo

    def update(self, app: "App"):
        if (
            app.bullet_y is not None
            and abs(app.player_x - self.x) < 6
            and abs(app.bullet_y - self.y) < 6
        ):
            self.hit(app)
        for e in app.enemies:
            if e is self:
                continue
            if (
                e.exploding
                and (e.x - self.x) ** 2 + (e.y - self.y) ** 2
                < e.exploding_radius() ** 2
            ):
                self.hit(app)
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
    combo_slidein: Optional[int]
    stage: int
    shot_num: int
    max_shot_num: int
    enemies: List["Enemy"]
    player_x: float
    player_vx: float
    bullet_y: Optional[int]

    def __init__(self):
        self.bullet_y = None
        self.enemies = [Enemy(64, 32), Enemy(60, 30), Enemy(32, 16), Enemy(96, 16)]
        self.score = 0
        self.stage = 1
        self.combo = 0
        self.combo_slidein = None
        self.shot_num = 0
        self.max_shot_num = 4
        self.phase = Ready(self)
        pyxel.init(128, 128, title="Hello Pyxel")
        pyxel.load("wheel-to-the-right.pyxres")

    def run(self):
        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        self.phase = self.phase.update(self)

    def draw(self):
        pyxel.cls(0)
        pyxel.text(2, 2, f"Score{self.score:4d}", 7)
        pyxel.text(
            128 - 4 * 14 - 1,
            2,
            f"Stage{self.stage:3d}:{self.shot_num:2d}/{self.max_shot_num:2d}",
            7,
        )
        if (
            self.combo > 0
            and self.combo_slidein
            and pyxel.frame_count - self.combo_slidein < 30
        ):
            combo_x = max(0, 10 + self.combo_slidein - pyxel.frame_count)
            pyxel.text(2 + 4 * 6 + combo_x, 8, f"{self.combo:3d} Combo!", 9)
        for e in self.enemies:
            if e.exploding:
                pyxel.circ(e.x, e.y, e.exploding_radius(), 8)
            elif e.exists:
                pyxel.blt(e.x - 4, e.y - 4, 0, 16, 0, 8, 8, colkey=0)
        if isinstance(self.phase, Fire) and self.bullet_y is not None:
            pyxel.blt(self.player_x - 4, self.bullet_y - 4, 0, 24, 0, 8, 8, colkey=0)
        pyxel.blt(self.player_x - 4, 118, 0, 8, 0, 8, 8, colkey=0)
        if isinstance(self.phase, Ready):
            pyxel.text(64 - 4 * 8 / 2, 70, f"Stage{self.stage:3d}", 7)
            pyxel.text(
                64 - 4 * 14 / 2,
                80,
                f"Shots:{self.shot_num:3d} /{self.max_shot_num:3d}",
                7,
            )
            pyxel.text(64 - 4 * 30 / 2, 90, "Hold [Space] to move and shot!", 7)
        if isinstance(self.phase, Clear):
            pyxel.text(64 - 4 * 15 / 2, 70, f"Stage{self.stage:3d} Clear!", 7)
            pyxel.text(
                64 - 4 * 9 / 2, 80, f"Bonus:{self.max_shot_num - self.shot_num:3d}", 7
            )
            pyxel.text(64 - 4 * 25 / 2, 90, "Press [Space] to continue", 7)
        if isinstance(self.phase, GameOver):
            pyxel.text(64 - 4 * 10 / 2, 75, f"Game Over!", 7)
            pyxel.text(64 - 4 * 25 / 2, 85, "Press [Space] to continue", 7)


class Ready(Phase):
    def __init__(self, app: "App"):
        app.player_x = 6
        app.player_vx = 0
        app.shot_num += 1

    def update(self, app: "App") -> "Phase":
        if pyxel.btnp(pyxel.KEY_SPACE):
            return Moving(app)
        return self


class Moving(Phase):
    def __init__(self, app: "App"):
        pyxel.play(0, 0, loop=True)

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
        pyxel.play(0, 5)

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
        pyxel.play(0, 1)
        app.bullet_y = 120
        app.combo = 0
        app.combo_slidein = None

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
        if all(not e.exists for e in app.enemies):
            return Clear(app)
        if app.shot_num >= app.max_shot_num:
            return GameOver(app)
        return Ready(app)


class Clear(Phase):
    def __init__(self, app: "App"):
        app.score += app.max_shot_num - app.shot_num
        pyxel.play(2, 3)
        pyxel.play(3, 4)

    def update(self, app: "App") -> "Phase":
        if pyxel.btnp(pyxel.KEY_SPACE):
            app.stage += 1
            app.combo = 0
            app.shot_num = 0
            app.enemies = [Enemy(64, 32), Enemy(60, 30), Enemy(32, 16), Enemy(96, 16)]
            return Ready(app)
        return self


class GameOver(Phase):
    def __init__(self, app: "App"):
        pyxel.play(2, 6)
        pyxel.play(3, 7)

    def update(self, app: "App") -> "Phase":
        if pyxel.btnp(pyxel.KEY_SPACE):
            app.stage = 1
            app.score = 0
            app.combo = 0
            app.shot_num = 0
            app.enemies = [Enemy(64, 32), Enemy(60, 30), Enemy(32, 16), Enemy(96, 16)]
            return Ready(app)
        return self


if __name__ == "__main__":
    App().run()
