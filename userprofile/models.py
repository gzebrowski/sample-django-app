# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager


class ProfileUserManager(UserManager):
    @classmethod
    def normalize_email(cls, email):
        return email.lower()

    def create_user(self, username, email=None, password=None, **extra_fields):
        if not email and username:
            email = username
        username = self.__class__.normalize_email(email)
        return super(ProfileUserManager, self).create_user(username, email=email, password=password, **extra_fields)

    def create_superuser(self, username, email, password, **extra_fields):
        x = 0
        while True:
            full_name = 'admin' + ('%s' % x if x else '')
            try:
                self.model.objects.get(full_name=full_name)
            except self.model.DoesNotExist:
                break
            else:
                x += 1
        extra_fields['full_name'] = full_name
        return super(ProfileUserManager, self).create_superuser(username, email, password, **extra_fields)


class ProfileUser(AbstractUser):
    full_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='full name')
    gender = models.CharField(max_length=1, null=True, blank=True, choices=(('1', 'Male'), ('2', 'Female')))
    password_hash = models.CharField(max_length=255, blank=True, null=True, editable=False)
    confirmed = models.BooleanField(default=False, blank=True)
    social_user = models.CharField(max_length=64, blank=True, null=True)
    social_user_data = models.TextField(blank=True, null=True)
    objects = ProfileUserManager()

    @property
    def user_name(self):
        return self.full_name

    def __unicode__(self):
        return u"%s" % self.full_name

    def get_short_name(self):
        return self.full_name
