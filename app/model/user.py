from peewee import CharField, Check

from app.db.base import BaseModel


class User(BaseModel):
    login = CharField(100, unique=True)
    password_hash = CharField(
        max_length=255,
        constraints=[
            Check("length(trim(password_hash)) > 0"),
        ],
    )

    class Meta:
        table_name = "users"