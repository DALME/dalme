import os
import dj_database_url
import elasticsearch
from requests_aws4auth import AWS4Auth
from django.contrib.messages import constants as messages
import saml2
from saml2.saml import NAMEID_FORMAT_EMAILADDRESS, NAMEID_FORMAT_UNSPECIFIED
from saml2.sigver import get_xmlsec_binary

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = os.environ.get('SECRET_KEY', '')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
AWS_ES_ENDPOINT = os.environ.get('AWS_ES_ENDPOINT', '')
AWS_REGION = os.environ.get('AWS_DEFAULT_REGION', '')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', '')
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
# AWS_SQS_URL = os.environ.get('AWS_SQS_QUEUE', '')

RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY', '')
RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY', '')

ZOTERO_API_KEY = os.environ.get('ZOTERO_API_KEY', '')
ZOTERO_LIBRARY_ID = os.environ.get('ZOTERO_LIBRARY_ID', '')

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEBUG = True

API_ENDPOINT = 'https://data.127.0.0.1.xip.io:8443'
PURL_ENDPOINT = 'https://purl.127.0.0.1.xip.io:8443'
DB_ENDPOINT = 'https://db.127.0.0.1.xip.io:8443'

ALLOWED_HOSTS = [
    '127.0.0.1:8000',
    '127.0.0.1',
    'localhost',
    '.127.0.0.1.xip.io',
    '.127.0.0.1.xip.io:8443',
    'db.127.0.0.1.xip.io:8443',
    'db.127.0.0.1.xip.io',
    'data.127.0.0.1.xip.io:8443',
    'data.127.0.0.1.xip.io',
    'purl.127.0.0.1.xip.io:8443',
    'purl.127.0.0.1.xip.io'
]

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
SECURE_REFERRER_POLICY = 'origin-when-cross-origin'

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_DOMAIN = '.127.0.0.1.xip.io'

CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = [
    '.127.0.0.1.xip.io',
    '.127.0.0.1.xip.io:8443',
    'data.127.0.0.1.xip.io',
    'data.127.0.0.1.xip.io:8443',
    'db.127.0.0.1.xip.io',
    'db.127.0.0.1.xip.io:8443',
    '127.0.0.1.xip.io',
    '127.0.0.1.xip.io:8443',
    'purl.127.0.0.1.xip.io:8443',
    'purl.127.0.0.1.xip.io'
]
CSRF_COOKIE_DOMAIN = '.127.0.0.1.xip.io'

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'https://*.127.0.0.1.xip.io:8443',
    'https://*.127.0.0.1.xip.io',
    'https://127.0.0.1.xip.io:8443',
    'http://127.0.0.1.xip.io',
    'https://data.127.0.0.1.xip.io:8443',
    'http://data.127.0.0.1.xip.io',
    'https://db.127.0.0.1.xip.io:8443',
    'http://db.127.0.0.1.xip.io',
    'https://purl.127.0.0.1.xip.io:8443',
    'http://purl.127.0.0.1.xip.io'
]

ROOT_HOSTCONF = 'dalme.hosts'
ROOT_URLCONF = 'dalme.devUrls'
DEFAULT_HOST = 'public'
PARENT_HOST = '127.0.0.1.xip.io:8443'
HOST_SCHEME = 'https://'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'dynamic_preferences',
    'dynamic_preferences.users.apps.UserPreferencesConfig',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django_hosts',
    'django_elasticsearch_dsl',
    # 'django_celery_results',
    # 'django_celery_beat',
    'django_q',
    'djangosaml2idp',
    'corsheaders',
    'rest_framework',
    'compressor',
    'storages',
    'django_filters',
    'modelcluster',
    'taggit',
    'maintenance_mode',
    'captcha',
    'wagtail.contrib.forms',
    'wagtail.contrib.redirects',
    'wagtail.contrib.routable_page',
    'wagtail.contrib.styleguide',
    'wagtail.embeds',
    'wagtail.sites',
    'wagtail.users',
    'wagtail.snippets',
    'wagtail.documents',
    'wagtail.images',
    'wagtail.search',
    'wagtail.admin',
    'wagtail.core',
    'wagtailmodelchooser',
    'dalme_api.application.DalmeAPIConfig',
    'dalme_app.application.DalmeConfig',
    'dalme_public.application.DalmePublicConfig',
    'dalme_purl.application.DalmePURLConfig',
]

