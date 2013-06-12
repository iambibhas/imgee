from os import environ
UPLOADED_FILES_DEST = 'imgee/static/test_uploads'
AWS_FOLDER = 'test/'

UNKNOWN_FILE_THUMBNAIL = 'unknown.jpeg'

#: S3 Configuration; AWS credentials with restricted access
AWS_ACCESS_KEY = environ.get('AWS_ACCESS_KEY')
AWS_SECRET_KEY = environ.get('AWS_SECRET_KEY')
AWS_BUCKET = 'imgee-testing'
AWS_FOLDER = 'test'

MEDIA_DOMAIN = 'https://%s.s3.amazonaws.com' % AWS_BUCKET

SQLALCHEMY_DATABASE_URI = 'sqlite://'
CSRF_ENABLED = False

# redis settings for RQ
RQ_DEFAULT_URL = "set it here" # set some non empty string here so that the default url is not set.
