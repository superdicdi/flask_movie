import os
import uuid
from functools import wraps

from datetime import datetime

from werkzeug.utils import secure_filename

from app import db, app
from app.admin import admin
from flask import render_template, redirect, url_for, flash, session, request

from app.admin.forms import LoginForm, Tagform, Movieform
from app.models import Admin, Tag, Movie

__author__ = "TuDi"
__date__ = "2018/3/29 下午11:44"


def user_login(f):
    @wraps(f)
    def login_req(*args, **kwargs):
        if "admin" not in session or session["admin"] is None:
            return redirect(url_for("admin.login", next=request.url))
        return f(*args, **kwargs)

    return login_req


def change_filename(file_name):
    info = os.path.splitext(file_name)
    return datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4().hex) + info[-1]


@admin.route("/")
@user_login
def index():
    return render_template("admin/index.html")


@admin.route("/login/", methods=["GET", "POST"])
def login():
    print("1" * 30)
    form = LoginForm()
    if form.validate_on_submit():
        print("2" * 30)
        data = form.data
        admin = Admin.query.filter_by(name=data["account"]).first()
        if not admin.check_pwd(data["pwd"]):
            flash("密码错误！")
            return redirect(url_for("admin.login"))
        session["admin"] = data["account"]
        return redirect(request.args.get("next") or url_for("admin.index"))
    return render_template("admin/login.html", form=form)


@admin.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("admin.login"))


@admin.route("/pwd/")
@user_login
def pwd():
    return render_template("admin/pwd.html")


@admin.route("/tag/add/", methods=["GET", "POST"])
@user_login
def tag_add():
    form = Tagform()
    if form.validate_on_submit():
        data = form.data
        tag = Tag.query.filter_by(name=data["name"]).count()
        if tag:
            flash("名称已经存在", "err")
            return redirect(url_for("admin.tag_add"))
        tag = Tag(
            name=data["name"]
        )
        db.session.add(tag)
        db.session.commit()
        flash("添加成功", "ok")
        return redirect(url_for("admin.tag_add"))
    return render_template("admin/tag_add.html", form=form)


@admin.route("/tag/list/<int:page>/", methods=["GET"])
@user_login
def tag_list(page=1):
    page_data = Tag.query.order_by(
        Tag.add_time.desc()
    ).paginate(page=page, per_page=3)
    return render_template("admin/tag_list.html", page_data=page_data)


@admin.route("/tag/del/<int:id>/", methods=["GET"])
@user_login
def tag_del(id=1):
    tag = Tag.query.filter_by(id=id).first_or_404()
    db.session.delete(tag)
    db.session.commit()
    flash("删除标签成功", "ok")
    return redirect(url_for("admin.tag_list", page=1))


@admin.route("/tag/edit/<int:id>/", methods=["GET", "POST"])
@user_login
def tag_edit(id=1):
    form = Tagform()
    tag = Tag.query.get_or_404(id)
    if form.validate_on_submit():
        data = form.data
        record = Tag.query.filter_by(name=data["name"]).count()
        if tag.name != data["name"].strip() and record:
            flash("名称已经存在", "err")
            return redirect(url_for("admin.tag_edit", id=id))
        tag.name = data["name"]
        db.session.add(tag)
        db.session.commit()
        flash("删除标签成功", "ok")
        return redirect(url_for("admin.tag_edit", id=id))
    return render_template("admin/tag_edit.html", form=form, tag=tag)


@admin.route("/movie/add/", methods=["GET", "POST"])
@user_login
def movie_add():
    form = Movieform()

    if form.validate_on_submit():
        data = form.data

        file_url = secure_filename(form.url.data.filename)
        logo_url = secure_filename(form.logo.data.filename)
        url = change_filename(file_url)
        logo = change_filename(logo_url)
        if not os.path.exists(app.config["UP_DIR"]):
            os.makedirs(app.config["UP_DIR"])

        form.url.data.save(app.config["UP_DIR"] + url)
        form.logo.data.save(app.config["UP_DIR"] + logo)

        movie = Movie(
            title=data["title"],
            url=url,
            info=data["info"],
            logo=logo,
            star=int(data["star"]),
            play_num=0,
            comment_num=0,
            tag_id=int(data["tag_id"]),
            area=data["area"],
            release_time=data["release_time"],
            length=data["length"]
        )
        db.session.add(movie)
        db.session.commit()
        flash("电影添加成功", "ok")
        return redirect(url_for("admin.movie_add"))
    return render_template("admin/movie_add.html", form=form)


