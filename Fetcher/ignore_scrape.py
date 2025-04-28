import re 

RESTICTED_SUB_LINKS = [
    "https://www.bbc.com/news/videos/",
]

def ignore_link(link):
    if any(re.search(sub_link, link) for sub_link in RESTICTED_SUB_LINKS):
        print(f"Ignored restricted link {link}")
        return True
    return False
