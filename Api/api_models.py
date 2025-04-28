from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

from database.db_enum import UserVerified

class MessageType(str, Enum):
    SUCCESS = 'success'
    FAILURE = 'failure'

class ArticleResponse(BaseModel):
    id: int
    title: str
    link: str
    image: str
    category_name: str  # This will be fetched from the related `news_category`
    source_name: str
    source_logo: str
    publish_timestamp: Optional[float] = None

class SummaryResponse(BaseModel):
    cluster_id:str
    source:List[ArticleResponse]
    summary:str    

class PageEnabledSummaryResponse(BaseModel):
    message:MessageType
    data:List[SummaryResponse]
    total:int
    data_count:int
    page:int
    total_page:int
    desc:str

class UserSignup(BaseModel):
    name:str
    email:str
    password:str

class UserLogin(BaseModel):
    email:str
    password:str

class TokenRequest(BaseModel):
    token: str

class ProfileResponse(BaseModel):
    id: int
    avatarid:str
    name: str
    email: str
    user_verified: UserVerified
    created_at: datetime
    updated_at: datetime

    class config:
        orm_mode = True