from enum import Enum

class ScrapeType(Enum):
    RSS = "rss"
    API = "api"
    WEB = "web"

class UserVerified(int, Enum):
    VERIFIED = 1
    NOT_VERIFIED = 0