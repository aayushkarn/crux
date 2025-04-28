from sqlalchemy import Column, DateTime, Float, Integer, String, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database.db_engine import Base
from database.db_enum import ScrapeType, UserVerified


class NewsCategory(Base):
    __tablename__ = "news_category"

    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(255), unique=True, nullable=False)

    sources = relationship("Source", back_populates="news_category")

    def __repr__(self):
        return f"{self.category_name}"


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
    logo = Column(String(255))
    url = Column(String(500), unique=True, index=True)
    news_category_id = Column(Integer, ForeignKey("news_category.id"), nullable=False)
    type = Column(Enum(ScrapeType), nullable=False)
    is_active = Column(Boolean, default=True)
    ttl = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    news_category = relationship("NewsCategory", back_populates="sources")
    articles = relationship("Article", back_populates="source")

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    hash = Column(String(200), unique=True, nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    image = Column(String(255))
    title = Column(String(500), nullable=False)
    link = Column(String(500), nullable=False)
    guid = Column(String(500))
    publish_date = Column(String(100))
    local_publish_date = Column(String(100))
    publish_timestamp = Column(Float)
    content = Column(Text)
    cluster_id = Column(String(500), nullable=True, index=True)  # Add index here
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    source = relationship("Source", back_populates="articles")

    # Corrected relationship to summaries
    summaries = relationship(
        "Summary",
        back_populates="article",
        cascade="all, delete-orphan",  # Cascade delete orphaned summaries
        passive_deletes=True,
        primaryjoin="Article.cluster_id == foreign(Summary.cluster_id)"
    )


    def __repr__(self):
        return f"{self.id}-{self.title}"


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(String(500), ForeignKey("articles.cluster_id", ondelete="CASCADE"), index=True) 
    summary = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    article = relationship(
        "Article",
        back_populates="summaries",
        primaryjoin="foreign(Summary.cluster_id) == Article.cluster_id",
        viewonly=True
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, unique=True)
    avatarid = Column(String(100), default=uuid.uuid4().hex)
    name = Column(String(100))
    email = Column(String(100))
    password = Column(String(100))
    user_verified = Column(Enum(UserVerified), default=UserVerified.NOT_VERIFIED)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Admin(Base):
    __tablename__ = "admin"

    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String(100))
    email = Column(String(100))
    password = Column(String(100))
    user_verified = Column(Enum(UserVerified),default=UserVerified.NOT_VERIFIED)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
