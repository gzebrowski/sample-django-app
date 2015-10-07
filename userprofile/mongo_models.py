# -*- coding: utf-8 -*-

import datetime
import json
import mongoengine as models


class User(models.Document):
    USERNAME_FIELD = 'name'
    created_at = models.DateTimeField(default=datetime.datetime.now, required=True)
    name = models.StringField(max_length=255, required=True)
    email = models.StringField(max_length=255, required=True, unique=True)
    gender = models.StringField(max_length=1, required=False)
    confirmed = models.BooleanField(default=False)
    db_id = models.IntField(required=False)
    user_is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    password_hash = models.StringField(max_length=255, required=True)

    meta = {
        'allow_inheritance': True,
        'indexes': ['-created_at'],
        'ordering': ['-created_at'],
    }

    def get_social_user(self):
        res = UserSocialAuth.objects.filter(user=self)
        if not res.count():
            return None
        return res[0]

    @property
    def social_user(self):
        s_user = self.get_social_user()
        return s_user.provider if s_user else ''

    @property
    def social_user_data(self):
        s_user = self.get_social_user()
        return json.dumps(s_user.extra_data) if s_user and s_user.extra_data else '{}'

    @property
    def username(self):
        return self.email


class SiteUser(User):
    pass


class UserSocialAuth(models.Document):
    user = models.ReferenceField(SiteUser)
    provider = models.StringField(max_length=32)
    uid = models.StringField(max_length=255, unique_with='provider')
    extra_data = models.DictField()
