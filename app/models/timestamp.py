from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class TimeStamped(db.Model):
    __abstract__ = True
    created_at = db.Column(db.String, server_default=db.func.now())
    updated_at = db.Column(db.String, server_default=db.func.now(), onupdate=db.func.now())