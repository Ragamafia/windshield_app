from tortoise import Model, fields


class Car(Model):
    id = fields.IntField(pk=True)
    brand = fields.CharField(max_length=50)
    model = fields.CharField(max_length=50)
    gen = fields.CharField(max_length=50)
    glass_height = fields.IntField()
    glass_width = fields.IntField()
    film_complexity = fields.IntField()