@admin.route("/movie/list/<int:page>/", methods=["GET"])
@user_login
def movie_list(page=1):
    form = Movieform()
    page_data = Movie.query.order_by(
        Movie.add_time.desc()
    ).paginate(page=page, per_page=1)
    return render_template("admin/movie_list.html", form=form, page_data=page_data)


@admin.route("/movie/edit/<int:id>/", methods=["GET", "POST"])
@user_login
def movie_edit(id=1):
    form = Movieform()
    form.url.validators = []
    form.logo.validators = []
    movie = Movie.query.get_or_404(id)
    if request.method == "GET":
        form.title.data = movie.title
        form.url.data = movie.url  # 为什么无效？
        form.info.data = movie.info

        form.logo.data = movie.logo  # 为什么无效？
        form.star.data = movie.star
        form.tag_id.data = movie.tag_id

        form.area.data = movie.area
        form.release_time.data = movie.release_time
        form.length.data = movie.length

    if form.validate_on_submit():
        data = form.data
        record = Movie.query.filter_by(title=data["title"]).count()
        if movie.title != data["title"].strip() and record:
            flash("名称已经存在", "err")
            return redirect(url_for("admin.movie_edit", id=id))
        if not os.path.exists(app.config["UP_DIR"]):
            os.makedirs(app.config["UP_DIR"])
        if hasattr(form.url.data, "filename"):
            file = secure_filename(form.url.data.filename)
            movie.url = change_filename(file)
            form.url.data.save(app.config["UP_DIR"] + movie.url)

        if hasattr(form.logo.data, "filename"):
            file = secure_filename(form.logo.data.filename)
            movie.logo = change_filename(file)
            form.logo.data.save(app.config["UP_DIR"] + movie.logo)

        movie.title = data["title"]
        movie.info = data["info"]
        movie.star = data["star"]
        movie.tag_id = data["tag_id"]
        movie.area = data["area"]
        movie.release_time = data["release_time"]
        movie.length = data["length"]
        db.session.add(movie)
        db.session.commit()
        flash("电影修改成功", "ok")
        return redirect(url_for("admin.movie_edit", id=id))
    return render_template("admin/movie_edit.html", form=form, movie=movie)


@admin.route("/movie/del/<int:id>/")
@user_login
def movie_del(id=1):
    movie = Movie.query.filter_by(id=id).first_or_404()
    db.session.delete(movie)
    db.session.commit()
    flash("删除成功", "ok")
    return redirect(url_for("admin.movie_list", page=1))


@admin.route("/preview/add/")
@user_login
def preview_add():
    return render_template("admin/preview_add.html")


@admin.route("/preview/list/")
@user_login
def preview_list():
    return render_template("admin/preview_list.html")


@admin.route("/user/list/")
@user_login
def user_list():
    return render_template("admin/user_list.html")


@admin.route("/user/view/")
@user_login
def user_view():
    return render_template("admin/user_view.html")


@admin.route("/comment/list/")
@user_login
def comment_list():
    return render_template("admin/comment_list.html")


@admin.route("/moviecol/list/")
@user_login
def moviecol_list():
    return render_template("admin/moviecol_list.html")


@admin.route("/oplog/list/")
@user_login
def oplog_list():
    return render_template("admin/oplog_list.html")


@admin.route("/adminloginlog/list/")
@user_login
def adminloginlog_list():
    return render_template("admin/adminloginlog_list.html")


@admin.route("/userloginlog/list/")
@user_login
def userloginlog_list():
    return render_template("admin/userloginlog_list.html")


@admin.route("/role/add/")
@user_login
def role_add():
    return render_template("admin/role_add.html")


@admin.route("/role/list/")
@user_login
def role_list():
    return render_template("admin/role_list.html")


@admin.route("/auth/add/")
@user_login
def auth_add():
    return render_template("admin/auth_add.html")


@admin.route("/auth/list/")
@user_login
def auth_list():
    return render_template("admin/auth_list.html")


@admin.route("/admin/add/")
@user_login
def admin_add():
    return render_template("admin/admin_add.html")


@admin.route("/admin/list/")
@user_login
def admin_list():
    return render_template("admin/admin_list.html")
