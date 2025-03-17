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
            pyxel.play(3, 2)
            self.exploded_at = pyxel.frame_count
            app.bullet_y = None
            app.combo += 1
            app.combo_slidein = pyxel.frame_count
            app.score += app.combo
            self.max_explode_radius = 5 + 7 / (app.combo_before + 1)

    def update(self, app: "App"):
        if (
            app.bullet_y is not None
            and (app.player_x - self.x) ** 2 + (app.bullet_y - self.y) ** 2
            <= (3 + 3) ** 2
        ):
            self.hit(app)
        for e in app.enemies:
            if e is self:
                continue
            if (
                e.exploding
                and (e.x - self.x) ** 2 + (e.y - self.y) ** 2
                <= (3 + e.exploding_radius()) ** 2
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
    combo_before: int
    combo: int
    combo_slidein: Optional[int]
    stage: int
    shot_num: int
    max_shot_num: int
    enemies: List["Enemy"]
    player_x: float
    player_vx: float
    player_exists: bool
    bullet_y: Optional[int]
    bgm_playing: bool

    def __init__(self):
        pyxel.init(128, 128, title="Wheel to the Right")
        pyxel.load("wheel-to-the-right.pyxres")
        self.bullet_y = None
        self.score = 0
        self.bgm_playing = False
        init_stage(self, 1)
        self.phase = Title(self)

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
        if not isinstance(self.phase, Title):
            for e in self.enemies:
                if e.exploding:
                    pyxel.circ(e.x, e.y, e.exploding_radius(), 8)
                elif e.exists:
                    pyxel.blt(e.x - 4, e.y - 4, 0, 16, 0, 8, 8, colkey=0)
        if isinstance(self.phase, Fire) and self.bullet_y is not None:
            pyxel.blt(self.player_x - 4, self.bullet_y - 4, 0, 24, 0, 8, 8, colkey=0)
        if isinstance(self.phase, Fail):
            if self.phase.exploding_radius() > 0:
                pyxel.circ(128 - 4, 122, self.phase.exploding_radius(), 8)
            if pyxel.frame_count - self.combo_slidein < 30:
                combo_x = max(0, 10 + self.combo_slidein - pyxel.frame_count)
                pyxel.text(2 + 4 * 6 + combo_x, 8, " -5", 12)
        if self.player_exists:
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
            if self.stage < STAGES_MAX:
                pyxel.text(64 - 4 * 27 / 2, 90, "Press [Space] to next stage", 7)
            else:
                pyxel.text(64 - 4 * 22 / 2, 90, "Thank you for playing!", 7)
        if isinstance(self.phase, Title):
            pyxel.text(64 - 4 * 18 / 2, 30, "Wheel to the Right", 7)
            pyxel.text(64 - 4 * 24 / 2, 40, "<Shooting + UFO Catcher>", 7)
            pyxel.text(64 - 4 * 21 / 2, 60, "(c) 2025 na-trium-144", 7)
            pyxel.text(64 - 4 * 23 / 2, 90, "Press [Space] to start!", 7)
        if isinstance(self.phase, GameOver):
            pyxel.text(64 - 4 * 10 / 2, 80, "Game Over!", 7)


class Ready(Phase):
    def __init__(self, app: "App"):
        app.player_x = 6
        app.player_exists = True
        app.player_vx = 0
        app.shot_num += 1
        if not app.bgm_playing:
            pyxel.playm(0, loop=True)
            app.bgm_playing = True

    def update(self, app: "App") -> "Phase":
        if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            return Moving(app)
        return self


class Moving(Phase):
    def __init__(self, app: "App"):
        pyxel.play(3, 0, loop=True)

    def update(self, app: "App") -> "Phase":
        if pyxel.btn(pyxel.KEY_SPACE) or pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
            app.player_vx = min(app.player_vx + 0.1, 1.5)
            app.player_x += app.player_vx
            if app.player_x > 128 - 4:
                return Fail(app)
            return self
        return Stop(app)


class Stop(Phase):
    stopped_frame: int

    def __init__(self, app: "App"):
        self.stopped_frame = pyxel.frame_count
        pyxel.play(3, 5)

    def update(self, app: "App") -> "Phase":
        if app.player_vx > 0:
            app.player_x += app.player_vx
            app.player_vx -= 0.1
            self.stopped_frame = pyxel.frame_count
            if app.player_x > 128 - 4:
                return Fail(app)
            return self
        if pyxel.frame_count - self.stopped_frame < 20:
            return self
        return Fire(app)


class Fire(Phase):
    stopped_frame: int

    def __init__(self, app: "App"):
        pyxel.play(3, 1)
        app.bullet_y = 120
        app.combo = 0
        app.combo_slidein = None

    def update(self, app: "App") -> "Phase":
        if app.bullet_y is not None:
            app.bullet_y -= 3
            if app.bullet_y < -10:
                app.bullet_y = None
        app.combo_before = app.combo
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


class Fail(Phase):
    stopped_frame: int

    def __init__(self, app: "App"):
        pyxel.play(3, 2)
        app.score -= 5
        app.combo = 0
        app.combo_slidein = pyxel.frame_count
        app.player_exists = False
        self.stopped_frame = pyxel.frame_count

    def update(self, app: "App") -> "Phase":
        if pyxel.frame_count - self.stopped_frame < 40:
            return self
        if app.shot_num >= app.max_shot_num:
            return GameOver(app)
        return Ready(app)

    def exploding_radius(self) -> float:
        if pyxel.frame_count - self.stopped_frame > 10:
            return 0
        return (pyxel.frame_count - self.stopped_frame) / 10 * 12


class Title(Phase):
    def __init__(self, app: "App"):
        app.player_exists = False  # hide player
        app.player_vx = 0
        if not app.bgm_playing:
            pyxel.playm(0, loop=True)
            app.bgm_playing = True

    def update(self, app: "App") -> "Phase":
        if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            init_stage(app, 1)
            app.score = 0
            return Ready(app)
        return self


class Clear(Phase):
    def __init__(self, app: "App"):
        app.score += app.max_shot_num - app.shot_num
        pyxel.stop()
        app.bgm_playing = False
        pyxel.play(0, 3)
        pyxel.play(1, 4)

    def update(self, app: "App") -> "Phase":
        if (
            pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)
        ) and app.stage < STAGES_MAX:
            init_stage(app, app.stage + 1)
            return Ready(app)
        return self


