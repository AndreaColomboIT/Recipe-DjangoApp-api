"""
Database Models
"""

from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)
from django.conf import settings

class UserManager(BaseUserManager):

    def create_user(self,email, password = None, **extra_fields):
        if not email:
            raise ValueError('User must have email address')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email,password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
        
class User(AbstractBaseUser, PermissionsMixin):

    email = models.EmailField(max_length=255,unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    objects = UserManager()
    USERNAME_FIELD = 'email'


class Recipe(models.Model):
    """Recipe Object"""
    user = models.ForeignKey(
        # Same as giving core.User
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=5,decimal_places=2)
    link = models.CharField(max_length=255,blank=True)
    tags = models.ManyToManyField('Tag')
    
    def __str__(self) -> str:
        return self.title


class Tag(models.Model):
    """Tag model"""
    user = models.ForeignKey(
        # Same as giving core.User
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name