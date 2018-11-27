from app.admin import admin

__author__ = "TuDi"
__date__ = "2018/3/29 下午11:44"


@admin.route("/aa")
def index():
    return "<h1 style='color:red'>I like it~</h1>"