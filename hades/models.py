from django.contrib.auth.models import AbstractUser
from django.db import models
from django.forms import model_to_dict
from crum import get_current_request
from Gaia.settings import MEDIA_URL, STATIC_URL
# Create your models here.

class User(AbstractUser):
    image = models.ImageField(upload_to='users/%Y/%m/%d', null=True, blank=True)
    token = models.UUIDField(primary_key=False, default=None, editable=False, null=True)

    def get_image(self):
        if self.image:
            return '{}{}'.format(MEDIA_URL, self.image)
        return'{}{}'.format(STATIC_URL, 'img/user.png')
    
    def to_json(self):
        item = model_to_dict(self)
        item['image'] = self.get_image()
        item['is_superuser'] = self.is_superuser
        item['is_staff'] = self.is_staff
        item['is_active'] = self.is_active
        item['last_login'] = self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else None
        item['date_joined'] = self.date_joined.strftime('%Y-%m-%d %H:%M:%S')
        item['groups'] = [{'id': group.id, 'name': group.name} for group in self.groups.all()]
        return item
    
    def get_group_sessions(self):
        try:
            request = get_current_request()
            groups = self.groups.all()
            if groups.exists:
                if groups not in request.session:
                    request.session['group'] = [{'id': groups[0].id, 'name': groups[0].name}]
        except:
            pass 