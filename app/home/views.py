import os
import uuid
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename

from app import db, app, rd
from app.home import home
from flask import render_template, redirect, url_for, flash, request, session, Response

from app.home.forms import RegisterForm, LoginForm, UserDetailForm, PwdForm, CommentForm
from app.models import User, UserLog, Preview, Tag, Movie, Comment, MovieCol
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


@home.route("/<int:page>/", methods=["GET"])
def index(page=1):
    tags = Tag.query.all()
    page_data = Movie.query
    tid = request.args.get("tid", 0)
    if int(tid) != 0:
        page_data = page_data.filter_by(tag_id=int(tid))

    star = request.args.get("star", 0)
    if int(star) != 0:
        page_data = page_data.filter_by(star=int(star))

    time = request.args.get("time", 0)
    if int(time) != 0:
        if int(time) == 1:
            page_data = page_data.order_by(
                Movie.release_time.desc()
            )
        else:
            page_data = page_data.order_by(
                Movie.release_time.asc()
            )

    play_num = request.args.get("pm", 0)
    if int(play_num) != 0:
        if int(play_num) == 1:
            page_data = page_data.order_by(
                Movie.play_num.desc()
            )
        else:
            page_data = page_data.order_by(
                Movie.play_num.asc()
            )

    comm_num = request.args.get("cm", 0)
    if int(comm_num) != 0:
        if int(comm_num) == 1:
            page_data = page_data.order_by(
                Movie.comment_num.desc()
            )
        else:
            page_data = page_data.order_by(
                Movie.comment_num.asc()
            )

    page_data = page_data.paginate(page=page, per_page=8)
    p = dict(
        tid=tid,
        star=star,
        time=time,
        pm=play_num,
        cm=comm_num,

    )
    return render_template("home/index.html", tags=tags, p=p, page_data=page_data)


@home.route("/animation/")
def animation():
    data = Preview.query.all()
    return render_template("home/animation.html", data=data)


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
        return redirect(request.args.get("next") or url_for("home.index", page=1))
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


@home.route("/comments/<int:page>/", methods=["GET"])
@user_login
def comments(page=1):
    page_data = Comment.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == Comment.movie_id,
        User.id == session["user_id"]
    ).order_by(
        Comment.add_time.desc()
    ).paginate(page=page, per_page=2)
    return render_template("home/comments.html", page_data=page_data)


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


@home.route("/moviecol/<int:page>", methods=["GET"])
@user_login
def moviecol(page=1):
    page_data = MovieCol.query.join(
        User
    ).join(
        Movie
    ).filter(
        User.id == session["user_id"],
        Movie.id == MovieCol.movie_id
    ).order_by(
        MovieCol.add_time.desc()
    ).paginate(page=page, per_page=1)
    return render_template("home/moviecol.html", page_data=page_data)


@home.route("/moviecol/add")
@user_login
def moviecol_add():
    uid = request.args.get("uid", "")
    mid = request.args.get("mid", "")
    moviecol = MovieCol.query.filter_by(
        movie_id=int(mid),
        user_id=int(uid)
    ).count()
    if moviecol:
        data = dict(ok=0)
    else:
        moviecol = MovieCol(
            user_id=int(uid),
            movie_id=int(mid)
        )
        db.session.add(moviecol)
        db.session.commit()
        data = dict(ok=1)
    import json
    return json.dumps(data)


@home.route("/search/<int:page>/", methods=["GET"])
def search(page=1):
    key = request.args.get("key", "")
    movie_count = Movie.query.filter(
        Movie.title.ilike("%" + key + "%")
    ).count()

    page_data = Movie.query.filter(
        Movie.title.ilike("%" + key + "%")
    ).paginate(page=page, per_page=3)
    return render_template("home/search.html", page_data=page_data, key=key, movie_count=movie_count)


@home.route("/play/<int:id>", methods=["GET", "POST"])
def play(id=1):
    movie = Movie.query.join(Tag).filter(Tag.id == Movie.tag_id, Movie.id == id).first_or_404()
    form = CommentForm()
    movie.play_num += 1
    if form.validate_on_submit():
        data = form.data
        comment = Comment(
            content=data["content"],
            movie_id=movie.id,
            user_id=session["user_id"]
        )
        db.session.add(comment)
        db.session.commit()
        movie.comment_num += 1
        flash("评论成功", "ok")
    db.session.add(movie)
    db.session.commit()
    page = int(request.args.get("page", 1))
    page_data = Comment.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == movie.id,
        User.id == Comment.user_id
    ).order_by(
        Comment.add_time.desc()
    ).paginate(page=page, per_page=1)

    return render_template("home/play.html", movie=movie, form=form, page_data=page_data)


@home.route("/video/<int:id>", methods=["GET", "POST"])
def video(id=1):
    movie = Movie.query.join(Tag).filter(Tag.id == Movie.tag_id, Movie.id == id).first_or_404()
    form = CommentForm()
    movie.play_num += 1
    if form.validate_on_submit():
        data = form.data
        comment = Comment(
            content=data["content"],
            movie_id=movie.id,
            user_id=session["user_id"]
        )
        db.session.add(comment)
        db.session.commit()
        movie.comment_num += 1
        flash("评论成功", "ok")
    db.session.add(movie)
    db.session.commit()
    page = int(request.args.get("page", 1))
    page_data = Comment.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == movie.id,
        User.id == Comment.user_id
    ).order_by(
        Comment.add_time.desc()
    ).paginate(page=page, per_page=1)

    return render_template("home/video.html", movie=movie, form=form, page_data=page_data)


@home.route("/tm/", methods=["GET", "POST"])
def tm():
    import json
    if request.method == "GET":
        #获取弹幕消息队列
        id = request.args.get('id')
        key = "movie" + str(id)
        if rd.llen(key):
            msgs = rd.lrange(key, 0, 2999)
            res = {
                "code": 1,
                "danmaku": [json.loads(v) for v in msgs]
            }
        else:
            res = {
                "code": 1,
                "danmaku": []
            }
        resp = json.dumps(res)
    if request.method == "POST":
        #添加弹幕
        data = json.loads(request.get_data())
        msg = {
            "__v": 0,
            "author": data["author"],
            "time": data["time"],
            "text": data["text"],
            "color": data["color"],
            "type": data['type'],
            "ip": request.remote_addr,
            "_id": datetime.now().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex,
            "player": [
                data["player"]
            ]
        }
        res = {
            "code": 1,
            "data": msg
        }
        resp = json.dumps(res)
        rd.lpush("movie" + str(data["player"]), json.dumps(msg))
    return Response(resp, mimetype='application/json')