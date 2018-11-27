from flask import Flask

from app.admin import admin
from app.home import home

__author__ = "TuDi"
__date__ = "2018/3/29 下午11:43"

app = Flask(__name__)
app.debug = True

app.register_blueprint(home)
app.register_blueprint(admin, url_prefix="/admin")