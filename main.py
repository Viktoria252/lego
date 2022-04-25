import os

from flask import Flask, render_template, send_file, url_for
from flask_login import login_user, login_required, logout_user, LoginManager
from werkzeug.exceptions import abort
from werkzeug.utils import redirect
from data.blogs import Blogs
from data import db_session
from forms.comments import AddCommentForm
from forms.loginform import LoginForm
from forms.user import RegisterForm
from forms.blogform import BlogsForm
from data.users import User
from flask_login import current_user
from requests import request
from data.Comments import Comment

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


def main():
    db_session.global_init("db/blogs.sqlite")
    app.run(debug=True)


@app.route("/")
def index_page():
    blogs = db_session.create_session().query(Blogs).all()
    return render_template("home.html", current_user=current_user, blog=blogs)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.username == form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form,
                               current_user=current_user)
    return render_template('login.html', title='Авторизация', form=form, current_user=current_user)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Пароли не совпадают", current_user=current_user)
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть", current_user=current_user)
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form,
                           current_user=current_user)


@app.route('/logout')
@login_required
def log_out():
    logout_user()
    return redirect("/")


@app.route('/blogs', methods=['GET', 'POST'])
@login_required
def add_blog():
    form = BlogsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        blogs = Blogs()
        blogs.title = form.title.data
        blogs.content = form.content.data

        f = form.video.data
        current_user_dir = f'static/video/{current_user.username}'
        if not os.path.isdir(current_user_dir):  # существует ли папка для файлов юзера
            os.makedirs(current_user_dir)
        full_path = f'{current_user_dir}/{f.filename}'
        f.save(full_path)
        blogs.video = full_path

        img = form.img.data
        current_user_dir_img = f'static/img/{current_user.username}'
        if not os.path.isdir(current_user_dir_img):
            os.makedirs(current_user_dir_img)
        full_path_img = f'{current_user_dir_img}/{img.filename}'
        img.save(full_path_img)
        blogs.img = full_path_img

        # blogs.is_private = form.is_private.data
        # blogs.video = form.video

        current_user.news.append(blogs)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('add_blog.html', title='Create Video', form=form)


@app.route('/<title>')
def video(title):
    blog = db_session.create_session().query(Blogs).filter(Blogs.title == title).first()
    return render_template("blog.html", blog=blog)


@app.route('/blogs_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def blog_delete(id):
    db_sess = db_session.create_session()
    blog = db_sess.query(Blogs).filter(Blogs.id == id, Blogs.user == current_user).first()
    if blog:
        db_sess.delete(blog)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route("/blog/<int:blog_id>/comment", methods=["GET", "POST"])
@login_required
def comment_blog(blog_id):
    blog = Blogs.query.get_or_404(blog_id)
    form = AddCommentForm()
    if request.method == 'POST': # this only gets executed when the form is submitted and not when the page loads
        if form.validate_on_submit():
            session = db_session.create_session()
            comment = Comment(body=form.body.data, blog_id=blog.id)
            session.add(comment)
            session.commit()
            return redirect("/blogs")
    return render_template("comment_blog.html", title="Comment Post", form=form, post_id=blog_id)


if __name__ == "__main__":
    main()

