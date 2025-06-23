from dataclasses import dataclass, field, asdict
from typing import Protocol, TypeVar, Generic, Sequence, Optional
import json
import os

# Тип-переменная
T = TypeVar("T")

# ========== Класс User ==========
@dataclass(order=True)
class User:
    id: int
    name: str
    login: str
    password: str = field(repr=False)
    email: Optional[str] = None
    address: Optional[str] = None

# ========== Протоколы ==========
class DataRepositoryProtocol(Protocol, Generic[T]):
    def get_all(self) -> Sequence[T]: ...
    def get_by_id(self, id: int) -> Optional[T]: ...
    def add(self, item: T) -> None: ...
    def update(self, item: T) -> None: ...
    def delete(self, item: T) -> None: ...

class UserRepositoryProtocol(DataRepositoryProtocol[User], Protocol):
    def get_by_login(self, login: str) -> Optional[User]: ...

# ========== Универсальный репозиторий ==========
class DataRepository(Generic[T]):
    def __init__(self, path: str):
        self.path = path
        self._items: list[dict] = []
        try:
            self._load()
        except (json.JSONDecodeError, IOError) as e:
            print(f"Ошибка загрузки данных: {e}")
            self._items = []

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self._items = json.load(f)
        else:
            self._items = []

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._items, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Ошибка сохранения данных: {e}")

    def _serialize(self, obj: T) -> dict:
        return asdict(obj)

    def _deserialize(self, d: dict) -> T:
        raise NotImplementedError

    def get_all(self) -> Sequence[T]:
        return [self._deserialize(d) for d in self._items]

    def get_by_id(self, id: int) -> Optional[T]:
        for d in self._items:
            if d["id"] == id:
                return self._deserialize(d)
        return None

    def add(self, item: T) -> None:
        if self.get_by_id(item.id):
            raise ValueError(f"Элемент с id={item.id} уже существует.")
        self._items.append(self._serialize(item))
        self._save()

    def update(self, item: T) -> None:
        for i, d in enumerate(self._items):
            if d["id"] == item.id:
                self._items[i] = self._serialize(item)
                self._save()
                return
        raise ValueError(f"Элемент с id={item.id} не найден.")

    def delete(self, item: T) -> None:
        initial_len = len(self._items)
        self._items = [d for d in self._items if d["id"] != item.id]
        if len(self._items) < initial_len:
            self._save()

# ========== Репозиторий пользователей ==========
class UserRepository(DataRepository[User], UserRepositoryProtocol):
    def _deserialize(self, d: dict) -> User:
        return User(**d)

    def get_by_login(self, login: str) -> Optional[User]:
        for d in self._items:
            if d["login"] == login:
                return self._deserialize(d)
        return None

# ========== Протокол авторизации ==========
class AuthServiceProtocol(Protocol):
    def sign_in(self, login: str, password: str) -> bool: ...
    def sign_out(self) -> None: ...
    @property
    def is_authorized(self) -> bool: ...
    @property
    def current_user(self) -> Optional[User]: ...

# ========== Сервис авторизации ==========
class AuthService(AuthServiceProtocol):
    def __init__(self, repository: UserRepositoryProtocol):
        self.repository = repository
        self._current_user: Optional[User] = None

    def sign_in(self, login: str, password: str) -> bool:
        try:
            user = self.repository.get_by_login(login)
            if user and user.password == password:
                self._current_user = user
                return True
            return False
        except Exception as e:
            print(f"Ошибка при входе: {e}")
            return False

    def sign_out(self) -> None:
        self._current_user = None

    @property
    def is_authorized(self) -> bool:
        return self._current_user is not None

    @property
    def current_user(self) -> Optional[User]:
        return self._current_user

# ========== Пример использования ==========
def main():
    try:
        repo = UserRepository("users.json")
        auth = AuthService(repo)

        if auth.is_authorized:
            print(f"Добро пожаловать обратно, {auth.current_user.name}!")
        else:
            login = input("Введите логин: ")
            password = input("Введите пароль: ")
            
            if auth.sign_in(login, password):
                print(f"Успешный вход. Привет, {auth.current_user.name}!")
            else:
                print("Ошибка: Неверный логин или пароль.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    main()
