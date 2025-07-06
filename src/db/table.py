from tortoise.models import Model
from tortoise import fields


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
    rated = fields.BooleanField(default=False)  # получен difficulty level

    id = fields.UUIDField(primary_key=True)
    glass_id = fields.CharField(max_length=50)

    brand = fields.CharField(max_length=50)
    model = fields.CharField(max_length=50)
    year_start = fields.IntField(max_length=50, null=True)
    year_end = fields.IntField(max_length=50, null=True)
    gen = fields.IntField(null=True)
    restyle = fields.BooleanField(null=True)

    glass_height = fields.CharField(max_length=50, null=True)
    glass_width = fields.CharField(max_length=50, null=True)
    difficulty = fields.CharField(max_length=50, null=True)