from collections import defaultdict
import json
import shutil
from fastapi import FastAPI, File, HTTPException, Depends, Header, UploadFile, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from utils.jwt_handler import create_access_token, create_refresh_token, verify_refresh_token,verify_access_token
from utils.password_handler import get_hashed_password, verify_hashed_password
from utils.validators import validate_email, validate_password
from sqlalchemy.orm import Session
from Api.api_models import ArticleResponse, MessageType, PageEnabledSummaryResponse, SummaryResponse, UserLogin, UserSignup, TokenRequest, ProfileResponse
from jose import JWTError, jwt

import os
import redis
import config

# from Admin.api.routers import authentication, sources
import uvicorn

from database.db_engine import get_db
from database.db_models import *

app = FastAPI()
# app.include_router(authentication.router)
# app.include_router(sources.router)
if config.REMOTE_HOST:
    r = redis.Redis(host=config.SUMMARY_REDIS_IP_ADDRESS, port=config.SUMMARY_REDIS_PORT, password=config.SUMMARY_REDIS_PASSWORD)
else:
    print("LOCAL")
    r = redis.Redis(host=config.SUMMARY_REDIS_IP_ADDRESS, port=config.SUMMARY_REDIS_PORT)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)
app.mount('/media', StaticFiles(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..","media")), name="media")

oauth2_schema=OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token:str=Depends(oauth2_schema), db:Session=Depends(get_db)):
    credentials_exception=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate":"Bearer"},
    )
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=config.ALGORITHM)
        user_data=payload['sub'].replace("'",'"')
        user_id = json.loads(user_data)['id']
        print(user_id)
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id==user_id).first()
    if user is None:
        raise credentials_exception
    return user

@app.get("/api/hello")
async def hi():
    return {"hi":"hi"}

@app.post("/api/signup")
async def create_user(userSignup:UserSignup, db:Session =Depends(get_db)):
    email = userSignup.email
    name = userSignup.name
    password = userSignup.password

    if name is None or name=="":
        raise HTTPException(status_code=400, detail="Name must be   provided")
    if email is None or email=="":
        raise HTTPException(status_code=400, detail="Email must be provided")
    if password is None or password=="":
        raise HTTPException(status_code=400, detail="Password must be provided")
    if not validate_email(email):
        raise HTTPException(status_code=400, detail="Email is not valid")
    if not validate_password(password):
        raise HTTPException(status_code=400, detail="Password must be atleast 6 characters")
    user = db.query(User).filter(User.email==email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already exists!")
    else:
        hashed_password = get_hashed_password(password)
        user = User(
            email = email,
            name = name,
            password = hashed_password   
        )
        db.add(user)
        db.commit()

        new_user = db.query(User).filter(User.email==email).first()
        user_data = {"id":new_user.id}
        access_token = create_access_token(user_data)
        refresh_token = create_refresh_token(user_data)
        return {
            "access_token":access_token,
            "refresh_token":refresh_token,
        }
        


@app.post("/api/login")
async def login(userLogin:UserLogin, db:Session = Depends(get_db)):
    email = userLogin.email
    password = userLogin.password

    if email is None or email=="":
        raise HTTPException(status_code=400, detail="Email is not valid")
    if password is None or password=="":
        raise HTTPException(status_code=400, detail="Password cannot be empty")
    user = db.query(User).filter(User.email==email).first()
    if user is None:
        raise HTTPException(status_code=400, detail="No such user exists!")
    else:
        if not verify_hashed_password(password, user.password):
            raise HTTPException(status_code=400, detail="Email or Password incorrect")
        else:
            user_data = {"id":user.id}
            access_token = create_access_token(user_data)
            refresh_token = create_refresh_token(user_data)
            return {
                "access_token":access_token,
                "refresh_token":refresh_token,
            }

@app.post("/api/refresh")
async def refresh_access_token(request:TokenRequest):
    refresh_token = request.token
    if refresh_token is None:
        raise HTTPException(status_code=400, detail="Access token not provided")
    if refresh_token is None:
        raise HTTPException(status_code=400, detail="Refresh Token not provided")
    payload = verify_refresh_token(refresh_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Refresh Token is invalid!")
    new_user_data = payload.replace("'", '"')
    json_user_data = json.loads(new_user_data)['id']
    
    access_token  = create_access_token({"id":json_user_data})
    new_refresh_token = create_refresh_token({"id":json_user_data})
    return {
        "access_token":access_token,
        "refresh_token":new_refresh_token,
    }

@app.post("/api/verify")
async def verify_token(request: TokenRequest):
    token = request.token
    if token is None:
        raise HTTPException(status_code=400, detail="Access token not provided")
    print("performing payload")
    payload = verify_access_token(token)
    print(payload)
    if payload is None:
        raise HTTPException(status_code=401, detail="Access token is invalid")
    return True
    
@app.get("/api")
# @app.get("/", response_model=PageEnabledSummaryResponse)
async def main(db:Session = Depends(get_db), page:int = 0,current_user: User = Depends(get_current_user)):
    
    cached = r.get("summary_api")
    if cached:
        print("Using cached!")
        return json.loads(cached)

    query = (
        db.query(Summary, Article, Source, NewsCategory.category_name)
        .select_from(Summary)
        .join(Article, Summary.cluster_id==Article.cluster_id)
        .join(Source, Article.source_id==Source.id)
        .join(NewsCategory, Source.news_category_id==NewsCategory.id)
        .filter(Summary.summary is not None and Summary.summary != '')
        .order_by(Article.publish_timestamp.desc())
    ).all()
    
    if not query:
       
        return {'message':'No data found ok'}
    

    cluster_articles = defaultdict(list)
    cluster_summaries = {}

    # Iterate over results and print
    for summary, article, source, category_name in query:
        cluster_articles[article.cluster_id].append(ArticleResponse(
            id= article.id,
            title= article.title,
            link=article.link,
            image=article.image,
            category_name=category_name,
            source_name=source.name,
            source_logo=source.logo,
            publish_timestamp=article.publish_timestamp
        ))

        if article.cluster_id not in cluster_summaries:
            cluster_summaries[article.cluster_id] = summary.summary


    summary_responses = []
    for cluster_id, articles in cluster_articles.items():
        summary_responses.append(SummaryResponse(
            cluster_id=cluster_id,
            source=articles,
            summary=cluster_summaries[cluster_id]
        ))

    print(len(summary_responses))

    r.setex("summary_api", config.DEFAULT_SCRAPE_TTL*60, json.dumps([response.dict() for response in summary_responses]))
    return summary_responses

@app.get('/api/me',response_model=ProfileResponse)
# @app.get('/me')
async def profile(current_user:User = Depends(get_current_user)):
    return current_user

@app.post("/upload/")
async def upload_file(
    file:UploadFile=File(...),
    x_secret_key: str = Header(None)
    ):
    if x_secret_key != config.UPLOAD_MEDIA_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid secret key")

    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    project_root_dir = os.path.join(current_file_dir, "..")
    upload_folder = os.path.join(project_root_dir, "media", "img","test")

    # upload_folder = os.path.join(os.path.abspath(__file__), '..', '..', config.ARTICLE_IMAGE_UPLOAD_PATH)
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # return {'ok':'ok'}
    return {'filename':file.filename}

def start_api():
    uvicorn.run("Api.api:app", host="0.0.0.0", port=800, reload=True)
