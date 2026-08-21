from app.model.user import User


class UserRepository:
    def get_by_id(self, user_id: int) -> User | None:
        return User.get_or_none(id=user_id)

    def get_by_login(self, login: str) -> User | None:
        return User.get_or_none(login=login)

    def create(self, login: str, password_hash: str) -> User:
        return User.create(login=login, password_hash=password_hash)