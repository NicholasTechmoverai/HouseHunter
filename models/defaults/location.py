from tortoise import fields, Model

class GeoLocation(Model):
    id = fields.IntField(pk=True)
    lat = fields.FloatField(index=True)
    lon = fields.FloatField(index=True)

    class Meta:
        table = "geo_locations"
        indexes = (
            ("lat", "lon"), 
        )
