from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

class Client(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
    )

    def __unicode__(self):
        return '%s' % self.name

class Account(User):
    client = models.ForeignKey(
        Client,
        related_name='accounts',
    )

    fake_fields = (
        'datetime_now',
    )
    def _compute_fake_fields(self, field):
        if field=='datetime_now':
            return datetime.now()

    def __unicode__(self):
        return '%s of client %s' % ( 
            ' '.join((self.first_name, self.last_name)),
            self.client.name
        )

class Contact(models.Model):
    client = models.ForeignKey(
        Client,
        related_name='contacts',
    )

    name = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
    )

    surname = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
    )

    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    gender = models.CharField(
        blank=True,
        max_length=1,
        choices=GENDER_CHOICES,
    )    

from django.contrib import admin, databrowse
admin.site.register(Client)
admin.site.register(Account)
admin.site.register(Contact)


