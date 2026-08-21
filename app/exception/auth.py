class UserAlreadyExistsError(Exception):
    """Kullanıcı adı zaten kullanımda olduğunda fırlatılır."""
    pass


class InvalidCredentialsError(Exception):
    """Kullanıcı adı veya şifre hatalı olduğunda fırlatılır."""
    pass