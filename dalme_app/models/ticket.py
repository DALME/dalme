from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse
from dalme_app.models._templates import dalmeIntid
import django.db.models.options as options
from django.contrib.auth.models import User

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('in_db',)


class Ticket(dalmeIntid):
    OPEN = 0
    CLOSED = 1
    STATUS = (
        (OPEN, 'Open'),
        (CLOSED, 'Closed')
    )

    subject = models.CharField(max_length=140)
    description = models.TextField(blank=True, null=True)
    status = models.IntegerField(choices=STATUS, default=0)
    tags = GenericRelation('Tag')
    url = models.CharField(max_length=255, null=True, default=None)
    file = models.ForeignKey('Attachment', blank=True, null=True, on_delete=models.SET_NULL)
    comments = GenericRelation('Comment')
    assigned_to = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name="ticket_assigned_to")

    @property
    def creation_name(self):
        return self.creation_user.profile.full_name

    def __str__(self):
        return str(self.id) + ' - ' + self.subject + ' ('+self.get_status_display+')'

    def get_absolute_url(self):
        return reverse('ticket_detail', kwargs={'pk': self.pk})

    class Meta:
        ordering = ["status", "creation_timestamp"]
