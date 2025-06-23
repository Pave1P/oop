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
        if interface_type in self._registrations:
            raise ValueError(f"Тип {interface_type.__name__} уже зарегистрирован")

        self._registrations[interface_type] = {
            'implementation': implementation,
            'life_style': life_style,
            'params': params or {}
        }

    def get_instance(self, interface_type: Type[T]) -> T:
        if interface_type not in self._registrations:
            raise ValueError(f"Тип {interface_type.__name__} не зарегистрирован")

        registration = self._registrations[interface_type]
        life_style = registration['life_style']
        implementation = registration['implementation']
        params = registration['params']

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
        if callable(implementation) and not isinstance(implementation, type):
            # Фабричный метод
            return implementation(**params)

        try:
            if isinstance(implementation, type):
                constructor_params = get_type_hints(implementation.__init__)
            else:
                constructor_params = get_type_hints(implementation)
        except (TypeError, AttributeError):
            constructor_params = {}

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

# Новые интерфейсы и классы для демонстрации
class IReportGenerator(ABC):
    @abstractmethod
    def generate(self, data: dict) -> str:
        pass

class ReportGenerator(IReportGenerator):
    def __init__(self, template: str, header: str):
        self.template = template
        self.header = header

    def generate(self, data: dict) -> str:
        return f"{self.header}\n{self.template.format(**data)}"

def report_generator_factory(template: str, header: str) -> IReportGenerator:
    """Фабричная функция для создания ReportGenerator"""
    return ReportGenerator(template, header)

class IDataProcessor(ABC):
    @abstractmethod
    def process(self, data: list) -> dict:
        pass

class DataProcessor(IDataProcessor):
    def __init__(self, logger, threshold: int):
        self.logger = logger
        self.threshold = threshold

    def process(self, data: list) -> dict:
        self.logger.log(f"Обработка данных с порогом {self.threshold}")
        return {"result": sum(x for x in data if x > self.threshold)}

# Дополненная демонстрация работы
def demonstrate_injector():
    print("=== Расширенная демонстрация ===")
    injector = Injector()
    
    # Регистрация с параметрами
    injector.register(
        IReportGenerator,
        ReportGenerator,
        LifeStyle.PER_REQUEST,
        {"template": "Данные: {value}", "header": "=== Отчет ==="}
    )
    
    # Регистрация через фабрику
    injector.register(
        IReportGenerator,
        report_generator_factory,
        LifeStyle.SINGLETON,
        {"template": "Фабричные данные: {value}", "header": "=== Фабричный отчет ==="}
    )
    
    # Регистрация сложной зависимости с параметрами
    injector.register(ILogger, ConsoleLogger, LifeStyle.SINGLETON)
    injector.register(
        IDataProcessor,
        DataProcessor,
        LifeStyle.PER_REQUEST,
        {"threshold": 5}
    )
    
    # Пример использования ReportGenerator с параметрами
    report_gen1 = injector.get_instance(IReportGenerator)
    print(report_gen1.generate({"value": "Тестовые данные"}))
    
    # Пример использования фабрики
    report_gen2 = injector.get_instance(IReportGenerator)
    print(report_gen2.generate({"value": "Данные из фабрики"}))
    
    # Пример использования DataProcessor с зависимостями и параметрами
    processor = injector.get_instance(IDataProcessor)
    result = processor.process([1, 6, 3, 8, 2])
    print(f"Результат обработки: {result}")

if __name__ == "__main__":
    demonstrate_injector()
