from flask_sqlalchemy import SQLAlchemy
from app.models.timestamp import TimeStamped

db = SQLAlchemy()

class ScrapersRunningStatus(TimeStamped, db.Model):
    __tablename__ = 'flaskscrapper_scrapersrunningstatus'
    id = db.Column(db.Integer, primary_key=True)
    job_source = db.Column(db.String(250), nullable=True)
    running = db.Column(db.Boolean, default=False)
    loop = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Status {self.job_source} {self.loop}>"