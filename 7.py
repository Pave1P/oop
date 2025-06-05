from abc import ABC, abstractmethod
from typing import Type, Dict, Any, Callable, Optional, TypeVar, get_type_hints
import inspect

T = TypeVar('T')


class LifeStyle:
    PER_REQUEST = "PerRequest"
    SCOPED = "Scoped"
    SINGLETON = "Singleton"


class Injector:
    def __init__(self):
        self._registrations: Dict[Type, Dict] = {}
        self._scoped_instances: Dict[Type, Any] = {}
        self._singleton_instances: Dict[Type, Any] = {}
        self._in_scope = False

    def register(self,
                 interface_type: Type[T],
                 implementation: Type[T] | Callable[..., T],
                 life_style: str = LifeStyle.PER_REQUEST,
                 params: Optional[Dict[str, Any]] = None) -> None:
        """Регистрирует зависимость между интерфейсом и его реализацией"""
        if interface_type in self._registrations:
            raise ValueError(f"Тип {interface_type.__name__} уже зарегистрирован")

        self._registrations[interface_type] = {
            'implementation': implementation,
            'life_style': life_style,
            'params': params or {}
        }

    def get_instance(self, interface_type: Type[T]) -> T:
        """Возвращает экземпляр класса по интерфейсу"""
        if interface_type not in self._registrations:
            raise ValueError(f"Тип {interface_type.__name__} не зарегистрирован")

        registration = self._registrations[interface_type]
        life_style = registration['life_style']
        implementation = registration['implementation']
        params = registration['params']

        # Обработка разных жизненных циклов
        if life_style == LifeStyle.SINGLETON:
            if interface_type not in self._singleton_instances:
                self._singleton_instances[interface_type] = self._create_instance(implementation, params)
            return self._singleton_instances[interface_type]

        elif life_style == LifeStyle.SCOPED:
            if not self._in_scope:
                raise RuntimeError("Невозможно получить Scoped экземпляр вне области видимости Scope")
            if interface_type not in self._scoped_instances:
                self._scoped_instances[interface_type] = self._create_instance(implementation, params)
            return self._scoped_instances[interface_type]

        else:  # PerRequest
            return self._create_instance(implementation, params)

    def _create_instance(self, implementation: Type[T] | Callable[..., T], params: Dict[str, Any]) -> T:
        """Создает экземпляр класса, рекурсивно разрешая его зависимости"""
        if callable(implementation) and not isinstance(implementation, type):
            # Фабричный метод
            return implementation(**params)

        try:
            # Пытаемся получить аннотации конструктора
            if isinstance(implementation, type):
                constructor_params = get_type_hints(implementation.__init__)
            else:
                constructor_params = get_type_hints(implementation)
        except (TypeError, AttributeError):
            # Если аннотаций нет, используем пустой словарь
            constructor_params = {}

        # Собираем аргументы для конструктора
        args = {}
        for param_name, param_type in constructor_params.items():
            if param_name == 'return':
                continue
            if param_name in params:
                args[param_name] = params[param_name]
            elif param_type in self._registrations:
                args[param_name] = self.get_instance(param_type)

        return implementation(**args)

    def scope(self):
        """Контекстный менеджер для работы с Scoped зависимостями"""
        return self.ScopeContext(self)

    class ScopeContext:
        def __init__(self, injector: 'Injector'):
            self.injector = injector

        def __enter__(self):
            self.injector._in_scope = True
            return self.injector

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.injector._in_scope = False
            self.injector._scoped_instances.clear()


# Интерфейсы
class ILogger(ABC):
    @abstractmethod
    def log(self, message: str) -> None:
        pass


class IDatabase(ABC):
    @abstractmethod
    def query(self, sql: str) -> list:
        pass


class IEmailSender(ABC):
    @abstractmethod
    def send_email(self, to: str, subject: str, body: str) -> bool:
        pass


# Реализации ILogger
class ConsoleLogger(ILogger):
    def log(self, message: str) -> None:
        print(f"[LOG] {message}")


class FileLogger(ILogger):
    def __init__(self, filename: str = "app.log"):
        self.filename = filename

    def log(self, message: str) -> None:
        with open(self.filename, "a") as f:
            f.write(f"[LOG] {message}\n")


