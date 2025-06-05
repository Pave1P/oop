from enum import Enum

class Color(Enum):
    default = "\033[0m"
    blue = "\033[94m"
    green = "\033[92m"
    red = "\033[91m"
class Printer:
    _font: dict[str, list[str]] = {}

    def __init__(self, color: Color, size: int, xShift: int, yShift: int, symbol = '*'):
        self.color = color
        self.size = size
        self.xShift = xShift
        self.yShift = yShift
        self.symbol = symbol

    @classmethod
    def updateFont(cls, font: int):
        filename = f'font{font}.txt'
        with open(filename, 'r') as f:
            cls._font.clear()
            while True:
                line = f.readline()[:-1]
                if line == '':
                    break
                if len(line)!=1:
                    raise Exception("Font file build wrong")
                letter = line
                cls._font[letter] = []
                for i in range(font):
                    cls._font[letter].append(f.readline()[:-1])

    def print(self, text: str):
        self.updateFont(self.size)
        for c in text:
            if c not in self._font:
                continue
            for i, j in enumerate(self._font[c]):
                show = j.replace('*', self.symbol)
                print(f"\033[{self.yShift + i + 1};{self.xShift}H" + show, end="")
            self.xShift+=self.size+1

    @classmethod
    def setPrint(cls, text: str, color:Color, size: int,xShift: int, yShift: int, symbol = '*'):
        cls.updateFont(size)
        for c in text:
            if c not in cls._font:
                continue
            for i, j in enumerate(cls._font[c]):
                show = j.replace('*', symbol)
                print(f"\033[{yShift + i + 1};{xShift}H" + color.value + show, end=Color.default.value)
            xShift+=size+1
        cls.xShift = xShift

    def __enter__(self):
        print(self.color.value, end="")
        return self

    def __exit__(self, *args) -> None:
        print(Color.default.value, end="")

#actual test
Printer.setPrint('SAMPLE', Color.blue, 7, 1, 1, '#')
with Printer(Color.red, 5, 50, 10, "$") as printer:
    printer.print('HELLO')
