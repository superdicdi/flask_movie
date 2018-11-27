from app.home import home

__author__ = "TuDi"
__date__ = "2018/3/29 下午11:44"


@home.route("/")
def index():
    return "<h1 style='color:blue'>My yaya is so beautlful</h1>"