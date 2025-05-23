from dotenv import load_dotenv
import os

load_dotenv()

NAME = "Crux"
DESCRIPTION ="Short curated news for your feed"
TIME_STANDARD = "Asia/Kathmandu"
SCRAPE_RETRIES =  2 
DATABASE_URL = ""
DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOSTNAME = os.getenv("DATABASE_HOSTNAME")
DATABASE_NAME = os.getenv("DATABASE_NAME")

REMOTE_HOST = True

if REMOTE_HOST:
    SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOSTNAME}:3306/{DATABASE_NAME}"
else:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./crux2.db"  

ALLOWED_IMAGE_EXTENSION = ['jpg', 'jpeg', 'png']
SOURCE_IMAGE_UPLOAD_PATH = "media/img/source_logo/"
ARTICLE_IMAGE_UPLOAD_PATH = "media/img/article/"
DEFAULT_SOURCE_IMAGE_LOGO = "media/img/source_logo/default_source_logo.png"
DEFAULT_ARTICLE_IMAGE = "media/img/article/default_article.jpg"

DEFAULT_SCRAPE_TTL = 10 #In minutes

AVOID_CLUSTER_AFTER_DAYS = 3 #maximum days after which clustering will be avoided
CLUSTER_SIMILARITY_THRESHOLD = 0.7

if REMOTE_HOST:
    SUMMARY_REDIS_IP_ADDRESS = os.getenv("GLOBAL_REDIS_IP_ADDRESS")
    SUMMARY_REDIS_PORT = os.getenv("GLOBAL_REDIS_PORT")
    SUMMARY_REDIS_PASSWORD = os.getenv("GLOBAL_REDIS_PASSWORD")
else:
    SUMMARY_REDIS_IP_ADDRESS = os.getenv("LOCAL_REDIS_IP_ADDRESS")
    SUMMARY_REDIS_PORT = os.getenv("LOCAL_REDIS_PORT")
    SUMMARY_REDIS_PASSWORD = os.getenv("LOCAL_REDIS_PASSWORD")

LIMIT_ARTICLE_BY_PAGE = 20

# JWT
# ACCESS_TOKEN_EXPIRY_MINUTE = 30 #minutes
# REFRESH_TOKEN_EXPIRY_MINUTE = 60*24*7 #days
ACCESS_TOKEN_EXPIRY_MINUTE = 30 #minutes
REFRESH_TOKEN_EXPIRY_MINUTE = 60*24*7 #days
ALGORITHM = 'HS256'
JWT_SECRET_KEY = os.environ['JWT_SECRET_KEY']
JWT_REFRESH_SECRET_KEY = os.environ['JWT_REFRESH_SECRET_KEY']
ADMIN_JWT_SECRET_KEY = os.environ['ADMIN_JWT_SECRET_KEY']
ADMIN_JWT_REFRESH_SECRET_KEY = os.environ['ADMIN_JWT_REFRESH_SECRET_KEY']
FLASK_SECRET_KEY = os.environ['FLASK_SECRET_KEY']


DEFAULT_ADMIN_NAME = "Admin"
DEFAULT_ADMIN_EMAIL = "admin@crux.com"
DEFAULT_ADMIN_PASSWORD = "$2b$12$BSy.UWHPAYpQviI56wYtU.Kv05bHYY2OT1DF8feYMfiRYxpIb/m4i" #admin123

OWN_URL = "http://localhost:800/"

REMOTE_IMAGE_UPLOAD = os.getenv("REMOTE_URL") 
UPLOAD_MEDIA_SECRET_KEY = os.getenv("UPLOAD_MEDIA_SECRET_KEY")

