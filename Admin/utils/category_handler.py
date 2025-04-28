from database.db_engine import SessionLocal
from database.db_models import NewsCategory, Source
from utils.field_handler import notEmpty

db = SessionLocal()

def create_category(name):
    category = db.query(NewsCategory).filter(NewsCategory.category_name==name).first()
    if category:
        return 1 #already exists
    if notEmpty(name):
        name = name.lower()
        new_category = NewsCategory(category_name=name)
        db.add(new_category)
        db.commit()
        db.refresh(new_category)
        return 0
    return 1 

def read_category():
    category = db.query(NewsCategory).all()
    return category

def update_category(id, name):
    category = db.query(NewsCategory).filter(NewsCategory.id==id).first()
    if category:
        name = name.lower()
        category.category_name = name
        db.commit()
        return 0
    return 1

def delete_category(id):
    category = db.query(NewsCategory).filter(NewsCategory.id==id).first()
    if category:
        all_child_sources = [source.name for source in category.sources]
        if confirm_delete_category(all_child_sources):
            sources = db.query(Source).filter(Source.news_category_id==category.id).all()
            for s in sources:
                db.delete(s)
            db.delete(category)
            db.commit()
        else:
            return 1 #not deleted
        return 0    
    return 1

def confirm_delete_category(obj):
    print(f"{obj} will be deleted")
    a = input("Do you want to delete?(y/n)")
    if a.lower() == "y":
        return True
    else:
        return False