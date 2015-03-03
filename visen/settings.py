#encoding:UTF-8
# Django settings for visen project.

import os, socket

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
ROOT_PATH = os.path.dirname(__file__)
hostname = socket.gethostname()

DEBUG = False

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

PROJECT_NAME = 'visen'
DEPLOYMENT_NAME = PROJECT_NAME
DEPLOYMENT_SUBNET = "ecs.soton.ac.uk"

PROTOCOL = "https"
# Put the hostname where the site will be deployed here.
DEPLOYMENT_HOSTS = ['hci']
if hostname in DEPLOYMENT_HOSTS:
    LIVE = True
else:
    LIVE = False

if LIVE:
    ROOT_URL = '%s://%s.%s/%s/' % (PROTOCOL, hostname, DEPLOYMENT_SUBNET, DEPLOYMENT_NAME)
    BASE_URL = '/' + DEPLOYMENT_NAME
    HOSTING = 'deployment'
else:
    ROOT_URL = 'http://127.0.0.1:8000/'
    BASE_URL = ''
    DEBUG = True
    HOSTING = 'development'

TEMPLATE_DEBUG = DEBUG

if LIVE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': DEPLOYMENT_NAME,
            'USER': DEPLOYMENT_NAME,
            'PASSWORD': DEPLOYMENT_NAME+'@1amhc1too',
            'HOST': '',
            'PORT': '',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'visen',
            'USER': 'root',
            'PASSWORD': '',
            'HOST': 'localhost',
            'PORT': '',
        }
    }

   # DATABASES = {
   #      'default': {
   #          'ENGINE': 'django.db.backends.sqlite3',
   #          'NAME': os.path.join(ROOT_PATH, '../sqlite.db'),
   #          'USER': '',
   #          'PASSWORD': '',
   #          'HOST': '',
   #          'PORT': '',
   #      }
   #  }


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(ROOT_PATH, 'media')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"

if LIVE:
    STATIC_URL = ROOT_URL + 'media/'
else:
    STATIC_URL = '/media/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '&amp;!@8lco2xhg&amp;j3=uf)t1xbjb1qu4%p#h_l2+hl@e-g%5768rdp'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = PROJECT_NAME + '.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = PROJECT_NAME+'.wsgi.application'

TEMPLATE_DIRS = ( os.path.join(SITE_ROOT, 'templates'), )

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.static',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'basicutils.djutils.populate_context',
    'frontend.context.default',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'registration',
    'sd_store',
    'basicutils',
    'basic_registration',
    'multiplot',
    'django.contrib.admin',
    'frontend',
)

if not LIVE:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = "webmaster@%s.%s" % (hostname, DEPLOYMENT_SUBNET)
SERVER_EMAIL = "webmaster@%s.%s" % (hostname, DEPLOYMENT_SUBNET)

# for registration module
ACCOUNT_ACTIVATION_DAYS = 3
DEFAULT_FROM_EMAIL = "webmaster@%s.%s" % (hostname, DEPLOYMENT_SUBNET)

# URL that handles the LOGIN path when running in local machine
LOGIN_URL = ROOT_URL + 'accounts/login'

# URL that handles the LOGOUT path when running in local machine
LOGOUT_URL = ROOT_URL + ''

# URL that handles the LOGIN path when running in local machine
LOGIN_REDIRECT_URL = ROOT_URL

if LIVE:
    logFilename = '/srv/log/' + DEPLOYMENT_NAME + '/usage.log'
else:
    logFilename = 'usage.log'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'json': {
            'format': '{"level": "%(levelname)s", "timestamp": "%(asctime)s", %(message)s}'
        },
        'simple': {
            'format': 'iot | %(levelname)s %(asctime)s %(message)s'
        },
        'detailed': {
            'format': "iot | %(levelname)s %(asctime)s \n%(pathname)s %(filename)s \n%(funcName)s \n%(message)s"
        },

    },
    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file':{
            'level':'DEBUG',
            'class':'logging.FileHandler',
            'formatter': 'simple',
            'filename': logFilename
        },
        'file_json':{
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'formatter': 'json',
            'filename': logFilename
        },
        'mail_admins': {
            'level': 'WARNING',
            'formatter': 'detailed',
            'class': 'django.utils.log.AdminEmailHandler',
            #'filters': [],
            'include_html': True,
        }
    },
    'root': {
        'handlers': ['mail_admins'],
        'level': 'WARNING'
    },
    'loggers': {
                # "catch-all" logger?
        '': {
            'handlers': ['file', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': True,
        },

        'custom': {
            'handlers': ['file', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': True,
        },

        'django': {
            'handlers':['null'],
            'level':'INFO',
            'propagate': True,
        },

        'django.request': {
            'handlers': ['null'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}
