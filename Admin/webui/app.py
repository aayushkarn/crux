import os
import tempfile
import uuid
from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.filters import FilterEqual, FilterInList
from flask_admin import AdminIndexView, expose
from flask_admin.menu import MenuLink
from markupsafe import Markup
from sqlalchemy import func
from wtforms import FileField, PasswordField, StringField
from Admin.webui.utils import login_not_required, login_required
import config
from database.db_engine import SessionLocal
from database.db_models import Article, Admin as ad, NewsCategory, Source, Summary, User


from utils.file_handler import image_upload, remove_image
from utils.password_handler import get_hashed_password, verify_hashed_password
from utils.server_image import upload_image_to_server


# Create Flask application
app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY
# app.config['CACHE_TYPE'] = 'null'  
# db = SessionLocal()


@app.after_request
def add_cache_control_headers(response):
    if 'admin' not in session:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response


@app.route('/')
def main():
    return render_template("landing.html")

@app.route('/summary/<clusterid>')
def summary_view(clusterid):
    db = SessionLocal()
    try:
        summary = db.query(Summary).filter(Summary.cluster_id==clusterid).first()
        if summary is None:
            return "No such summary"
        articles = db.query(Article).filter(Article.cluster_id==summary.cluster_id).all()
        
        image = config.OWN_URL+articles[0].image
        sources = []
        for article in articles:
            source = db.query(Source).filter(Source.id==article.source_id).first()
            sources.append({
                'name':source.name,
                'logo':config.OWN_URL+source.logo,
                'link':article.link
            })
        print(sources)
        # for source in summary.
        # logo = config.OWN_URL+summary.source.logo
        return render_template('summary.html', summary=summary, image=image, sources=sources)
    finally:
        db.close()


@app.route("/login", methods=['POST', 'GET'])
@login_not_required
def login():
    error=None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if not email or email == "":
            error = "Email not provided"
        elif not password or password == "":
            error = "Password not provided"
        else:
            db = SessionLocal()
            admin = db.query(ad).filter(ad.email==email).first()
            print("admin", admin)
            if admin is None:
                error = "Access Forbidden"
            else:
                if not verify_hashed_password(password, admin.password):
                    error = "Invalid email or password"
                else:
                    session['admin'] = admin.email
                    db.close()
                    return redirect(url_for('admin.index'))

    return render_template("login.html", error=error)

@app.route("/logout")
@login_required
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

@app.route('/view-article/<hash>')
def article_view(hash):
    db = SessionLocal()
    try:
        article = db.query(Article).filter(Article.hash == hash).first()
        image = config.OWN_URL+article.image
        logo = config.OWN_URL+article.source.logo
        if article is None:
            return "No such page exists"
        return render_template('view_article.html', article=article, image=image, logo=logo)
    finally:
        db.close()

class SecureModelView(ModelView):
    def is_accessible(self):
        return 'admin' in session 
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

class SecureAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        if 'admin' not in session:
            return redirect(url_for('login'))
        return super(SecureAdminIndexView,self).index()

# Initialize Flask-Admin
admin_panel = Admin(
    app,
    name="Crux",
    template_mode="bootstrap4",
    endpoint="admin",
    url="/admin",
    index_view=SecureAdminIndexView(name="Home"),
)


def clustered_ids():
    db = SessionLocal()
    db_query = (
            db.query(Article.cluster_id)
            .filter(Article.cluster_id != None)
            .group_by(Article.cluster_id)
            .having(func.count(Article.id) > 1)
            .all()
        )
    db.close()
    return [
        row[0] for row in db_query
    ]

