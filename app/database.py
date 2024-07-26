from app.models.timestamp import db
import os

def db_config(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("OCTAGON_LOCAL_DB")
    db.init_app(app)
