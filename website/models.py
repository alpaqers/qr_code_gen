from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class QRCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    size = db.Column(db.Integer, default=10)
    color_fg = db.Column(db.String(7), default="#000000")
    color_bg = db.Column(db.String(7), default="#FFFFFF")
    logo_filename = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
