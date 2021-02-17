import os
from django.db import models
from dalme_app.models._templates import dalmeUuidOwned
import django.db.models.options as options
import mimetypes

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('in_db',)


class Attachment(dalmeUuidOwned):
    file = models.FileField(upload_to='attachments/%Y/%m/')
    type = models.CharField(max_length=255, null=True)

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    def extension(self):
        name, extension = os.path.splitext(self.file.name)
        return extension

    @property
    def source(self):
        return f'https://dalme-app-media.s3.amazonaws.com/media/{str(self.file)}'

    def preview(self):
        icon_type_dict = {
            'application/msword': 'fa-file-word',
            'text/csv': 'fa-file-csv',
            'application/pdf': 'fa-file-pdf',
            'application/zip': 'fa-file-archive',
            'application/vnd.ms-excel': 'fa-file-excel'
        }
        icon_class_dict = {
            'audio': 'fa-file-audio',
            'video': 'fa-file-video',
            'image': 'fa-file-image',
            'text': 'fa-file-alt',
        }
        if icon_type_dict.get(self.type) is not None:
            icon = icon_type_dict.get(self.type)
        elif icon_class_dict.get(self.type.split('/')[0]) is not None:
            icon = icon_class_dict.get(self.type.split('/')[0])
        else:
            icon = 'fa-file'
        if self.type.split('/')[0] == 'image':
            preview = '<div class="attachment-file"><img src="{}" class="attachment-file-image" alt="image">\
                                   <div class="attachment-file-label">{}</div></div>'.format('https://dalme-app-media.s3.amazonaws.com/media/'+str(self.file), self.filename)
        else:
            preview = '<div class="attachment-file"><div class="attachment-file-body"><i class="far {} fa-8x"></i>\
                                   </div><div class="attachment-file-label"><a href="/download/{}">{}</a></div>\
                                   </div>'.format(icon, self.file, self.filename)
        return preview

    def __str__(self):
        return self.file.name

    def save(self, *args, **kwargs):
        type, encoding = mimetypes.guess_type(str(self.file).split('/').pop(-1))
        self.type = type
        super(Attachment, self).save(*args, **kwargs)
