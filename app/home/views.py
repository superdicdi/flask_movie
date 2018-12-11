import os
import uuid
from datetime import datetime
from functools import wraps

from werkzeug.utils import secure_filename

from app import db, app
from app.home import home
from flask import render_template, redirect, url_for, flash, request, session

from app.home.forms import RegisterForm, LoginForm, UserDetailForm, PwdForm
from app.models import User, UserLog
from werkzeug.security import generate_password_hash

__author__ = "TuDi"
__date__ = "2018/3/29 下午11:44"


def change_filename(file_name):
    info = os.path.splitext(file_name)
    return datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4().hex) + info[-1]


# 登录装饰器
def user_login(f):
    @wraps(f)
    def login_req(*args, **kwargs):
        if "user" not in session or session["user"] is None:
            return redirect(url_for("home.login", next=request.url))
        return f(*args, **kwargs)

    return login_req


@home.route("/")
def index():
    return render_template("home/index.html")


@home.route("/animation/")
def animation():
    return render_template("home/animation.html")


@home.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        data = form.data
        user = User.query.filter_by(name=data["name"].strip()).first()
        if not user:
            flash("用户未注册", "err")
            return redirect(url_for("home.login"))
        if not user.check_pwd(data["pwd"]):
            flash("密码错误", "err")
            return redirect(url_for("home.login"))
        session["user"] = user.name
        session["user_id"] = user.id
        userlog = UserLog(
            user_id=user.id,
            ip=request.remote_addr
        )
        db.session.add(userlog)
        db.session.commit()
        return redirect(request.args.get("next") or url_for("home.index"))
    return render_template("home/login.html", form=form)


@home.route("/logout/")
def logout():
    session.pop("user", None)
    session.pop("user_id", None)
    return redirect(url_for("home.login"))


@home.route("/register/", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        data = form.data
        user = User(
            name=data["name"],
            pwd=generate_password_hash(data["pwd"]),
            email=data["email"],
            phone=data["phone"],
            uuid=uuid.uuid4().hex
        )
        db.session.add(user)
        db.session.commit()
        flash("注册成功，请登录", "ok")
        return redirect(url_for("home.login"))
    return render_template("home/register.html", form=form)


@home.route("/user/", methods=["GET", "POST"])
@user_login
def user():
    form = UserDetailForm()
    form.face.validators = []
    user = User.query.get_or_404(session["user_id"])
    if request.method == "GET":
        form.name.data = user.name
        form.email.data = user.email
        form.phone.data = user.phone
        form.info.data = user.info
    if form.validate_on_submit():
        data = form.data
        name = User.query.filter_by(name=data["name"]).count()
        email = User.query.filter_by(email=data["email"]).count()
        phone = User.query.filter_by(phone=data["phone"]).count()
        if user.name != data["name"].strip() and name:
            flash("昵称已经存在", "err")
            return redirect(url_for("home.user"))

        if user.email != data["email"].strip() and email:
            flash("邮箱已经注册", "err")
            return redirect(url_for("home.user"))

        if user.phone != data["phone"].strip() and phone:
            flash("手机号已经注册", "err")
            return redirect(url_for("home.user"))

        if not os.path.exists(app.config["UP_DIR"] + "users/"):
            os.makedirs(app.config["UP_DIR"] + "users/")
        if hasattr(form.face.data, "filename"):
            file_name = secure_filename(form.face.data.filename)
            user.face = change_filename(file_name)
            form.face.data.save(app.config["UP_DIR"] + "users/" + user.face)
        user.name = data["name"]
        user.email = data["email"]
        user.phone = data["phone"]
        user.info = data["info"]
        db.session.add(user)
        db.session.commit()
        flash("个人信息修改成功", "ok")
        return redirect(url_for("home.user"))
    return render_template("home/user.html", form=form, user=user)


@home.route("/pwd/", methods=["GET", "POST"])
@user_login
def pwd():
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        admin = User.query.filter_by(name=session["user"]).first()
        admin.pwd = generate_password_hash(data["new_pwd"])
        db.session.add(admin)
        db.session.commit()
        flash("修改密码成功, 请重新登录", "ok")
        return redirect(url_for("home.logout"))
    return render_template("home/pwd.html", form=form)


@home.route("/comments/")
@user_login
def comments():
    return render_template("home/comments.html")


@home.route("/loginlog/<int:page>", methods=["GET"])
@user_login
def loginlog(page=1):
    page_data = UserLog.query.join(
        User
    ).filter(
        User.id == UserLog.user_id
    ).order_by(
        UserLog.add_time.desc()
    ).paginate(page=page, per_page=4)
    return render_template("home/loginlog.html", page_data=page_data)


@home.route("/moviecol/")
@user_login
def moviecol():
    return render_template("home/moviecol.html")


@home.route("/search/")
def search():
    return render_template("home/search.html")


@home.route("/play/")
def play():
    return render_template("home/play.html")
