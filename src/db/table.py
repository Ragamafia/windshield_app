import uuid

from tortoise.models import Model
from tortoise import fields


class BrandDBModel(Model):
    processed = fields.BooleanField(default=False)
    id = fields.CharField(primary_key=True, max_length=36)
    brand = fields.CharField(max_length=50)

class ModelDBModel(Model):
    processed = fields.BooleanField(default=False)
    id = fields.CharField(primary_key=True, max_length=36)
    brand = fields.CharField(max_length=50)
    model = fields.CharField(max_length=50)

class GenDBModel(Model):
    processed = fields.BooleanField(default=False)
    rated = fields.BooleanField(default=False)  # получен difficulty level

    id = fields.CharField(primary_key=True, max_length=36)

    brand = fields.CharField(max_length=50)
    model = fields.CharField(max_length=50)
    gen_start = fields.IntField(default=None)
    gen_end = fields.IntField(default=None)
    gen = fields.IntField(default=None)
    restyle = fields.BooleanField(default=False)

    glass_height = fields.IntField(default=None)
    glass_width = fields.IntField(default=None)
    difficulty = fields.IntField(default=None)