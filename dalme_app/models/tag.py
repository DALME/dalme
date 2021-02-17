from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from dalme_app.models._templates import dalmeUuid
import django.db.models.options as options

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('in_db',)


class Tag(dalmeUuid):
    WORKFLOW = 'WF'  # type of tags used to keep track of general DALME workflow
    CONTROL = 'C'  # general purpose control tags
    TICKET = 'T'  # tags for issue ticket management
    TAG_TYPES = (
        (WORKFLOW, 'Workflow'),
        (CONTROL, 'Control'),
        (TICKET, 'Ticket')
    )
    TICKET_TAGS = (
        ('bug', 'bug'),
        ('feature', 'feature'),
        ('documentation', 'documentation'),
        ('question', 'question'),
        ('content', 'content')
    )

    tag_type = models.CharField(max_length=2, choices=TAG_TYPES)
    tag = models.CharField(max_length=55, null=True, default=None)
    tag_group = models.CharField(max_length=255, null=True, default=None)
    content_object = GenericForeignKey('content_type', 'object_id')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.CharField(max_length=55, null=True, db_index=True)

    def __str__(self):
        return self.tag

    class Meta:
        unique_together = ("tag", "object_id")
