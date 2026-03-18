from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_user, login_required, logout_user
from datetime import date, timedelta
from .models import Engineer, Assignment, User
from . import db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.get("/login")
def login():
    return render_template("admin_login.html")

@admin_bp.post("/login")
def login_post():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    user = User.query.filter_by(username=username, active=True).first()
    if not user or not user.check_password(password):
        return render_template("admin_login.html", error="Invalid credentials")

    login_user(user)

    next_url = request.args.get("next")
    if next_url:
        return redirect(next_url)

    return redirect(url_for("admin.dashboard"))

@admin_bp.post("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("admin.login"))

@admin_bp.get("")
@login_required
def dashboard():
    return render_template("admin.html")

@admin_bp.get("/api/engineers")
@login_required
def api_engineers():
    engineers = Engineer.query.filter_by(active=True).order_by(Engineer.first_name).all()
    return jsonify([
        {
            "id": e.id,
            "first_name": e.first_name,
            "position": e.position or "",
            "phone": e.phone,
            "email": e.email,
            "shift_start": e.shift_start or "",
            "shift_end": e.shift_end or "",
            "responsibilities": e.responsibilities or "",
        }
        for e in engineers
    ])

@admin_bp.post("/api/engineers")
@login_required
def api_add_engineer():
    data = request.json
    shift_start = (data.get("shift_start") or "").strip() or "19:00"
    shift_end = (data.get("shift_end") or "").strip() or "07:00"

    e = Engineer(
        first_name=data["first_name"].strip(),
        position=(data.get("position") or "").strip() or None,
        phone=data["phone"].strip(),
        email=data["email"].strip(),
        shift_start=shift_start,
        shift_end=shift_end,
        responsibilities=(data.get("responsibilities") or "").strip() or None,
        active=True
    )
    db.session.add(e)
    db.session.commit()
    return jsonify({"ok": True, "id": e.id})

@admin_bp.post("/api/assignments/bulk_add")
@login_required
def bulk_add():
    data = request.json
    dates = data.get("dates", [])
    engineer_ids = data.get("engineer_ids", [])

    created = 0
    for d in dates:
        day = date.fromisoformat(d)
        for eid in engineer_ids:
            exists = Assignment.query.filter_by(date=day, engineer_id=eid).first()
            if exists:
                continue
            db.session.add(Assignment(date=day, engineer_id=eid))
            created += 1

    db.session.commit()
    return jsonify({"ok": True, "created": created})

@admin_bp.post("/api/assignments/bulk_remove")
@login_required
def bulk_remove():
    data = request.json
    dates = data.get("dates", [])
    engineer_ids = data.get("engineer_ids", [])

    removed = 0
    for d in dates:
        day = date.fromisoformat(d)
        q = Assignment.query.filter(Assignment.date == day)
        if engineer_ids:
            q = q.filter(Assignment.engineer_id.in_(engineer_ids))
        removed += q.delete(synchronize_session=False)

    db.session.commit()
    return jsonify({"ok": True, "removed": removed})

@admin_bp.get("/api/stats/last6months")
@login_required
def stats_6m():
    today = date.today()
    start = today - timedelta(days=183)

    rows = (
        db.session.query(Engineer.id, Engineer.first_name, db.func.count(Assignment.id))
        .join(Assignment, Assignment.engineer_id == Engineer.id)
        .filter(
            Assignment.date >= start,
            Assignment.date <= today,
            Engineer.active == True
        )
        .group_by(Engineer.id, Engineer.first_name)
        .all()
    )

    return jsonify([
        {"engineer_id": r[0], "first_name": r[1], "days": int(r[2])}
        for r in rows
    ])
@admin_bp.put("/api/engineers/<int:engineer_id>")
@login_required
def api_update_engineer(engineer_id):
    data = request.json

    e = Engineer.query.get_or_404(engineer_id)

    if "first_name" in data:
        e.first_name = data["first_name"].strip()
    if "phone" in data:
        e.phone = data["phone"].strip()
    if "email" in data:
        e.email = data["email"].strip()
    if "position" in data:
        e.position = data["position"].strip() or None
    if "shift_start" in data:
        e.shift_start = data["shift_start"].strip() or "19:00"
    if "shift_end" in data:
        e.shift_end = data["shift_end"].strip() or "07:00"
    if "responsibilities" in data:
        e.responsibilities = data["responsibilities"].strip() or None

    db.session.commit()
    return jsonify({"ok": True})
@admin_bp.delete("/api/engineers/<int:engineer_id>")
@login_required
def api_delete_engineer(engineer_id):
    e = Engineer.query.get_or_404(engineer_id)

    # soft delete
    e.active = False
    db.session.commit()

    return jsonify({"ok": True})
