"""
This file contains templates for models, used in dalme_app.models. These templates
are used to more easily associate common data points with those models, things like
timestamps and unique IDs.
"""
from django.db import models
from django.contrib.auth.models import User
from django_currentuser.middleware import get_current_user
import uuid


def get_current_username():
    return get_current_user().username


class dalmeBasic(models.Model):
    """ Model template with timestamps, but no pre-defined ID or Owner """
    creation_user = models.ForeignKey(User, on_delete=models.SET_NULL, default=get_current_user, related_name="%(app_label)s_%(class)s_creation", null=True)
    creation_timestamp = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    modification_user = models.ForeignKey(User, on_delete=models.SET_NULL, default=get_current_user, related_name="%(app_label)s_%(class)s_modification", null=True)
    modification_timestamp = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        abstract = True

    def class_name(self):
        return self.__class__.__name__

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self._state.adding is True:
            self.owner = get_current_user()
        super().save(force_insert, force_update, using, update_fields)


class dalmeUuid(models.Model):
    """ Model template with a unique ID assigned by `uuid.uuid4`, resulting in a long, random identifier. """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    creation_user = models.ForeignKey(User, on_delete=models.SET_NULL, default=get_current_user, related_name="%(app_label)s_%(class)s_creation", null=True)
    creation_timestamp = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    modification_user = models.ForeignKey(User, on_delete=models.SET_NULL, default=get_current_user, related_name="%(app_label)s_%(class)s_modification", null=True)
    modification_timestamp = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        abstract = True

    def class_name(self):
        return self.__class__.__name__


class dalmeIntid(models.Model):
    """ Model template with a unique ID assigned as a sequential integer """
    id = models.AutoField(primary_key=True, unique=True, db_index=True)
    creation_user = models.ForeignKey(User, on_delete=models.SET_NULL, default=get_current_user, related_name="%(app_label)s_%(class)s_creation", null=True)
    creation_timestamp = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    modification_user = models.ForeignKey(User, on_delete=models.SET_NULL, default=get_current_user, related_name="%(app_label)s_%(class)s_modification", null=True)
    modification_timestamp = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        abstract = True

    def class_name(self):
        return self.__class__.__name__


class dalmeUuidOwned(dalmeUuid):
    """ Same as dalmeUuid but with the addition of an owner field """
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="%(app_label)s_%(class)s_related", null=True)

    class Meta:
        abstract = True

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self._state.adding is True:
            self.owner = get_current_user()
        super().save(force_insert, force_update, using, update_fields)


class dalmeIntidOwned(dalmeIntid):
    """ Same as dalmeIntid but with the addition of an owner field """
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="%(app_label)s_%(class)s_related", null=True)

    class Meta:
        abstract = True

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self._state.adding is True:
            self.owner = get_current_user()
        super().save(force_insert, force_update, using, update_fields)
