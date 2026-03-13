from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    u = User.query.filter_by(username="admin").first()
    if not u:
        u = User(username="admin", active=True)
        u.set_password("ChangeMe123!")
        db.session.add(u)
    else:
        u.set_password("ChangeMe123!")
        u.active = True
    db.session.commit()
    print("Flask admin user ready")
