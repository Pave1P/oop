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
        print(self.char, end="")
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
    def __init__(self, state: dict):
        self.state = state  # Просто хранит состояние, ничего не зная о командах

    def to_json(self):
        return json.dumps(self.state)

    @staticmethod
    def from_json(data: str):
        state = json.loads(data)
        return KeyboardMemento(state)

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
        self.bindings = {}
        self.undo_stack = []
        self.redo_stack = []
        self.text_output = []
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
        state = {
            'bindings': {
                key: {
                    'type': type(cmd).__name__,
                    'char': cmd.char if isinstance(cmd, PrintCommand) else None
                }
                for key, cmd in self.bindings.items()
            },
            'text_output': self.text_output
        }
        self.saver.save(KeyboardMemento(state))

    def _load_state(self):
        memento = self.saver.load()
        if not memento.state:
            return

        self.text_output = memento.state.get('text_output', [])
        
        for key, cmd_data in memento.state.get('bindings', {}).items():
            cmd_type = cmd_data['type']
            if cmd_type == "PrintCommand":
                self.bindings[key] = PrintCommand(self.text_output, cmd_data['char'])
            elif cmd_type == "VolumeUpCommand":
                self.bindings[key] = VolumeUpCommand()
            elif cmd_type == "VolumeDownCommand":
                self.bindings[key] = VolumeDownCommand()
            elif cmd_type == "MediaPlayerCommand":
                self.bindings[key] = MediaPlayerCommand()

# ---------------- Точка входа ----------------
def main():
    print("=== Виртуальная клавиатура ===")
    kb = Keyboard()

    kb.bind("a", PrintCommand(kb.text_output, "a"))
    kb.bind("b", PrintCommand(kb.text_output, "b"))
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
