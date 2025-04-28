import hashlib

def create_article_hash(source_name, title, link):
    article_data = source_name + title + link
    article_hash = hashlib.sha256(article_data.encode('utf-8')).hexdigest()
    return article_hash