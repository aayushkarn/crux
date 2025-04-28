from functools import wraps

from flask import redirect, session, url_for

from database.db_engine import SessionLocal


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'admin' not in session or session['admin'] == "":
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper

def login_not_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'admin' in session:
            return redirect(url_for('admin.index')) 
        return func(*args, **kwargs)
    return wrapper

def with_session(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        db = SessionLocal()
        try:
            return func(db, *args, **kwargs)
        finally:
            db.close()
    return wrapper