class GameOver(Phase):
    def __init__(self, app: "App"):
        pyxel.stop()
        app.bgm_playing = False
        pyxel.play(0, 6)
        pyxel.play(1, 7)

    def update(self, app: "App") -> "Phase":
        if pyxel.btnp(pyxel.KEY_SPACE):
            return Title(app)
        return self


STAGES_MAX = 5


def init_stage(app: "App", stage: int) -> None:
    app.stage = stage
    app.combo = 0
    app.combo_before = 0
    app.combo_slidein = None
    app.shot_num = 0
    app.max_shot_num = {
        1: 5,
        2: 3,
        3: 7,
        4: 6,
        5: 10,
    }[stage]
    app.enemies = [
        Enemy(64 + x * 7, 56 - y * 7)
        for (x, y) in {
            1: [(-1, 0), (1, 0), (-5, 3), (5, 3)],
            2: [(0, 1), (-1.5, 1), (1.5, 1), (-3, 1), (3, 1)],
            3: [
                (0, 0),
                (-1.5, 1.5),
                (1.5, 1.5),
                (-3, 3),
                (0, 3),
                (3, 3),
                (-4.5, 4.5),
                (-1.5, 4.5),
                (1.5, 4.5),
                (4.5, 4.5),
            ],
            4: [(8, 0), (8, 2.5), (8, 5)],
            5: [
                (-3, -1),
                (-1.5, -1),
                (0, -1),
                (1.5, -1),
                (3, -1),
                (-4.5, 0),
                (4.5, 0),
                (-4.5, 1),
                (-1.5, 1),
                (0, 1),
                (1.5, 1),
                (4.5, 1),
                (-4.5, 2),
                (4.5, 2),
                (-4.5, 3),
                (4.5, 3),
                (-4.5, 4),
                (-1.5, 4),
                (1.5, 4),
                (4.5, 4),
                (-4.5, 5),
                (4.5, 5),
                (-3, 6),
                (-1.5, 6),
                (0, 6),
                (1.5, 6),
                (3, 6),
            ],
        }[stage]
    ]


if __name__ == "__main__":
    App().run()
