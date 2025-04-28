from database.db_engine import engine, Base
from database.db_models import NewsCategory, Source, Admin, Article,Summary, User
Base.metadata.create_all(bind=engine, tables=[
    NewsCategory.__table__,
    Source.__table__,
    Article.__table__,
    Summary.__table__,
    User.__table__,
    Admin.__table__
])