class ArticleView(SecureModelView):
    def __init__(self, model, session_maker, **kwargs):
        self.session_maker = session_maker
        super().__init__(model, session=session_maker(), **kwargs)

    def get_query(self):
        # Use a scoped session for proper session management within the request context
        db = self.session_maker()
        if not self.model:
            raise ValueError("Model is not set correctly in NewsCategoryView.")
        try:
            query = db.query(self.model)
            if query is None:
                raise ValueError("Query returned None, model might not be set correctly.")
            return query
        finally:
            db.close()

    def get_count_query(self):
        db = self.session_maker()
        try:
            query = db.query(func.count('*')).select_from(self.model)
            if query is None:
                raise ValueError("Query returned None, model might not be set correctly.")
            return query
        finally:
            db.close()

    can_create = False  
    can_edit = False 
    column_list = ('title', 'content_preview', 'source_name','cluster_id','publish_date')
    column_sortable_list = ['title', 'content', 'source_id', 'publish_date']
    column_default_sort = ('publish_timestamp', True)
    column_searchable_list = ('content','cluster_id',)
    # column_filters = ('content','source_id')

    column_filters = [
        'source_name',
        FilterInList(
            Summary.cluster_id,
            'Is Clustered',
            options=lambda: [(cid, f"Cluster {cid}") for cid in clustered_ids()]
        )
    ]

    column_labels = {
        'content_preview': 'Content',
        'source_name': 'Source',
    }

    column_exclude_list = ['content', 'source_id']


    # Format the preview content with a link to view full
    def _content_preview(view, context, model, name):
        preview = (model.content[:100] + '...') if model.content else ''
        return Markup(f"{preview} <a href='{url_for('article_view', hash=model.hash)}' target='_blank'>View</a>")
    def _source_name(view, context, model, name):
        db = SessionLocal()
        source = db.query(Source).filter(Source.id==model.source_id).first().name
        db.close()
        return source

    column_formatters = {
        'content_preview': _content_preview,
        'source_name': _source_name
    }   

    def get_source_filter_options(self):
        db = SessionLocal()
        sources = db.query(Source).order_by(Source.name).all()
        db.close()
        return [(s.id, s.name) for s in sources]
    
    def scaffold_filters(self, name):
        if name == "source_name":
            return [
                FilterEqual(
                    column=Article.source_id,
                    name="Source name",
                    options=self.get_source_filter_options()
                )
            ]
        return super().scaffold_filters(name)


class AdminView(SecureModelView):
    def __init__(self, model, session_maker, **kwargs):
        self.session_maker = session_maker
        super().__init__(model, session=session_maker(), **kwargs)

    def get_query(self):
        # Use a scoped session for proper session management within the request context
        db = self.session_maker()
        if not self.model:
            raise ValueError("Model is not set correctly in NewsCategoryView.")
        try:
            query = db.query(self.model)
            if query is None:
                raise ValueError("Query returned None, model might not be set correctly.")
            return query
        finally:
            db.close()

    def get_count_query(self):
        db = self.session_maker()
        try:
            query = db.query(func.count('*')).select_from(self.model)
            if query is None:
                raise ValueError("Query returned None, model might not be set correctly.")
            return query
        finally:
            db.close()
    
    column_exclude_list = ('password',)
    form_excluded_columns = ('password','created_at','updated_at',)

    form_create_rules = (
        'name', 'email', 'new_password', 'user_verified',
    )

    form_extra_fields = {
        'new_password': PasswordField('Password'),
    }

    def on_model_change(self, form, model, is_created):
        if not form.name.data or form.name.data == "":
            raise ValueError("Name cannot be empty")
        if not form.email.data or form.email.data == "":
            raise ValueError("Email cannot be empty")
        if not form.new_password.data or form.new_password.data == "":
            raise ValueError("Password cannot be empty")
        if form.user_verified is None:
            raise ValueError("UserVerified cannot be empty")
        if is_created:
            if form.new_password.data:
                if len(form.new_password.data)<6:
                    raise ValueError("Password must be atleast of 6 digits")
                model.password = get_hashed_password(form.new_password.data)
        else:
            if form.new_password.data or form.new_password.data != "":
                if len(form.new_password.data)<6:
                    raise ValueError("Password must be atleast of 6 digits")
                model.password = get_hashed_password(form.new_password.data)
        return super().on_model_change(form, model, is_created)


class UserView(SecureModelView):
    def __init__(self, model, session_maker, **kwargs):
        self.session_maker = session_maker
        super().__init__(model, session=session_maker(), **kwargs)

    def get_query(self):
        # Use a scoped session for proper session management within the request context
        db = self.session_maker()
        if not self.model:
            raise ValueError("Model is not set correctly in NewsCategoryView.")
        try:
            query = db.query(self.model)
            if query is None:
                raise ValueError("Query returned None, model might not be set correctly.")
            return query
        finally:
            db.close()

    def get_count_query(self):
        db = self.session_maker()
        try:
            query = db.query(func.count('*')).select_from(self.model)
            if query is None:
                raise ValueError("Query returned None, model might not be set correctly.")
            return query
        finally:
            db.close()
    
    can_create = False
    column_exclude_list = ('password','avatarid',)
    form_excluded_columns = ('password','created_at','updated_at','avatarid',)
    # form_excluded_columns = ('password','created_at','updated_at',)

