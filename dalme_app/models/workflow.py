from django.contrib.auth.models import User
from django.db import models
from django_currentuser.middleware import get_current_user
import django.db.models.options as options

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('in_db',)


class Workflow(models.Model):
    ASSESSING = 1
    PROCESSING = 2
    DONE = 3
    INGESTION = 1
    TRANSCRIPTION = 2
    MARKUP = 3
    REVIEW = 4
    PARSING = 5
    WORKFLOW_STATUS = (
        (ASSESSING, 'assessing'),
        (PROCESSING, 'processing'),
        (DONE, 'processed')
    )
    PROCESSING_STAGES = (
        (INGESTION, 'ingestion'),
        (TRANSCRIPTION, 'transcription'),
        (MARKUP, 'markup'),
        (REVIEW, 'review'),
        (PARSING, 'parsing')
    )

    source = models.OneToOneField('Source', on_delete=models.CASCADE, related_name='workflow', primary_key=True)
    wf_status = models.IntegerField(choices=WORKFLOW_STATUS, default=2)
    stage = models.IntegerField(choices=PROCESSING_STAGES, default=1)
    last_modified = models.DateTimeField(null=True, blank=True)
    last_user = models.ForeignKey(User, null=True, on_delete=models.CASCADE, default=get_current_user)
    help_flag = models.BooleanField(default=False)
    ingestion_done = models.BooleanField(default=False)
    transcription_done = models.BooleanField(default=False)
    markup_done = models.BooleanField(default=False)
    parsing_done = models.BooleanField(default=False)
    review_done = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)

    @property
    def status(self):
        stage_dict = dict(self.PROCESSING_STAGES)
        if 1 <= self.wf_status <= 3:
            if self.wf_status != 2:
                status_text = self.get_wf_status_display()
                status_text_alt = ''
                css_class = 'tag-wf-' + status_text
            else:
                if getattr(self, self.get_stage_display() + '_done'):
                    status_text = 'awaiting ' + stage_dict[self.stage + 1]
                    status_text_alt = 'begin ' + stage_dict[self.stage + 1]
                    css_class = 'tag-wf-awaiting'
                else:
                    status_text = self.get_stage_display() + ' in progress'
                    status_text_alt = ''
                    css_class = 'tag-wf-in_progress'
        else:
            status_text = 'unknown'
            status_text_alt = ''
            css_class = 'tag-wf-unknown'
        return {'text': status_text, 'css_class': css_class, 'text_alt': status_text_alt, 'title_text': status_text.capitalize()}

    @property
    def stage_done(self):
        if self.wf_status == 2:
            stage_done = getattr(self, self.get_stage_display() + '_done')
        else:
            stage_done = True
        return stage_done


class Work_log(models.Model):
    id = models.AutoField(primary_key=True, unique=True, db_index=True)
    source = models.ForeignKey('Workflow', db_index=True, on_delete=models.CASCADE, related_name="work_log")
    event = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE, default=get_current_user)
