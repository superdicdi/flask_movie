# coding:utf8
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, TextAreaField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, ValidationError, EqualTo
from app.models import Admin, Tag, Auth, Role

tags = Tag.query.all()
auth_list = Auth.query.all()
role_list = Role.query.all()


class LoginForm(FlaskForm):
    account = StringField(
        label="账号",
        validators=[
            DataRequired("请输入账号")
        ],
        description="账号",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入账号",
            "required": False,
        }
    )
    pwd = PasswordField(
        label="密码",
        validators=[
            DataRequired("请输入密码")
        ],
        description=u"密码",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入密码",
            "required": False,
        }
    )
    submit = SubmitField(
        '登录',
        render_kw={
            "class": "btn btn-primary btn-block btn-flat",
        }
    )

    def validate_account(self, field):
        account = field.data
        admin = Admin.query.filter_by(name=account).count()
        if admin == 0:
            raise ValidationError("账号不存在")


class Tagform(FlaskForm):
    name = StringField(
        label="名称",
        validators=[
            DataRequired("请输入标签")
        ],
        description="标签",
        render_kw={
            "class": "form-control",
            "id": "input_name",
            "placeholder": "请输入标签名称！",
            "required": False,
        }
    )
    submit = SubmitField(
        '编辑',
        render_kw={
            "class": "btn btn-primary",
        }
    )


class TagEditform(FlaskForm):
    name = StringField(
        label="名称",
        validators=[
            DataRequired("请输入标签")
        ],
        description="标签",
        render_kw={
            "class": "form-control", "id": "input_name", "placeholder": "请输入标签名称！"}
    )
    submit = SubmitField(
        '编辑',
        render_kw={
            "class": "btn btn-primary",
        }
    )


class Movieform(FlaskForm):
    title = StringField(
        label="片名",
        validators=[
            DataRequired("请输入片名")
        ],
        description="片名",
        render_kw={
            "class": "form-control", "id": "input_title", "placeholder": "请输入片名！",
            "required": False}
    )
    url = FileField(
        label="文件",
        validators=[
            DataRequired("请上传文件")
        ],
        description="文件",
        render_kw={
            "required": False
        }
    )
    info = TextAreaField(
        label="简介",
        validators=[
            DataRequired("请输入简介")
        ],
        description="简介",
        render_kw={
            "class": "form-control", "rows": "10",
            "required": False}
    )
    logo = FileField(
        label="封面",
        validators=[
            DataRequired("请上传封面")
        ],
        description="封面",
        render_kw={
            "required": False
        }
    )
    star = SelectField(
        label="星级",
        validators=[
            DataRequired("请选择星级")
        ],
        coerce=int,
        choices=[(1, "1星"), (2, "2星"), (3, "3星"), (4, "4星"), (5, "5星")],
        description="星级",
        render_kw={
            "class": "form-control",
            "required": False
        }
    )
    tag_id = SelectField(
        label="标签",
        validators=[
            DataRequired("请选择标签")
        ],
        coerce=int,
        choices=[(v.id, v.name) for v in tags],
        description="标签",
        render_kw={
            "class": "form-control",
            "required": False
        }
    )
    area = StringField(
        label="地区",
        validators=[
            DataRequired("请输入地区")
        ],
        description="地区",
        render_kw={
            "class": "form-control", "placeholder": "请输入地区！",
            "required": False}
    )
    length = StringField(
        label="片长",
        validators=[
            DataRequired("请输入片长")
        ],
        description="片长",
        render_kw={
            "class": "form-control", "placeholder": "请输入片长！",
            "required": False}
    )
    release_time = StringField(
        label="上映时间",
        validators=[
            DataRequired("请选择上映时间")
        ],
        description="上映时间",
        render_kw={
            "class": "form-control", "id": "input_release_time", "placeholder": "请选择上映时间！",
            "required": False}
    )
    submit = SubmitField(
        '添加',
        render_kw={
            "class": "btn btn-primary",
        }
    )