ENABLE_DJANGO_EXTENSIONS = bool(int(os.environ.get("ENABLE_DJANGO_EXTENSIONS", "1")))
if DEBUG and ENABLE_DJANGO_EXTENSIONS:
    INSTALLED_APPS += ['django_extensions']

MIDDLEWARE = [
    'dalme_app.utils.SubdomainRedirectMiddleware',
    'django_hosts.middleware.HostsRequestMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django_currentuser.middleware.ThreadLocalUserMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'dalme_app.utils.AsyncMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'maintenance_mode.middleware.MaintenanceModeMiddleware',
    'wagtail.contrib.redirects.middleware.RedirectMiddleware',
    'django_hosts.middleware.HostsResponseMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'dalme_public.context_processors.year',
                'dalme_public.context_processors.project',
                'django.template.context_processors.request',
                'dynamic_preferences.processors.global_preferences',
            ],
            'debug': DEBUG,
        },
    },
]

WSGI_APPLICATION = 'dalme.wsgi.application'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend'
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

awsauth = AWS4Auth(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, 'es')
LOGIN_URL = 'https://db.127.0.0.1.xip.io:8443/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = 'https://dalme.org'

SAML_IDP_CONFIG = {
    'debug': DEBUG,
    'xmlsec_binary': get_xmlsec_binary(['/opt/local/bin', '/usr/bin/xmlsec1']),
    'entityid': 'https://127.0.0.1.xip.io:8443/idp/metadata',
    'description': 'DALME SAML Identity Provider Setup',
    'service': {
        'idp': {
            'name': 'DALME SAML Identity Provider',
            'endpoints': {
                'single_sign_on_service': [
                    ('https://127.0.0.1.xip.io:8443/idp/sso/post/', saml2.BINDING_HTTP_POST),
                    ('https://127.0.0.1.xip.io:8443/idp/sso/redirect/', saml2.BINDING_HTTP_REDIRECT),
                ],
                "single_logout_service": [
                    ("https://127.0.0.1.xip.io:8443/idp/slo/post/", saml2.BINDING_HTTP_POST),
                    ("https://127.0.0.1.xip.io:8443/idp/slo/redirect/", saml2.BINDING_HTTP_REDIRECT)
                ],
            },
            'name_id_format': [NAMEID_FORMAT_EMAILADDRESS, NAMEID_FORMAT_UNSPECIFIED],
            'sign_response': True,
            'sign_assertion': True,
            'want_authn_requests_signed': False,
        },
    },

    # Signing
    'key_file': PROJECT_ROOT + '/ssl-certs/dam.dalme.org.pem',
    'cert_file': PROJECT_ROOT + '/ssl-certs/dam.dalme.org.cert',
    # Encryption
    'encryption_keypairs': [{
        'key_file': PROJECT_ROOT + '/ssl-certs/dam.dalme.org.pem',
        'cert_file': PROJECT_ROOT + '/ssl-certs/dam.dalme.org.cert',
    }],
    'valid_for': 365 * 24,
}


DATABASE_ROUTERS = ['dalme_app.utils.ModelDatabaseRouter']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'read_default_file': os.path.join(BASE_DIR, 'db.cnf'),
            'sql_mode': 'traditional',
        },
        'TEST': {
            'NAME': 'dalme_app_test',
        },
    },
    'dam': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ['DAM_DB_NAME'],
        'USER': os.environ['DAM_USERNAME'],
        'PASSWORD': os.environ['DAM_PASSWORD'],
        'HOST': os.environ['DAM_HOSTNAME'],
    }
}

