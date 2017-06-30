"""
Django settings for judy project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os, ConfigParser
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
config = ConfigParser.ConfigParser()
config.read(os.path.join(BASE_DIR, 'judy.conf'))

redis_host = config.get('redis', 'redis_host')
redis_port = config.get('redis', 'redis_port')
redis_password = config.get('redis', 'redis_password')
redis_db = config.get('redis', 'redis_db')

mysql_host = config.get('mysql', 'mysql_host')
mysql_port = config.get('mysql', 'mysql_port')
mysql_database = config.get('mysql', 'mysql_database')
mysql_user = config.get('mysql', 'mysql_user')
mysql_password = config.get('mysql', 'mysql_password')

ZEUSADMIN_PWD = config.get('zeusadmin','password')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '57u0g@u2o+rwmh%o_63x@8p0(ht&_6zw-g22)&7ads&5ia4fd+'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 60*60*24
# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'console',
    'interface',
    'django_rq',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'judy.urls'

WSGI_APPLICATION = 'judy.wsgi.application'


RQ_QUEUES = {
    'default': {
        'HOST': redis_host,
        'PORT': redis_port,
        'DB': redis_db,
        'PASSWORD': redis_password,
        'DEFAULT_TIMEOUT': 360,
    },
    'high': {
        'HOST': redis_host,
        'PORT': redis_port,
        'PASSWORD': redis_password,
        'DB': redis_db,
    },
    'low': {
        'HOST': redis_host,
        'PORT': redis_port,
        'PASSWORD': redis_password,
        'DB': redis_db,
    }
}

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#    }
#}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': mysql_database,
        'USER': mysql_user,
        'PASSWORD': mysql_password,
        'HOST': mysql_host,
        'PORT': mysql_port,
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'zh-cn'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
