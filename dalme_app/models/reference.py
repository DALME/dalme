from django.db import models
from dalme_app.models._templates import dalmeIntid, dalmeUuid
import django.db.models.options as options

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('in_db',)


class AttributeReference(dalmeUuid):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=55)
    description = models.TextField()
    data_type = models.CharField(max_length=15)
    source = models.CharField(max_length=255)
    term_type = models.CharField(max_length=55, blank=True, default=None)


class CountryReference(dalmeIntid):
    name = models.CharField(max_length=255, unique=True)
    alpha_3_code = models.CharField(max_length=3)
    alpha_2_code = models.CharField(max_length=2)
    num_code = models.IntegerField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_url(self):
        return '/countries/' + str(self.id)


class LanguageReference(dalmeIntid):
    # LANGUAGE_TYPES = (
    #     ('language', 'language'),
    #     ('dialect', 'dialect')
    # )
    LANGUAGE = 1
    DIALECT = 2
    LANG_TYPES = (
        (LANGUAGE, 'Language'),
        (DIALECT, 'Dialect'),
    )

    glottocode = models.CharField(max_length=25, unique=True)
    iso6393 = models.CharField(max_length=25, unique=True, blank=True, null=True, default=None)
    name = models.CharField(max_length=255)
    # lang_type = models.IntegerField(choices=LANG_TYPES)
    type = models.IntegerField(choices=LANG_TYPES)
    # type = models.CharField(max_length=15, choices=LANGUAGE_TYPES)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_url(self):
        return '/languages/' + str(self.id)


class LocaleReference(dalmeIntid):
    name = models.CharField(max_length=255)
    administrative_region = models.CharField(max_length=255)
    country = models.ForeignKey('CountryReference', on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['country', 'name']
        unique_together = ('name', 'administrative_region')

    def __str__(self):
        return self.name

    def get_url(self):
        return '/locales/' + str(self.id)
