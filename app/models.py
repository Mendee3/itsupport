from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db, login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=True)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pw: str):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw: str) -> bool:
        return check_password_hash(self.password_hash, pw)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Engineer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    position = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(40), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    shift_start = db.Column(db.String(20), nullable=True)
    shift_end = db.Column(db.String(20), nullable=True)
    responsibilities = db.Column(db.String(255), nullable=True)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    engineer_id = db.Column(db.Integer, db.ForeignKey("engineer.id"), nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    engineer = db.relationship("Engineer", backref="assignments")

    __table_args__ = (
        db.UniqueConstraint("date", "engineer_id", name="uq_assignment_date_engineer"),
    )
