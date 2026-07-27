from peewee import Model, AutoField

from app.db.database import database_proxy


class BaseModel(Model):
    id = AutoField()

    class Meta:
        database = database_proxy