from flask import Blueprint

__author__ = "TuDi"
__date__ = "2018/3/29 下午11:44"

admin = Blueprint("admin", __name__)

import app.admin.views