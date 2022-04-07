from flask import Flask, render_template
from flask_login import login_user, login_required, logout_user
from werkzeug.exceptions import abort
from werkzeug.utils import redirect
from data.blogs import Blogs
from data import db_session
from forms.loginform import LoginForm
from forms.user import RegisterForm
from forms.blogform import BlogsForm
from data.users import User
from flask_login import current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@app.route("/")
def index_page():
    return render_template("home.html", current_user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        user = User(name=form.name.data, email=form.email.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/logout')
@login_required
def log_out():
    logout_user()
    return redirect("/")


@app.route('/blogs',  methods=['GET', 'POST'])
@login_required
def add_blog():
    form = BlogsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        blogs = Blogs()
        blogs.title = form.title.data
        blogs.content = form.content.data
        blogs.is_private = form.is_private.data
        current_user.blogs.append(blogs)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('news.html', title='Добавление новости',
                           form=form)


@app.route('/blogs_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def blog_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(Blogs).filter(Blogs.id == id, Blogs.user == current_user).first()
    if news:
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)


