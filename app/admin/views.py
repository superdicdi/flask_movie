import os
import uuid
from functools import wraps

from datetime import datetime

from werkzeug.utils import secure_filename

from app import db, app
from app.admin import admin
from flask import render_template, redirect, url_for, flash, session, request

from app.admin.forms import LoginForm, Tagform, Movieform, PreviewForm, PwdForm
from app.models import Admin, Tag, Movie, Preview, User, Comment, MovieCol, OpLog, AdminLog, UserLog

__author__ = "TuDi"
__date__ = "2018/3/29 下午11:44"

# 上下文处理器将变量转换为全局的变量
@admin.context_processor
def tpl_extra():
    data = dict(
        online_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    return data


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
            flash("密码错误！", "err")
            return redirect(url_for("admin.login"))
        session["admin"] = data["account"]
        session["admin_id"] = admin.id

        adminlog = AdminLog(
            admin_id=session["admin_id"],
            ip=request.remote_addr
        )
        db.session.add(adminlog)
        db.session.commit()
        return redirect(request.args.get("next") or url_for("admin.index"))
    return render_template("admin/login.html", form=form)


@admin.route("/logout")
def logout():
    session.pop("admin", None)
    session.pop("admin_id", None)
    return redirect(url_for("admin.login"))


@admin.route("/pwd/", methods=["GET", "POST"])
@user_login
def pwd():
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=session["admin"]).first()
        from werkzeug.security import generate_password_hash
        admin.pwd = generate_password_hash(data["new_pwd"])
        db.session.add(admin)
        db.session.commit()
        flash("修改密码成功, 请重新登录", "ok")
        return redirect(url_for("admin.logout"))
    return render_template("admin/pwd.html", form=form)


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

        oplog = OpLog(
            admin_id=session["admin_id"],
            ip=request.remote_addr,
            reason="添加了一条标签《{0}》".format(data["name"])
        )
        db.session.add(oplog)
        db.session.commit()
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


    oplog = OpLog(
        admin_id=session["admin_id"],
        ip=request.remote_addr,
        reason="删除了标签《{0}》".format(tag.name)
    )
    db.session.delete(tag)
    db.session.commit()
    db.session.add(oplog)
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
        start_value = tag.name
        tag.name = data["name"]
        db.session.add(tag)
        db.session.commit()
        flash("修改标签成功", "ok")

        oplog = OpLog(
            admin_id=session["admin_id"],
            ip=request.remote_addr,
            reason="将标签《{0}》修改为《{1}》".format(start_value, tag.name)
        )
        db.session.add(oplog)
        db.session.commit()

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


@admin.route("/preview/add/", methods=["GET", "POST"])
@user_login
def preview_add():
    form = PreviewForm()
    if form.validate_on_submit():
        data = form.data
        if not os.path.exists(app.config["UP_DIR"]):
            os.makedirs(app.config["UP_DIR"])

        pre_logo = secure_filename(form.logo.data.filename)
        logo = change_filename(pre_logo)
        form.logo.data.save(app.config["UP_DIR"] + logo)

        pre = Preview(
            title=data["title"],
            logo=logo
        )
        db.session.add(pre)
        db.session.commit()
        flash("添加成功", "ok")
    return render_template("admin/preview_add.html", form=form)


@admin.route("/preview/list/<int:page>/", methods=["GET"])
@user_login
def preview_list(page=1):
    page_data = Preview.query.order_by(
        Preview.add_time.desc()
    ).paginate(page=page, per_page=1)
    return render_template("admin/preview_list.html", page_data=page_data)


