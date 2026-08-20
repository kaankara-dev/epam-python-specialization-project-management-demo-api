from app.core.security import create_access_token, hash_password
from app.db.database import initialize_database
from app.model.user import User


def seed_user() -> None:
    # Gerçek PostgreSQL veritabanına bağlanıyoruz
    initialize_database()

    # Gerçek kullanıcıyı oluşturuyoruz (varsa getirir)
    user, created = User.get_or_create(
        login="kaan_dev",
        defaults={"password_hash": hash_password("SuperSecret123!")},
    )

    if created:
        print(f"Kullanici olusturuldu: {user.login} (ID: {user.id})")
    else:
        print(f"Kullanici zaten vardi: {user.login} (ID: {user.id})")

    # Bu kullanıcı için gerçek, geçerli bir JWT Token üretiyoruz
    token = create_access_token(subject=user.login)
    print("\n--- SENIN JWT ACCESS TOKEN'IN (Kopyala) ---")
    print(f"Bearer {token}")
    print("-------------------------------------------\n")


if __name__ == "__main__":
    seed_user()