# Crux - News Summarizer Backend
```bash
> python --version
  Python 3.10.0
```
Currently only supports rss feeds and has been built around rss feed from [`BBC`](https://feeds.bbci.co.uk/news/world/rss.xml).
Setup your virtual environment and then install requirements.

```
pip install -r requirements.py
```

Also install Redis.

## Models Used (Inside `models/` folder)

- [`facebook/bart-large-cnn`](https://huggingface.co/facebook/bart-large-cnn) — for summarization
- `nltk` — for basic natural language processing
- [`paraphrase-MiniLM-L3-v2`](https://huggingface.co/sentence-transformers/paraphrase-MiniLM-L3-v2) — for clustering semantic similarity
---
## Setup ```.env```  file
```
DATABASE_USERNAME = "YOUR-DB-USERNAME"
DATABASE_PASSWORD = "YOUR-DB-PASSWORD"
DATABASE_HOSTNAME = "YOUR-DB-HOST-IP"
DATABASE_NAME = "YOUR-DB-NAME"

JWT_SECRET_KEY = "SECRET-KEY-FOR-JWT-ACCESS-TOKEN"
JWT_REFRESH_SECRET_KEY = "SECRET-KEY-FOR-JWT-REFRESH-TOKEN"

ADMIN_JWT_SECRET_KEY = "ADMIN_JWT_ACCESS_TOKEN_SECRET_KEY"
ADMIN_JWT_REFRESH_SECRET_KEY = "ADMIN_JWT_ACCESS_REFRESH_SECRET_KEY"
FLASK_SECRET_KEY = "FLASK-SECRET-KEY"

LOCAL_REDIS_IP_ADDRESS = "localhost"
LOCAL_REDIS_PORT = 6379 #change if somthing else
LOCAL_REDIS_PASSWORD = ""

GLOBAL_REDIS_IP_ADDRESS = "REMOTE-REDIS-IP-IF-USING-REMOTE-HOST"
GLOBAL_REDIS_PORT = 6379 #check port
GLOBAL_REDIS_PASSWORD = "REMOTE-REDIS-PASSWORD"

UPLOAD_MEDIA_SECRET_KEY = "SOME-SECRET-KEY-FOR-UPLOAD"

REMOTE_URL = "REMOTE_IP:PORT/upload/"
```


## Media Storage

- **Article images** are saved inside:
  ```
  media/img/article/
  ```

- **Source logo images** are saved inside:
  ```
  media/img/source_logo/
  ```


---
## Running API
In a separate terminal, start the Fastapi. By default you can access api at ```localhost:800/```  

```bash
python main.py
``` 


Make sure redis-server is running as we use caching for ```/api/```.

---

## Running Admin
In a separate terminal, start the Fastapi. By default you can access admin panel at ```localhost:5000/admin```  
```bash
python run_admin.py
```
---

## Running Celery flower
To visualize the workers and tasks we can use celery flower. By default you can access  at ```localhost:5555/```  
```bash
celery -A CelerySummarizer.tasks flower
```

Make sure Redis is running before launching.

---

## Running Celery Worker
In a separate terminal, start the Celery worker to process queued summarization tasks:

```bash
celery -A CelerySummarizer.tasks worker --pool=solo --loglevel=info
```

Make sure Redis is running before launching the worker.

---

## Future Improvements
- Dockerize the app for easier deployment
- Add automatic retriggering pipelines via Celery Beat
- Websocket support for real-time updates to users
- Admin approval workflows for generated summaries

---


## Acknowledgements
- [FastAPI](https://fastapi.tiangolo.com/)
- [Flask-Admin](https://flask-admin.readthedocs.io/)
- [Redis](https://redis.io/)
- [Celery](https://docs.celeryq.dev/)
- [Huggingface Transformers](https://huggingface.co/transformers/)
- [NLTK](https://www.nltk.org/)

---
