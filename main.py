from Api import api
# from database.db_models import *
import config
from database.db_engine import engine, Base
Base.metadata.create_all(bind=engine)

def admin_creator():
    from database.db_models import Admin
    from database.db_engine import SessionLocal
    from database.db_enum import UserVerified

    db=SessionLocal()
    admin = db.query(Admin).all()
    if admin == []:
        new_admin = Admin(
            name=config.DEFAULT_ADMIN_NAME,
            email=config.DEFAULT_ADMIN_EMAIL,
            password=config.DEFAULT_ADMIN_PASSWORD, 
            user_verified=UserVerified.VERIFIED
        )
        db.add(new_admin)
        db.commit()

    db.close()


if __name__ == "__main__":
    # import subprocess
    # subprocess.Popen(['cmd', '/C', 'start', 'python', 'article_pipeline.py'])
    admin_creator()
    api.start_api()
    
    