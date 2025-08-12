from tortoise.models import Model
from tortoise import fields


class User(Model):
    user_id = fields.IntField(max_length=50, null=True)
    admin = fields.BooleanField(default=False)
    username = fields.CharField(max_length=50, null=True)
    first_name = fields.CharField(max_length=50, null=True)
    banned = fields.BooleanField(default=False)

class UserLogs(Model):
    user_id = fields.IntField(max_length=50, null=True)
    record = fields.CharField(max_length=100, null=True)
    type =fields.CharField(max_length=50, null=True)
    ts = fields.DatetimeField(max_length=50, null=True)


class BrandDBModel(Model):
    processed = fields.BooleanField(default=False)
    id = fields.UUIDField(primary_key=True)
    brand = fields.CharField(max_length=50)

class ModelDBModel(Model):
    processed = fields.BooleanField(default=False)
    id = fields.UUIDField(primary_key=True)
    brand = fields.CharField(max_length=50)
    model = fields.CharField(max_length=50)

class GenDBModel(Model):
    processed = fields.BooleanField(default=False)
    level = fields.BooleanField(default=False)  # получен difficulty level

    id = fields.UUIDField(primary_key=True)
    glass_id = fields.CharField(max_length=50)

    brand = fields.CharField(max_length=50)
    model = fields.CharField(max_length=50)
    year_start = fields.IntField(max_length=50, null=True)
    year_end = fields.IntField(max_length=50, null=True)
    gen = fields.IntField(null=True)
    restyle = fields.IntField(null=True)

    height = fields.IntField(max_length=50, null=True)
    width = fields.IntField(max_length=50, null=True)

    difficulty = fields.IntField(max_length=50, null=True)