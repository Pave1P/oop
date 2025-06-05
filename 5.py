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
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self._items = json.load(f)
        else:
            self._items = []

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._items, f, ensure_ascii=False, indent=2)

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
    def sign_in(self, user: User) -> None: ...
    def sign_out(self, user: User) -> None: ...
    @property
    def is_authorized(self) -> bool: ...
    @property
    def current_user(self) -> Optional[User]: ...

# ========== Сервис авторизации с автологином ==========
class AuthService(AuthServiceProtocol):
    def __init__(self, repository: UserRepositoryProtocol, session_path: str = "session.json"):
        self.repository = repository
        self.session_path = session_path
        self._current_user: Optional[User] = None
        self._load_session()

    def _load_session(self):
        if os.path.exists(self.session_path):
            with open(self.session_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                login = data.get("login")
                if login:
                    user = self.repository.get_by_login(login)
                    if user:
                        self._current_user = user

    def _save_session(self):
        if self._current_user:
            with open(self.session_path, "w", encoding="utf-8") as f:
                json.dump({"login": self._current_user.login}, f)
        elif os.path.exists(self.session_path):
            os.remove(self.session_path)

    def sign_in(self, user: User) -> None:
        self._current_user = user
        self._save_session()

    def sign_out(self, user: User) -> None:
        if self._current_user and self._current_user.id == user.id:
            self._current_user = None
            self._save_session()

    @property
    def is_authorized(self) -> bool:
        return self._current_user is not None

    @property
    def current_user(self) -> Optional[User]:
        return self._current_user

# ========== Пример использования ==========
def main():
    repo = UserRepository("users.json")
    auth = AuthService(repo)

    if auth.is_authorized:
        print(f"Добро пожаловать обратно, {auth.current_user.name}!")
    else:
        login = input("Введите логин: ")
        password = input("Введите пароль: ")
        user = repo.get_by_login(login)
        if user and user.password == password:
            auth.sign_in(user)
            print(f"Успешный вход. Привет, {user.name}!")
        else:
            print("Ошибка: Неверный логин или пароль.")

if __name__ == "__main__":
    main()
