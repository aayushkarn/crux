import os
import threading
import feedparser
import json
from datetime import datetime
import newspaper
from langdetect import detect
import logging


from Fetcher.ignore_scrape import ignore_link
from database.db_enum import ScrapeType
from database.db_models import Article, Source
from database.db_engine import SessionLocal
from utils import get_local_time
from utils.article_hasher import create_article_hash
import config
from utils.file_handler import image_upload
from utils.server_image import upload_image_to_server

db=SessionLocal()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""
GETS NEWS FROM MULTIPLE RSS FEEDS AND SAVES IT IN DB
TODO: ADD SUPPORT FOR APIs AND SCRAPING
"""

def get_article_with_newspaper(entry, base_url):
    if not 'content' in entry:
        article = newspaper.article(entry.link)
        try:
            language = detect(content)
        except Exception as e:
            language = None
        if article.top_image:
            image = article.top_image
        content = [
            {
                "type":"text/html",
                "language": language,
                "base":base_url,
                "value":article.text
            }
        ]
        return image, content
    
def get_image_from_article(entry):
    image_url = None

    if 'enclosures' in entry and len(entry.enclosures) > 0:
        for enclosure in entry.enclosures:
            if enclosure.type.startswith('image/'):  # Check if it's an image
                image_url = enclosure.href
                break

    if not image_url and 'media_content' in entry:
        for media in entry.media_content:
            if 'url' in media:
                image_url = media['url']
                break

    if not image_url and 'image' in entry:
        image_url = entry.image

    if image_url:
        return image_url
    else:
        return None


def rss_scraper(source):
    """SCRAPE RSS TO GET ARTICLE_TITLE, LINK, GUID, PUBLISH_DATE, CONTENT(IF AVAILABLE), TIME_TO_LIVE(IF AVAILABLE)\n
    RETURNS PARSE_STATUS, PARSED_DATA, TIME_TO_LIVE
        -- PARSE_STATUS: 1 FOR ERROR, 0 FOR NO ERROR
        -- PARSED_DATA: NONE IF NO DATA PARSED ELSE DATA 
        -- TIME_TO_LIVE: NONE IF NO DATA ELSE DATA
    TODO: Handle if feed link is working or not
    TODO: USE TTL to scrape
    """
    news_article = []
    try:
        feed = feedparser.parse(source.url)
        if feed.status == 200:
            TIME_TO_LIVE = None if 'ttl' not in feed.feed else feed.feed['ttl']
            print(f"Scraping {source.name}\n")
            logger.info(f"Scraping {source.name}\n")
            for entry in feed.entries:
                if ignore_link(entry.link):
                    continue
                local_time = get_local_time(entry.published)

                if not 'content' in entry:
                    image, content = get_article_with_newspaper(entry, source.url)
                else:
                    content = entry.content
                    image = get_image_from_article(entry)
                if image is None:
                    image = config.DEFAULT_ARTICLE_IMAGE
                news_article.append({
                    "SOURCE":source.name,
                    "ARTICLE_TITLE":entry.title,
                    "LINK":entry.link,
                    "GUID":entry.guid,
                    "IMAGE":image,
                    "GUID_PERMANENT":entry.guidislink,
                    "PUBLISH_DATE":entry.published,
                    "LOCAL_PUBLISH_DATE": local_time[0],
                    "PUBLISH_TIMESTAMP":local_time[1],
                    "CONTENT":  content,
                })
            print(f"Scraped {source.name}\n")
            logger.info(f"Scraped {source.name}\n")
            return 0, news_article, TIME_TO_LIVE
        else:
            print(f"Unable to scrape {source['name']}\n")
            logger.info(f"Unable to scrape {source['name']}\n")
            return 1, None, TIME_TO_LIVE
    except Exception as e:
        print(f"An error occured {e}") 
        logger.info(f"An error occured {e}") 
        return None, None, None



def saveArticleToDb(datas, db):
    print(f"Saving to database for {datas[0]['SOURCE']}")
    logger.info(f"Saving to database for {datas[0]['SOURCE']}")
    for data in datas:
        hashed_article = create_article_hash(data['SOURCE'], data['ARTICLE_TITLE'], data['LINK'])
        old_article = db.query(Article).filter(Article.hash==hashed_article).first()
        if old_article is None:
            if data['IMAGE'] != config.DEFAULT_ARTICLE_IMAGE:
                img = image_upload(data['IMAGE'],config.ARTICLE_IMAGE_UPLOAD_PATH, os.getcwd(), thumbnail=False)
                if config.REMOTE_HOST:
                    local_file = os.path.join(os.path.abspath(__file__), '..', '..', img)
                    if os.path.exists(local_file):
                        upload_image_to_server(local_file, config.REMOTE_IMAGE_UPLOAD, config.UPLOAD_MEDIA_SECRET_KEY)
                    else:
                        #TODO: Apply default image for article
                        print("Unable to upload image")
            else:
                img = data['IMAGE']

            new_article = Article(
                hash = hashed_article,
                source_id = db.query(Source).filter(Source.name == data['SOURCE']).first().id,
                image = img,
                title = data['ARTICLE_TITLE'],
                link = data['LINK'],
                guid = data['GUID'],
                publish_date = data['PUBLISH_DATE'],
                local_publish_date = data['LOCAL_PUBLISH_DATE'],
                publish_timestamp = data['PUBLISH_TIMESTAMP'],
                content = data['CONTENT'][0]['value']
            )
            db.add(new_article)
            db.commit()
            db.close()
            
def article_scraper(source_id,db):
    try:
        source = db.query(Source).filter(Source.id == source_id).first()
        if source.type == ScrapeType.RSS:
            status, datas, ttl = rss_scraper(source=source)
            if status != 1:
                source.ttl = None if ttl is None else ttl
                saveArticleToDb(datas,db)
    except Exception as e:
        print(f"Error occured {e}")
        logger.info(f"Error occured {e}")
    finally:
        db.close()

def run_scraper():
    sources = db.query(Source).filter(Source.is_active==True).all()
    threads = []
    for source in sources:
        new_db_session = SessionLocal()
        t = threading.Thread(target=article_scraper, args=(source.id,new_db_session))
        t.start()
        threads.append(t)
    for thread in threads:
        thread.join()
