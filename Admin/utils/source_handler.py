import os
from config import DEFAULT_SOURCE_IMAGE_LOGO, SOURCE_IMAGE_UPLOAD_PATH
import config
from database.db_models import ScrapeType, Source, NewsCategory
from database.db_engine import SessionLocal
from utils.field_handler import notEmpty
from utils.file_handler import image_exists, image_upload

db = SessionLocal()

def is_valid_scrape_type(value: str) -> bool:
    try:
        ScrapeType(value)
        return True
    except ValueError:
        return False

def insert_source(name, url, news_category, type, is_active, logo=None, ttl=None):
    if notEmpty(name) or notEmpty(url) or notEmpty(news_category) or notEmpty(type) or notEmpty(is_active):
        # if logo is None:
        #     logo = DEFAULT_SOURCE_IMAGE_LOGO
        # else:
        #     if image_exists(logo, SOURCE_IMAGE_UPLOAD_PATH):
        #         return 1 # file already exists
        #     else:
        #         logo = image_upload(logo, SOURCE_IMAGE_UPLOAD_PATH,os.getcwd())
        #TODO: CAN BE ID
        category = db.query(NewsCategory).filter(NewsCategory.id==news_category).first()
        if category is None:
            return 1 #no such category
        source = db.query(Source).filter(Source.url==url).first()
        if source:
            return 2 #already url exists
        if not is_valid_scrape_type(type):
            return 3 #error type
        if ttl !=0 and ttl is not None:
            new_ttl = ttl
        else:
            new_ttl = config.DEFAULT_SCRAPE_TTL
        source = Source(
            name = name,
            logo = logo,
            url = url,
            news_category_id = category.id,
            type = ScrapeType(type),
            ttl = new_ttl,
            is_active = is_active
        )
        db.add(source)
        db.commit()
        db.close()
        return 0
    return -1

def get_sources():
    sources = db.query(Source).all()
    return sources

def update_source(id, name=None, url=None, news_category=None, type=None, is_active=None, ttl=None):
    # name, url, news_category, logo, type, is_active
    source = db.query(Source).filter(Source.id==id).first()
    if source is None:
        print("No source")
        return 1 #no such source
    if notEmpty(name):
        source.name = name
    if notEmpty(url):
        source.url = url
    if notEmpty(news_category):
        category = db.query(NewsCategory).filter(NewsCategory.id==news_category).first()
        if category is None:
            print("No category")
            return 2 #no category
        source.news_category_id = category.id
    # if logo is None:
    #     pass
    # else:
        
        # if image_exists(logo, SOURCE_IMAGE_UPLOAD_PATH):
        #     print("Image already exists")
        #     return 1 # file already exists
        # elif logo == "":
        #     logo = DEFAULT_SOURCE_IMAGE_LOGO
        # else:
        #     if source.logo != DEFAULT_SOURCE_IMAGE_LOGO:
        #         os.remove(source.logo)
        #     logo = image_upload(logo, SOURCE_IMAGE_UPLOAD_PATH, os.getcwd())
        # source.logo = logo
    if notEmpty(type):
        if not is_valid_scrape_type(type):
            return 3 #error type
        source.type = ScrapeType(type)
    if notEmpty(is_active):
        source.is_active = is_active

    if notEmpty(ttl):
        if isinstance(ttl, str):
            if ttl.isnumeric():
                if ttl !=0 and ttl is not None:
                    source.ttl = ttl
                else:
                    source.ttl = config.DEFAULT_SCRAPE_TTL
        elif isinstance(ttl, int):
            if ttl !=0 and ttl is not None:
                source.ttl = ttl
            else:
                source.ttl = config.DEFAULT_SCRAPE_TTL
    db.commit()
    db.close()
    print(db.query(Source).filter(Source.id==id).first().ttl)
    return 0

def delete_source(id):
    source = db.query(Source).filter(Source.id==id).first()
    if source is None:
        return 1 #no such source
    db.delete(source)
    db.commit()
    return 0


    