from datetime import datetime

from django.contrib import admin
from django.contrib.auth.models import User
from django.db import models


class Client(models.Model):

    name = models.CharField(max_length=255, unique=True)

    def __unicode__(self):
        return '%s' % self.name


class Account(User):

    client = models.ForeignKey(Client, related_name='accounts')

    _fake_static_fields = ('datetime_now',)

    def _compute_fake_static_field(self, field):
        if field == 'datetime_now':
            return datetime.now()

    def __unicode__(self):
        return '%s of client %s' % (
            ' '.join((self.first_name, self.last_name)),
            self.client.name
        )


class Contact(models.Model):

    client = models.ForeignKey(Client, related_name='contacts')

    name = models.CharField(max_length=100, blank=True, db_index=True)

    surname = models.CharField(max_length=100, blank=True, db_index=True)

    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )

    gender = models.CharField(blank=True, max_length=1, choices=GENDER_CHOICES)


class Group(models.Model):

    members = models.ManyToManyField(Contact)


admin.site.register(Client)
admin.site.register(Account)
admin.site.register(Contact)
admin.site.register(Group)
