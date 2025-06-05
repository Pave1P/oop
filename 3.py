from typing import Protocol, List  # Импортируем Protocol для описания интерфейсов и List для аннотаций типов
import re                         # Модуль регулярных выражений
import socket                     # Модуль сокетов для сетевых подключений


#Протоколы

class LogFilterProtocol(Protocol):
    def match(self, text: str) -> bool:
        """Проверяет, подходит ли текст под фильтр"""
        ...


class LogHandlerProtocol(Protocol):
    def handle(self, text: str) -> None:
        """Обрабатывает (выводит/записывает) текст"""
        ...


#Фильтры логов

class SimpleLogFilter:
    def __init__(self, pattern: str):
        self.pattern = pattern  # Строка, которую ищем в тексте

    def match(self, text: str) -> bool:
        return self.pattern in text  # Возвращает True, если pattern содержится в тексте


class ReLogFilter:
    def __init__(self, pattern: str):
        self.pattern = re.compile(pattern)  # Компилируем регулярное выражение

    def match(self, text: str) -> bool:
        return bool(self.pattern.search(text))  # True, если шаблон найден в тексте


# Обработчики логов


class ConsoleHandler:
    def handle(self, text: str) -> None:
        print(text)  # Просто печатаем текст в консоль


class FileHandler:
    def __init__(self, filename: str):
        self.filename = filename  # Имя файла, куда писать

    def handle(self, text: str) -> None:
        try:
            with open(self.filename, 'a') as f:  # Открываем файл для добавления
                f.write(text + '\n')             # Пишем строку
        except IOError as e:
            print(f"[FileHandler ERROR] Ошибка при записи в файл: {e}")


class SocketHandler:
    def __init__(self, host: str, port: int):
        self.host = host  # Хост сервера
        self.port = port  # Порт сервера

    def handle(self, text: str) -> None:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))  # Подключаемся
                s.sendall((text + '\n').encode())  # Отправляем сообщение
        except Exception as e:
            print(f"[SocketHandler ERROR] Ошибка при отправке данных: {e}")


class SyslogHandler:
    def handle(self, text: str) -> None:
        print(f"\033[93m[SYSLOG] {text}\033[0m")  # Желтым цветом имитируем системный лог


# Логгер

class Logger:
    def __init__(self, filters: List[LogFilterProtocol] = None, handlers: List[LogHandlerProtocol] = None):
        self.filters = filters if filters else []     # Список фильтров
        self.handlers = handlers if handlers else []  # Список обработчиков

    def log(self, text: str) -> None:
        for f in self.filters:          # Проверка всех фильтров
            if not f.match(text):       # Если хотя бы один фильтр не проходит — лог не пишется
                return

        for h in self.handlers:         # Передаем текст всем обработчикам
            h.handle(text)


#Тестирование системы

# Создание фильтров
errorFilter = SimpleLogFilter("ERROR")
warningFilter = SimpleLogFilter("WARNING")
httpFilter = ReLogFilter(r"HTTP/\d\.\d")

# Создание обработчиков
consoleHandler = ConsoleHandler()
fileHandler = FileHandler("Log.log")
socketHandler = SocketHandler("localhost", 6969)  # Предполагается, что там работает сервер
syslogHandler = SyslogHandler()

# Создание логгеров с нужными фильтрами и обработчиками
errorLogger = Logger(filters=[errorFilter], handlers=[consoleHandler, fileHandler, syslogHandler])
warningLogger = Logger(filters=[warningFilter], handlers=[consoleHandler, fileHandler])
httpLogger = Logger(filters=[httpFilter], handlers=[consoleHandler, fileHandler, socketHandler])
defaultLogger = Logger(handlers=[consoleHandler])  # Без фильтров — логирует всё

# Тестовые сообщения
testLogs = [
    "INFO: Today is a good day",
    "ERROR: Application is not responding",
    "WARNING: Memory leakage",
    "INFO: HTTP/1.1 request received",
    "ERROR: HTTP/2.0 connection error"
]

# Демонстрация
print("ERROR logs:")
for logText in testLogs:
    errorLogger.log(logText)

print("---------------\nWARNING logs:")
for logText in testLogs:
    warningLogger.log(logText)

print("---------------\nHTTP logs:")
for logText in testLogs:
    httpLogger.log(logText)

print("---------------\nALL logs:")
for logText in testLogs:
    defaultLogger.log(logText)
