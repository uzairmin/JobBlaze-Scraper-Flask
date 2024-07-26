from flask_sqlalchemy import SQLAlchemy
from app.models.timestamp import TimeStamped

db = SQLAlchemy()

class Accounts(TimeStamped, db.Model):
    __tablename__ = 'scraper_accounts'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(500), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    source = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f"<Accounts {self.email} {self.source}>"