@admin.route("/preview/edit/<int:id>/", methods=["GET", "POST"])
@user_login
def preview_edit(id=1):
    form = PreviewForm()
    form.logo.validators = []
    pre = Preview.query.get_or_404(id)
    if request.method == "GET":
        form.title.data = pre.title

    if form.validate_on_submit():
        data = form.data
        record = Movie.query.filter_by(title=data["title"]).count()
        if pre.title != data["title"].strip() and record:
            flash("名称已经存在", "err")
            return redirect(url_for("admin.preview_edit", id=id))

        if hasattr(form.logo.data, "filename"):
            pre_logo = secure_filename(form.logo.data.filename)
            pre.logo = change_filename(pre_logo)
            form.logo.data.save(app.config["UP_DIR"] + pre.logo)

        pre.title = data["title"]
        db.session.add(pre)
        db.session.commit()
        flash("修改成功", "ok")
    return render_template("admin/preview_edit.html", form=form, preview=pre)


@admin.route("/preview/del/<int:id>/", methods=["GET"])
@user_login
def preview_del(id=1):
    pre = Preview.query.filter_by(id=id).first_or_404()
    db.session.delete(pre)
    db.session.commit()
    return redirect(url_for("admin.preview_list", page=1))


@admin.route("/user/list/<int:page>/", methods=["GET"])
@user_login
def user_list(page=1):
    page_data = User.query.order_by(
        User.add_time.desc()
    ).paginate(page=page, per_page=2)
    return render_template("admin/user_list.html", page_data=page_data)


@admin.route("/user/view/<int:id>/")
@user_login
def user_view(id=1):
    user = User.query.get_or_404(id)
    return render_template("admin/user_view.html", user=user)


@admin.route("/user/del/<int:id>/")
@user_login
def user_del(id=1):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash("删除成功", "ok")
    return redirect(url_for("admin.user_list", page=1))


@admin.route("/comment/list/<int:page>/", methods=["GET"])
@user_login
def comment_list(page=1):
    page_data = Comment.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == Comment.movie_id,
        User.id == Comment.user_id
    ).order_by(
        Comment.add_time.desc()
    ).paginate(page=page, per_page=2)
    return render_template("admin/comment_list.html", page_data=page_data)


@admin.route("/comment/del/<int:id>/")
@user_login
def comment_del(id=1):
    comment = Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    flash("删除成功", "ok")
    return redirect(url_for("admin.comment_list", page=1))


@admin.route("/moviecol/list/<int:page>/", methods=["GET"])
@user_login
def moviecol_list(page=1):
    page_data = MovieCol.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == MovieCol.movie_id,
        User.id == MovieCol.user_id
    ).order_by(
        MovieCol.add_time.desc()
    ).paginate(page=page, per_page=2)
    return render_template("admin/moviecol_list.html", page_data=page_data)


@admin.route("/moviecol/del/<int:id>/", methods=["GET"])
@user_login
def moviecol_del(id=1):
    moviecol = MovieCol.query.get_or_404(id)
    db.session.delete(moviecol)
    db.session.commit()
    flash("删除成功", "ok")
    return redirect(url_for("admin.moviecol_list", page=1))


@admin.route("/oplog/list/<int:page>/", methods=["GET"])
@user_login
def oplog_list(page=1):
    page_data = OpLog.query.join(
        Admin
    ).filter(
        Admin.id == OpLog.admin_id
    ).order_by(
        OpLog.add_time.desc()
    ).paginate(page=page, per_page=5)
    return render_template("admin/oplog_list.html", page_data=page_data)


@admin.route("/adminloginlog/list/<int:page>/", methods=["GET"])
@user_login
def adminloginlog_list(page=1):
    page_data = AdminLog.query.join(
        Admin
    ).filter(
        Admin.id == AdminLog.admin_id
    ).order_by(
        AdminLog.add_time.desc()
    ).paginate(page=page, per_page=5)
    return render_template("admin/adminloginlog_list.html", page_data=page_data)


@admin.route("/userloginlog/list/<int:page>/", methods=["GET"])
@user_login
def userloginlog_list(page=1):
    page_data = UserLog.query.join(
        User
    ).filter(
        User.id == UserLog.user_id
    ).order_by(
        UserLog.add_time.desc()
    ).paginate(page=page, per_page=5)
    return render_template("admin/userloginlog_list.html", page_data=page_data)


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