class SummaryView(SecureModelView):
    def __init__(self, model, session_maker, **kwargs):
        self.session_maker = session_maker
        super().__init__(model, session=session_maker(), **kwargs)

    def get_query(self):
        # Use a scoped session for proper session management within the request context
        db = self.session_maker()
        if not self.model:
            raise ValueError("Model is not set correctly in NewsCategoryView.")
        try:
            query = db.query(self.model)
            if query is None:
                raise ValueError("Query returned None, model might not be set correctly.")
            return query
        finally:
            db.close()

    def get_count_query(self):
        db = self.session_maker()
        try:
            query = db.query(func.count('*')).select_from(self.model)
            if query is None:
                raise ValueError("Query returned None, model might not be set correctly.")
            return query
        finally:
            db.close()
    

    can_create = False
    # column_list = ['article.title', 'summary', 'cluster_id', 'created_at']
    # column_default_sort = ('summary', True)
    # column_sortable_list = ['id', 'article.title', 'summary', 'created_at']
    # column_labels = {'article.title': 'Article'}
    # column_searchable_list = ['article.title', 'cluster_id']

    column_list = ['cluster_id','summary', 'created_at']
    column_default_sort = ('summary', True)
    column_sortable_list = ['id', 'summary', 'created_at']
    column_labels = {'article.title': 'Article'}
    column_searchable_list = ['cluster_id']
    

    form_columns = ['summary']

    # form_args = {
    #     'article': {
    #         'query_factory': lambda: db.query(Article),
    #         'label': 'Article',
    #     }
    # }
    
class NewsCategoryView(SecureModelView):
    def __init__(self, model, session_maker, **kwargs):
        self.session_maker = session_maker
        super().__init__(model, session=session_maker(), **kwargs)

    def get_query(self):
        # Use a scoped session for proper session management within the request context
        db = self.session_maker()
        if not self.model:
            raise ValueError("Model is not set correctly in NewsCategoryView.")
        try:
            query = db.query(self.model)
            if query is None:
                raise ValueError("Query returned None, model might not be set correctly.")
            return query
        finally:
            db.close()

    def get_count_query(self):
        db = self.session_maker()
        try:
            query = db.query(func.count('*')).select_from(self.model)
            if query is None:
                raise ValueError("Query returned None, model might not be set correctly.")
            return query
        finally:
            db.close()

    column_list = ('id', 'category_name')
    column_default_sort = ('id')
    column_searchable_list = ('category_name',)
    column_filters = ('category_name',)

    form_excluded_columns = ('sources',)

    form_args = {
        'category_name':{
            'label':'Category Name'
        }
    }


