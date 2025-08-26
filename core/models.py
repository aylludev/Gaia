from django.db import models
from Gaia.settings import MEDIA_URL, STATIC_URL

# Create your models here.
# models.py
from django.db import models

class Currency(models.Model):
    image = models.ImageField(upload_to='users/%Y/%m/%d', null=True, blank=True)
    code = models.CharField(max_length=3, unique=True)  # 'COP', 'USD', etc.
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=5)
    exchange_rate_to_base = models.FloatField(default=1.0)  # Ej: USD = 1.0, COP = 4000

    def get_image(self):
        if self.image:
            return '{}{}'.format(MEDIA_URL, self.image)
        return'{}{}'.format(STATIC_URL, 'img/user.png')
