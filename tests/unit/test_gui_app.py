"""Headless smoke tests for the Tkinter GUI shell."""

from __future__ import annotations

from types import SimpleNamespace

from cop_thief.sdk import GameState


class FakeWidget:
    def __init__(self, *args, **kwargs) -> None:
        self.calls: list[tuple[str, tuple, dict]] = []

    def grid(self, *args, **kwargs) -> None:
        self.calls.append(("grid", args, kwargs))

    def pack(self, *args, **kwargs) -> None:
        self.calls.append(("pack", args, kwargs))

    def configure(self, **kwargs) -> None:
        self.calls.append(("configure", (), kwargs))


class FakeCanvas(FakeWidget):
    def delete(self, *args) -> None:
        self.calls.append(("delete", args, {}))

    def create_text(self, *args, **kwargs) -> None:
        self.calls.append(("text", args, kwargs))

    def create_rectangle(self, *args, **kwargs) -> None:
        self.calls.append(("rect", args, kwargs))

    def postscript(self, file: str, **kwargs) -> None:
        self.calls.append(("postscript", (file,), kwargs))


class FakeText(FakeWidget):
    def delete(self, *args) -> None:
        self.calls.append(("delete", args, {}))

    def insert(self, *args) -> None:
        self.calls.append(("insert", args, {}))


class FakeVar:
    def __init__(self, value: str = "") -> None:
        self.value = value

    def set(self, value: str) -> None:
        self.value = value

    def get(self) -> object:
        return self.value


class FakeRoot:
    def title(self, text: str) -> None:
        self.title_text = text

    def configure(self, **kwargs) -> None:
        self.config = kwargs

    def columnconfigure(self, *args, **kwargs) -> None:
        pass

    def rowconfigure(self, *args, **kwargs) -> None:
        pass

    def after(self, delay: int, callback) -> None:
        callback()


class FakeSDK:
    def __init__(self) -> None:
        self.frames = [
            GameState(grid_size=(2, 2), cop_pos=(0, 0), thief_pos=(1, 1)),
            GameState(grid_size=(2, 2), cop_pos=(0, 1), thief_pos=(1, 1), latest_message="closing"),
        ]

    def get_state(self) -> GameState:
        return self.frames[0]

    def run_sub_game(self, on_frame=None):
        if on_frame:
            for frame in self.frames:
                on_frame(frame)
        return SimpleNamespace(winner=SimpleNamespace(value="cop_win"))

    def run_full_game(self, on_frame=None):
        if on_frame:
            for frame in self.frames:
                on_frame(frame)
        return SimpleNamespace(sub_games_played=6)

    def get_replay_frames(self) -> list[GameState]:
        return self.frames


def test_gui_shell_runs_headless(monkeypatch, tmp_path) -> None:
    from cop_thief.gui import _shell, app

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(_shell.tk, "Canvas", FakeCanvas)
    monkeypatch.setattr(_shell.tk, "Text", FakeText)
    monkeypatch.setattr(app.tk, "StringVar", FakeVar)
    monkeypatch.setattr(app.tk, "IntVar", FakeVar)
    monkeypatch.setattr(_shell.ttk, "Scale", FakeWidget)
    monkeypatch.setattr(_shell.ttk, "Frame", FakeWidget)
    monkeypatch.setattr(_shell.ttk, "Label", FakeWidget)
    monkeypatch.setattr(_shell.ttk, "Button", FakeWidget)
    gui = app.CopThiefGui(FakeRoot(), FakeSDK())
    gui._run_worker(False)
    gui.step()
    gui.play()
    gui.capture()
    assert gui.status.value.startswith("Captured")
    assert (tmp_path / "assets").exists()
