from tortoise.models import Model
from tortoise import fields


class CarDBModel(Model):
    id = fields.IntField(pk=True)
    brand = fields.CharField(max_length=50)
    model = fields.CharField(max_length=50)
    #gen = fields.CharField(max_length=50, null=True)
    #glass_height = fields.IntField(null=True)
    #glass_width = fields.IntField(null=True)
    glass_difficulty_level = fields.IntField()

    #reserve_1 = fields.IntField(null=True)
    #reserve_2 = fields.IntField(null=True)
