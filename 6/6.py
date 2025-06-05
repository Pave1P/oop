import json
from abc import ABC, abstractmethod

# ---------------- Паттерн Command ----------------

class Command(ABC):
    @abstractmethod
    def execute(self): ...
    @abstractmethod
    def undo(self): ...

class PrintCommand(Command):
    def __init__(self, text_output: list, char: str):
        self.text_output = text_output
        self.char = char

    def execute(self):
        self.text_output.append(self.char)
        print(self.char, end="")  # на экран
        self._log(self.char)

    def undo(self):
        if self.text_output:
            self.text_output.pop()
            print("\b \b", end="")
            self._log("undo")

    def _log(self, text):
        with open("output.log", "a", encoding="utf-8") as f:
            f.write(text + "\n")

class VolumeUpCommand(Command):
    def __init__(self):
        self.percent = 20

    def execute(self):
        msg = f"volume increased +{self.percent}%"
        print(msg)
        self._log("ctrl++")

    def undo(self):
        msg = f"volume decreased -{self.percent}%"
        print(msg)
        self._log("undo")

    def _log(self, text):
        with open("output.log", "a", encoding="utf-8") as f:
            f.write(text + "\n")

class VolumeDownCommand(Command):
    def __init__(self):
        self.percent = 20

    def execute(self):
        msg = f"volume decreased -{self.percent}%"
        print(msg)
        self._log("ctrl+-")

    def undo(self):
        msg = f"volume increased +{self.percent}%"
        print(msg)
        self._log("undo")

    def _log(self, text):
        with open("output.log", "a", encoding="utf-8") as f:
            f.write(text + "\n")

class MediaPlayerCommand(Command):
    def __init__(self):
        self.launched = False

    def execute(self):
        self.launched = True
        msg = "media player launched"
        print(msg)
        self._log("ctrl+p")

    def undo(self):
        if self.launched:
            msg = "media player closed"
            print(msg)
            self._log("undo")

    def _log(self, text):
        with open("output.log", "a", encoding="utf-8") as f:
            f.write(text + "\n")

# ---------------- Паттерн Memento ----------------

class KeyboardMemento:
    def __init__(self, bindings: dict):
        self.bindings = bindings

    def to_json(self):
        return json.dumps(self.bindings)

    @staticmethod
    def from_json(data: str):
        bindings = json.loads(data)
        return KeyboardMemento(bindings)

class StateSaver:
    def __init__(self, filepath="bindings.json"):
        self.filepath = filepath

    def save(self, memento: KeyboardMemento):
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write(memento.to_json())

    def load(self):
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return KeyboardMemento.from_json(f.read())
        except FileNotFoundError:
            return KeyboardMemento({})

# ---------------- Основной класс Keyboard ----------------

class Keyboard:
    def __init__(self):
        self.bindings: dict[str, Command] = {}
        self.undo_stack: list[Command] = []
        self.redo_stack: list[Command] = []
        self.text_output: list[str] = []
        self.saver = StateSaver()
        self._load_state()

    def bind(self, key: str, command: Command):
        self.bindings[key] = command
        self._save_state()

    def press(self, key: str):
        cmd = self.bindings.get(key)
        if not cmd:
            print(f"No command bound to '{key}'")
            return

        # создаём новый экземпляр команды печати
        if isinstance(cmd, PrintCommand):
            cmd = PrintCommand(self.text_output, cmd.char)

        cmd.execute()
        self.undo_stack.append(cmd)
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            print("Nothing to undo")
            return
        cmd = self.undo_stack.pop()
        cmd.undo()
        self.redo_stack.append(cmd)

    def redo(self):
        if not self.redo_stack:
            print("Nothing to redo")
            return
        cmd = self.redo_stack.pop()
        cmd.execute()
        self.undo_stack.append(cmd)

    def _save_state(self):
        bindings_repr = {
            key: (
                f"PrintCommand:{cmd.char}" if isinstance(cmd, PrintCommand)
                else type(cmd).__name__
            )
            for key, cmd in self.bindings.items()
        }
        self.saver.save(KeyboardMemento(bindings_repr))

    def _load_state(self):
        memento = self.saver.load()
        for key, val in memento.bindings.items():
            if val.startswith("PrintCommand:"):
                char = val.split(":")[1]
                self.bindings[key] = PrintCommand(self.text_output, char)
            elif val == "VolumeUpCommand":
                self.bindings[key] = VolumeUpCommand()
            elif val == "VolumeDownCommand":
                self.bindings[key] = VolumeDownCommand()
            elif val == "MediaPlayerCommand":
                self.bindings[key] = MediaPlayerCommand()

# ---------------- Точка входа ----------------

def main():
    print("=== Виртуальная клавиатура ===")
    kb = Keyboard()

    # Привязка клавиш (можно менять)
    kb.bind("a", PrintCommand(kb.text_output, "a"))
    kb.bind("b", PrintCommand(kb.text_output, "b"))
    kb.bind("c", PrintCommand(kb.text_output, "c"))
    kb.bind("d", PrintCommand(kb.text_output, "d"))
    kb.bind("ctrl++", VolumeUpCommand())
    kb.bind("ctrl+-", VolumeDownCommand())
    kb.bind("ctrl+p", MediaPlayerCommand())

    while True:
        key = input("Введите клавишу (или 'undo', 'redo', 'exit'): ").strip()
        if key == "exit":
            break
        elif key == "undo":
            kb.undo()
        elif key == "redo":
            kb.redo()
        else:
            kb.press(key)

if __name__ == "__main__":
    main()
