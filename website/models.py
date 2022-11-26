from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

# User's zone entries
class Zone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    km = db.Column(db.Integer, default=10)
    price = db.Column(db.Float, default=1.35)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    day = db.relationship('Day')

# This table represents user's day of work 
class Day(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date(), default=func.now())
    hours = db.Column(db.Float, default=0.00)
    meal_qty = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'))

# Table with user info
# sundays column to be finished another time
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    hourly_rate = db.Column(db.Float, default=11.07)
    region = db.Column(db.String(150), default='Lorraine')
    sundays = db.Column(db.Integer, default=0)
    meal = db.Column(db.Float, default=1.0)
    zone = db.relationship('Zone')
    day = db.relationship('Day')