db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(db_from_env)

ELASTICSEARCH_DSL = {
    'default': {
        'host': AWS_ES_ENDPOINT,
        'port': 443,
        'http_auth': awsauth,
        'use_ssl': True,
        'verify_certs': True,
        'connection_class': elasticsearch.RequestsHttpConnection,
        'timeout': 360,  # Custom timeout
    },
}
ELASTICSEARCH_DSL_AUTOSYNC = True
ELASTICSEARCH_DSL_AUTO_REFRESH = True
ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = 'django_elasticsearch_dsl.signals.RealTimeSignalProcessor'
SEARCH_RESULTS_PER_PAGE = 10

REST_FRAMEWORK = {
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'DEFAULT_PAGINATION_CLASS': 'dalme_api.paginators.DALMELimitOffsetPagination',
    'PAGE_SIZE': 25,
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'dalme_api.renderers.SelectRenderer',
        'dalme_api.renderers.DTEJSONRenderer',
        'dalme_api.renderers.DBRenderer'
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'dalme_api.parsers.DTEParser',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'dalme_api.filter_backends.DalmeOrderingFilter'
    ],
    'EXCEPTION_HANDLER': 'dalme_api.utils.DTE_exception_handler',
}


DYNAMIC_PREFERENCES = {
    'MANAGER_ATTRIBUTE': 'preferences',
    'REGISTRY_MODULE': 'preferences',
    'ADMIN_ENABLE_CHANGELIST_FORM': False,
    'SECTION_KEY_SEPARATOR': '__',
    'ENABLE_CACHE': False,
    'VALIDATE_NAMES': True,
}

LANGUAGES = [
    ('en', 'English'),
    ('fr', 'French'),
]
LANGUAGE_CODE = 'en'
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_L10N = True
USE_TZ = True

DEFAULT_FILE_STORAGE = 'dalme.storage_backends.MediaStorage'
AWS_DEFAULT_ACL = None
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = 'https://%s/media/' % AWS_S3_CUSTOM_DOMAIN

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "www", 'static')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

COMPRESS_STORAGE = 'compressor.storage.BrotliCompressorFileStorage'
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True
COMPRESS_FILTERS = {
    'css': ['compressor.filters.cssmin.rCSSMinFilter'],
    'js': ['compressor.filters.jsmin.JSMinFilter']
}
COMPRESS_OFFLINE_CONTEXT = 'dalme_app.utils.offline_context_generator'

SITE_ID = 1
WAGTAIL_SITE_NAME = 'DALME'
WAGTAILIMAGES_IMAGE_MODEL = 'dalme_public.DALMEImage'

# CELERY_BROKER_URL = 'sqs://'
# CELERY_BROKER_TRANSPORT_OPTIONS = {
#     'predefined_queues': {
#         'celery': {
#             'url': AWS_SQS_URL,
#             'access_key_id': AWS_ACCESS_KEY_ID,
#             'secret_access_key': AWS_SECRET_ACCESS_KEY,
#         }
#     }
# }
# CELERY_ACCEPT_CONTENT = ['application/json']
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_BACKEND = 'django-db'

Q_CLUSTER = {
    'name': 'dalme_q_dev',
    'workers': 2,
    'recycle': 500,
    'timeout': 600,
    'retry': 620,
    'save_limit': 250,
    'queue_limit': 500,
    'bulk': 5,
    'sqs': {
        'aws_region': AWS_REGION,
        'aws_access_key_id': AWS_ACCESS_KEY_ID,
        'aws_secret_access_key': AWS_SECRET_ACCESS_KEY
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache',
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/dalme_app.log'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

MESSAGE_TAGS = {
    messages.DEBUG: 'info',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}

if "LOG_TO_STDOUT" in os.environ:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': True,
            },
        },
    }

if "HEROKU_APP_NAME" in os.environ:
    ALLOWED_HOSTS = ["*"]
