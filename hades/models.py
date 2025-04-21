from django.contrib.auth.models import AbstractUser
from django.db import models
from django.forms import model_to_dict
from crum import get_current_request
from Gaia.settings import MEDIA_URL, STATIC_URL
from django.conf import settings
# Create your models here.

# Modelo Base
class BaseModel(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="created_%(class)s")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="updated_%(class)s")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def to_json(self):
        item = model_to_dict(self)
        item['created_by'] = self.created_by.to_json() if self.created_by else None
        item['create_at'] = self.created_at.strftime('%Y-%m-%d')
        item['update_by'] = self.updated_by.to_json() if self.created_by else None
        item['update_by'] = self.updated_by.strftime('%Y-%m-%d')
        return item


class User(AbstractUser, BaseModel):
    image = models.ImageField(upload_to='users/%Y/%m/%d', null=True, blank=True)
    token = models.UUIDField(primary_key=False, default=None, editable=False, null=True)

    def get_image(self):
        if self.image:
            return '{}{}'.format(MEDIA_URL, self.image)
        return'{}{}'.format(STATIC_URL, 'img/user.png')
    
    def to_json(self):
        item = model_to_dict(self, exclude=['password', 'user_permissions'])
        item['image'] = self.get_image()
        item['last_login'] = self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else None
        item['date_joined'] = self.date_joined.strftime('%Y-%m-%d %H:%M:%S')
        item['groups'] = [{'id':g.id, 'name':g.name} for g in self.groups.all()]
        return item
    
    def get_group_sessions(self):
        try:
            request = get_current_request()
            groups = self.groups.all()
            if groups.exists():
                if 'group' not in request.session:
                    group = groups.first()
                    request.session['group'] = [{'id': group.id, 'name': group.name}]
        except Exception as e:
            print(f"Error en get_group_sessions: {e}")
            pass