# Реализации IDatabase
class SqlDatabase(IDatabase):
    def __init__(self, connection_string: str, logger: ILogger):
        self.connection_string = connection_string
        self.logger = logger
        self.logger.log(f"Подключение к базе данных: {connection_string}")

    def query(self, sql: str) -> list:
        self.logger.log(f"Выполнение запроса: {sql}")
        # Имитация работы с БД
        return [{"id": 1, "name": "Test"}]


class MockDatabase(IDatabase):
    def query(self, sql: str) -> list:
        # Всегда возвращает тестовые данные
        return [{"id": 1, "name": "Mock"}]


# Реализации IEmailSender
class SmtpEmailSender(IEmailSender):
    def __init__(self, smtp_server: str, logger: ILogger):
        self.smtp_server = smtp_server
        self.logger = logger

    def send_email(self, to: str, subject: str, body: str) -> bool:
        self.logger.log(f"Отправка email на {to} через {self.smtp_server}")
        # Имитация отправки
        return True


class MockEmailSender(IEmailSender):
    def send_email(self, to: str, subject: str, body: str) -> bool:
        # Всегда возвращает успех в тестах
        return True


# Конфигурации
def configure_development(injector: Injector):
    """Конфигурация для разработки"""
    injector.register(ILogger, ConsoleLogger, LifeStyle.SINGLETON)
    injector.register(IDatabase, MockDatabase, LifeStyle.PER_REQUEST)
    injector.register(IEmailSender, MockEmailSender, LifeStyle.PER_REQUEST)


def configure_production(injector: Injector):
    """Конфигурация для продакшена"""
    injector.register(ILogger, FileLogger, LifeStyle.SINGLETON, {"filename": "production.log"})
    injector.register(
        IDatabase,
        SqlDatabase,
        LifeStyle.SCOPED,
        {"connection_string": "Server=prod;Database=app;User=admin;Password=secret"}
    )
    injector.register(
        IEmailSender,
        SmtpEmailSender,
        LifeStyle.PER_REQUEST,
        {"smtp_server": "smtp.prod.com"}
    )


# Демонстрация работы
def demonstrate_injector():
    print("=== Конфигурация для разработки ===")
    dev_injector = Injector()
    configure_development(dev_injector)

    # Получаем экземпляры
    logger1 = dev_injector.get_instance(ILogger)
    logger2 = dev_injector.get_instance(ILogger)
    print(f"Один и тот же логгер (Singleton)? {logger1 is logger2}")

    db1 = dev_injector.get_instance(IDatabase)
    db2 = dev_injector.get_instance(IDatabase)
    print(f"Одна и та же БД (PerRequest)? {db1 is db2}")

    # Использование зависимостей
    logger1.log("Тестовое сообщение")
    result = db1.query("SELECT * FROM users")
    print(f"Результат запроса: {result}")

    email_sender = dev_injector.get_instance(IEmailSender)
    email_sender.send_email("test@example.com", "Тест", "Это тестовое письмо")

    print("\n=== Конфигурация для продакшена ===")
    prod_injector = Injector()
    configure_production(prod_injector)

    # Singleton логгер
    prod_logger1 = prod_injector.get_instance(ILogger)
    prod_logger2 = prod_injector.get_instance(ILogger)
    print(f"Один и тот же логгер (Singleton)? {prod_logger1 is prod_logger2}")

    # Scoped база данных
    with prod_injector.scope():
        scoped_db1 = prod_injector.get_instance(IDatabase)
        scoped_db2 = prod_injector.get_instance(IDatabase)
        print(f"Одна и та же БД в пределах Scope? {scoped_db1 is scoped_db2}")

        result = scoped_db1.query("SELECT * FROM products")
        print(f"Результат запроса: {result}")

    # PerRequest email sender
    email_sender1 = prod_injector.get_instance(IEmailSender)
    email_sender2 = prod_injector.get_instance(IEmailSender)
    print(f"Один и тот же email sender (PerRequest)? {email_sender1 is email_sender2}")

    email_sender1.send_email("user@example.com", "Важное", "Важное сообщение")


if __name__ == "__main__":
    demonstrate_injector()