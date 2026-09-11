class UserAlreadyExistsError(Exception):
    """Kullanıcı adı zaten kullanımda olduğunda fırlatılır."""


class InvalidCredentialsError(Exception):
    """Kullanıcı adı veya şifre hatalı olduğunda fırlatılır."""