class SourceAdmin(SecureModelView):
    def __init__(self, model, session_maker, **kwargs):
        self.session_maker = session_maker
        super().__init__(model, session=session_maker(), **kwargs)

    def get_query(self):
        # Use a scoped session for proper session management within the request context
        db = self.session_maker()
        if not self.model:
            raise ValueError("Model is not set correctly in NewsCategoryView.")
        try:
            query = db.query(self.model)
            if query is None:
                raise ValueError("Query returned None, model might not be set correctly.")
            return query
        finally:
            db.close()

    def get_count_query(self):
        db = self.session_maker()
        try:
            query = db.query(func.count('*')).select_from(self.model)
            if query is None:
                raise ValueError("Query returned None, model might not be set correctly.")
            return query
        finally:
            db.close()
    
    column_list = ('id', 'name', 'logo_preview','url','news_category', 'type', 'is_active', 'ttl', 'created_at', 'updated_at')

    form_create_rules = (
        'name', 'url', 'news_category', 'type', 'is_active', 'ttl', 'logo_url', 'logo_upload')
    
    # form_edit_rules = form_create_rules

    form_excluded_columns = ('logo','articles', 'created_at', 'updated_at')
    
    form_extra_fields = {
        'logo_url': StringField('Logo URL'),
        'logo_upload': FileField('Upload logo')
        # 'logo_upload': FileUploadField('Upload Logo', allowed_extensions=config.ALLOWED_IMAGE_EXTENSION)
    }
    

    column_labels = {
        'logo_preview': 'logo',
    }

    column_exclude_list = ['logo']

    # Format the preview content with a link to view full
    def _logo_preview(view, context, model, name):
        preview = (model.logo) if model.logo else ''
        return Markup(f"<img src='{config.OWN_URL+preview}' style='width:50px;height:50px;'>")

    column_formatters = {
        'logo_preview': _logo_preview,
    }  


    def on_model_change(self, form, model, is_created):
        if not form.name.data or form.name.data == "":
            raise ValueError("Name cannot be empty")
        if not form.url.data or form.url.data == "":
            raise ValueError("URL cannot be empty")
        if form.news_category is None:
            raise ValueError("News Category cannot be empty") 
        if form.type is None:
            raise ValueError("Type cannot be empty")               
        if form.is_active is None:
            raise ValueError("Is active cannot be empty")        

        if is_created:
            if not form.logo_upload.data and not form.logo_url.data:
                model.logo = config.DEFAULT_SOURCE_IMAGE_LOGO
                # raise ValueError("Please provide either a Logo URL or upload a Logo image")
            
            if form.logo_upload.data and form.logo_url.data:
                raise ValueError("Cannot provide both Logo URL and Logo image")
        else:
            if not form.logo_upload.data and not form.logo_url.data and not model.logo:
                raise ValueError("Please provide either a Logo URL or upload a Logo image")

        if form.logo_upload.data:
            if not is_created and model.logo and model.logo != config.SOURCE_IMAGE_UPLOAD_PATH:
                remove_image(model.logo, os.getcwd())
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}_{form.logo_upload.data.filename}")
            with open(temp_file_path, "wb") as f:
                f.write(form.logo_upload.data.read())
            temp_logo = image_upload(temp_file_path, config.SOURCE_IMAGE_UPLOAD_PATH, os.getcwd())
            model.logo = temp_logo
            # if config.REMOTE_HOST:
            #     local_file = os.path.join(os.path.abspath(__file__), '..', '..', temp_logo)
            #     upload_image_to_server(local_file, config.REMOTE_IMAGE_UPLOAD, config.UPLOAD_MEDIA_SECRET_KEY)
        elif form.logo_url.data:
            if not is_created and model.logo and model.logo != config.SOURCE_IMAGE_UPLOAD_PATH:
                remove_image(model.logo, os.getcwd())
            model.logo = image_upload(form.logo_url.data, config.SOURCE_IMAGE_UPLOAD_PATH, os.getcwd())
            
        
        model.name = form.name.data
        model.url = form.url.data
        model.news_category = form.news_category.data
        model.type = form.type.data
        model.is_active = form.is_active.data

        return True
    
    def on_model_delete(self, model):
        if model.logo and model.logo != config.DEFAULT_SOURCE_IMAGE_LOGO:
            print("model.logo != config.DEFAULT_SOURCE_IMAGE_LOGO", model.logo != config.DEFAULT_SOURCE_IMAGE_LOGO)
            remove_image(model.logo, os.getcwd())
        return super().on_model_delete(model)



class FlowerLink(MenuLink):
    def is_accessible(self):
        return 'admin' in session

@app.route('/admin/refresh-data')
@login_required
def refresh_data():
    # global db
    # try:
    #     db.close()
    #     db = SessionLocal()
    #     flash("DONE REFRESHING")
    # except Exception as e:
    #     flash(f"UNABLE TO REFRESH {e}")
    return redirect(request.referrer or url_for('admin.index'))

# Register the custom views with Flask-Admin
admin_panel.add_view(ArticleView(Article, SessionLocal, endpoint="admin_articles"))
admin_panel.add_view(AdminView(ad, SessionLocal, endpoint="admin_admins"))
admin_panel.add_view(UserView(User, SessionLocal, endpoint="admin_users"))
admin_panel.add_view(SummaryView(Summary, SessionLocal, endpoint="admin_summary"))
admin_panel.add_view(NewsCategoryView(NewsCategory, SessionLocal, endpoint="admin_newscategory"))
admin_panel.add_view(SourceAdmin(Source, SessionLocal, endpoint="admin_sourceadmin"))
admin_panel.add_links(MenuLink(name='Refresh', category='', url='/admin/refresh-data'))
admin_panel.add_link(FlowerLink(name='Celery Flower', category='', url='http://localhost:5555'))
admin_panel.add_links(MenuLink(name='Logout', category='', url='/logout'))
