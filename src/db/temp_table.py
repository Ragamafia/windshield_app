from tortoise.models import Model
from tortoise import fields


class TempDifficulty(Model):
    glass_id = fields.CharField(max_length=50)
    difficulty = fields.IntField(max_length=50)