class PreviewForm(FlaskForm):
    title = StringField(
        label="预告标题",
        validators=[
            DataRequired("请输入预告标题")
        ],
        description="预告标题",
        render_kw={
            "class": "form-control", "id": "input_title", "placeholder": "请输入片名！", "required": False
        }
    )
    logo = FileField(
        label="预告封面",
        validators=[
            DataRequired("请上传预告封面")
        ],
        description="预告封面",
        render_kw={
            "required": False
        }
    )
    submit = SubmitField(
        '添加',
        render_kw={
            "class": "btn btn-primary",
        }
    )


class PwdForm(FlaskForm):
    old_pwd = PasswordField(
        label=u"旧密码",
        validators=[
            DataRequired(u"请输入旧密码")
        ],
        description=u"旧密码",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入旧密码",
            "required": False
        }
    )
    new_pwd = PasswordField(
        label=u"新密码",
        validators=[
            DataRequired(u"请输入新密码")
        ],
        description=u"新密码",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入新密码",
            "required": False
        }
    )
    submit = SubmitField(
        '确认',
        render_kw={
            "class": "btn btn-primary btn-block btn-flat",
        }

    )

    def validate_old_pwd(self, field):
        from flask import session
        pwd = field.data
        name = session["admin"]
        admin = Admin.query.filter_by(
            name=name
        ).first()  # 这里是根据session的管理员用户名查找管理员，所以注册的时候不能重名
        if not admin.check_pwd(pwd):
            raise ValidationError("旧密码错误")


class Authform(FlaskForm):
    name = StringField(
        label="权限名称",
        validators=[
            DataRequired("请输入权限")
        ],
        description="权限",
        render_kw={
            "class": "form-control", "placeholder": "请输入权限名称！", "required": False}
    )
    url = StringField(
        label="权限地址",
        validators=[
            DataRequired("请输入权限地址")
        ],
        description="权限地址",
        render_kw={
            "class": "form-control", "placeholder": "请输入权限地址！", "required": False}
    )
    submit = SubmitField(
        '编辑',
        render_kw={
            "class": "btn btn-primary",
        }
    )


class Roleform(FlaskForm):
    name = StringField(
        label="角色名称",
        validators=[
            DataRequired("请输入角色名称")
        ],
        description="角色名称",
        render_kw={
            "class": "form-control", "placeholder": "请输入角色名称！", "required": False}
    )
    auths = SelectMultipleField(
        label="权限列表",
        validators=[
            DataRequired("请选择权限")
        ],
        coerce=int,
        choices=[(v.id, v.name) for v in auth_list],
        description="权限列表",
        render_kw={
            "class": "form-control", "required": False
        }
    )
    submit = SubmitField(
        '编辑',
        render_kw={
            "class": "btn btn-primary",
        }
    )


class AdminForm(FlaskForm):
    name = StringField(
        label=u"管理员名称",
        validators=[
            DataRequired(u"请输入管理员名称")
        ],
        description=u"管理员名称",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入管理员名称",
            "required": False
        }
    )
    pwd = PasswordField(
        label=u"管理员密码",
        validators=[
            DataRequired(u"请输入管理员密码")
        ],
        description=u"管理员密码",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入管理员密码",
            "required": False
        }
    )
    repwd = PasswordField(
        label=u"管理员重复密码",
        validators=[
            DataRequired(u"请输入管理员重复密码"),
            EqualTo('pwd', "两次密码不一致")
        ],
        description=u"管理员重复密码",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入管理员重复密码",
            "required": False
        }
    )
    role_id = SelectField(
        label="所属角色",
        coerce=int,
        choices=[(v.id, v.name) for v in role_list],
        render_kw={
            "class": "form-control",
            "required": False
        }
    )
    submit = SubmitField(
        '编辑',
        render_kw={
            "class": "btn btn-primary",
        }
    )
