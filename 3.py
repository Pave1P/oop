from typing import Protocol, List
import re
import socket


# Протоколы
class LogFilterProtocol(Protocol):
    def match(self, text: str) -> bool:
        """Проверяет, подходит ли текст под фильтр"""
        ...


class LogHandlerProtocol(Protocol):
    def handle(self, text: str) -> None:
        """Обрабатывает (выводит/записывает) текст"""
        ...


# Фильтры логов
class SimpleLogFilter:
    def __init__(self, pattern: str):
        self.pattern = pattern

    def match(self, text: str) -> bool:
        return self.pattern in text


class ReLogFilter:
    def __init__(self, pattern: str):
        try:
            self.pattern = re.compile(pattern)  # Может вызвать re.error при невалидном шаблоне
        except re.error as e:
            raise ValueError(f"Некорректное регулярное выражение: {e}") from e

    def match(self, text: str) -> bool:
        try:
            return bool(self.pattern.search(text))
        except (AttributeError, re.error) as e:
            print(f"[ReLogFilter ERROR] Ошибка при поиске по шаблону: {e}")
            return False


# Обработчики логов
class ConsoleHandler:
    def handle(self, text: str) -> None:
        print(text)


class FileHandler:
    def __init__(self, filename: str):
        self.filename = filename

    def handle(self, text: str) -> None:
        try:
            with open(self.filename, 'a') as f:
                f.write(text + '\n')
        except IOError as e:
            print(f"[FileHandler ERROR] Ошибка при записи в файл: {e}")


class SocketHandler:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def handle(self, text: str) -> None:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                s.sendall((text + '\n').encode())
        except Exception as e:
            print(f"[SocketHandler ERROR] Ошибка при отправке данных: {e}")


class SyslogHandler:
    def handle(self, text: str) -> None:
        print(f"\033[93m[SYSLOG] {text}\033[0m")


# Логгер
class Logger:
    def __init__(self, filters: List[LogFilterProtocol] = None, handlers: List[LogHandlerProtocol] = None):
        self.filters = filters if filters else []
        self.handlers = handlers if handlers else []

    def log(self, text: str) -> None:
        try:
            for f in self.filters:
                if not f.match(text):
                    return

            for h in self.handlers:
                h.handle(text)
        except Exception as e:
            print(f"[Logger ERROR] Ошибка при обработке лога: {e}")


# Тестирование системы
if __name__ == "__main__":
    # Создание фильтров
    errorFilter = SimpleLogFilter("ERROR")
    warningFilter = SimpleLogFilter("WARNING")
    try:
        httpFilter = ReLogFilter(r"HTTP/\d\.\d")
    except ValueError as e:
        print(f"Ошибка создания фильтра: {e}")
        httpFilter = SimpleLogFilter("HTTP")  # Фолбэк на простой фильтр

    # Создание обработчиков
    consoleHandler = ConsoleHandler()
    fileHandler = FileHandler("Log.log")
    socketHandler = SocketHandler("localhost", 6969)
    syslogHandler = SyslogHandler()

    # Создание логгеров
    errorLogger = Logger(filters=[errorFilter], handlers=[consoleHandler, fileHandler, syslogHandler])
    warningLogger = Logger(filters=[warningFilter], handlers=[consoleHandler, fileHandler])
    httpLogger = Logger(filters=[httpFilter], handlers=[consoleHandler, fileHandler, socketHandler])
    defaultLogger = Logger(handlers=[consoleHandler])

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

    print("\nWARNING logs:")
    for logText in testLogs:
        warningLogger.log(logText)

    print("\nHTTP logs:")
    for logText in testLogs:
        httpLogger.log(logText)

    print("\nALL logs:")
    for logText in testLogs:
        defaultLogger.log(logText)
