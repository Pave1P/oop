from typing import Protocol, List, Any


# === Протоколы ===

class PropertyChangedListenerProtocol(Protocol):
    def on_property_changed(self, obj: Any, property_name: str) -> None: ...


class PropertyChangingListenerProtocol(Protocol):
    def on_property_changing(self, obj: Any, property_name: str, old_value: Any, new_value: Any) -> bool: ...


class DataChangedProtocol(Protocol):
    def add_property_changed_listener(self, listener: PropertyChangedListenerProtocol) -> None: ...
    def remove_property_changed_listener(self, listener: PropertyChangedListenerProtocol) -> None: ...


class DataChangingProtocol(Protocol):
    def add_property_changing_listener(self, listener: PropertyChangingListenerProtocol) -> None: ...
    def remove_property_changing_listener(self, listener: PropertyChangingListenerProtocol) -> None: ...


# === Основной класс Person, реализующий оба протокола ===

class Person(DataChangedProtocol, DataChangingProtocol):
    def __init__(self, name: str, age: int):
        self._name = name
        self._age = age
        self._changed_listeners: List[PropertyChangedListenerProtocol] = []
        self._changing_listeners: List[PropertyChangingListenerProtocol] = []

    # Методы управления слушателями
    def add_property_changed_listener(self, listener: PropertyChangedListenerProtocol) -> None:
        self._changed_listeners.append(listener)

    def remove_property_changed_listener(self, listener: PropertyChangedListenerProtocol) -> None:
        self._changed_listeners.remove(listener)

    def add_property_changing_listener(self, listener: PropertyChangingListenerProtocol) -> None:
        self._changing_listeners.append(listener)

    def remove_property_changing_listener(self, listener: PropertyChangingListenerProtocol) -> None:
        self._changing_listeners.remove(listener)

    # Уведомление слушателей
    def _notify_changed(self, property_name: str):
        for listener in self._changed_listeners:
            listener.on_property_changed(self, property_name)

    def _notify_changing(self, property_name: str, old_value: Any, new_value: Any) -> bool:
        for listener in self._changing_listeners:
            if not listener.on_property_changing(self, property_name, old_value, new_value):
                return False
        return True

    # Свойство name
    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str):
        if new_name != self._name and self._notify_changing("name", self._name, new_name):
            self._name = new_name
            self._notify_changed("name")

    # Свойство age
    @property
    def age(self) -> int:
        return self._age

    @age.setter
    def age(self, new_age: int):
        if new_age != self._age and self._notify_changing("age", self._age, new_age):
            self._age = new_age
            self._notify_changed("age")

    def __repr__(self):
        return f"Person(name='{self._name}', age={self._age})"


# === Слушатели ===

class ConsoleChangedListener:
    def on_property_changed(self, obj: Any, property_name: str) -> None:
        print(f"[CHANGED] {property_name} changed on {obj}")


# === Валидаторы ===

class AgeValidator:
    def on_property_changing(self, obj: Any, property_name: str, old_value: Any, new_value: Any) -> bool:
        if property_name == "age" and (new_value < 0 or new_value > 150):
            print(f"[BLOCKED] Invalid age value: {new_value}")
            return False
        return True


class NameValidator:
    def on_property_changing(self, obj: Any, property_name: str, old_value: Any, new_value: Any) -> bool:
        if property_name == "name" and (not isinstance(new_value, str) or not new_value.strip()):
            print(f"[BLOCKED] Invalid name: '{new_value}'")
            return False
        return True


# === Демонстрация ===

if __name__ == "__main__":
    # Объект
    person = Person("Alice", 30)

    # Слушатели и валидаторы
    person.add_property_changed_listener(ConsoleChangedListener())
    person.add_property_changing_listener(AgeValidator())
    person.add_property_changing_listener(NameValidator())

    # Успешные изменения
    person.name = "Bob"
    person.age = 35

    # Попытки невалидных изменений
    person.age = -10
    person.name = ""
    person.age = 200

    # Повторная корректная установка
    person.name = "Charlie"
    person.age = 40
