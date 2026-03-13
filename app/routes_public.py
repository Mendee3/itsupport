from flask import Blueprint, render_template, request, jsonify
from datetime import datetime, date
from .models import Assignment, Engineer

public_bp = Blueprint("public", __name__)

@public_bp.get("/")
def home():
    return render_template("public.html")

@public_bp.get("/api/public/assignments")
def public_assignments():
    date_str = request.args.get("date")
    start = request.args.get("start")
    end = request.args.get("end")

    q = (
        Assignment.query
        .join(Engineer)
        .filter(Engineer.active == True)
    )

    # 🔹 Case 1: exact day (Today widget)
    if date_str:
        try:
            day = date.fromisoformat(date_str)
        except ValueError:
            return jsonify([])

        q = q.filter(Assignment.date == day)

    # 🔹 Case 2: range (FullCalendar)
    elif start and end:
        start_dt = datetime.fromisoformat(start.replace("Z","")).date()
        end_dt = datetime.fromisoformat(end.replace("Z","")).date()

        q = q.filter(
            Assignment.date >= start_dt,
            Assignment.date < end_dt
        )

    else:
        return jsonify([])

    rows = q.all()

    events = []
    for a in rows:
        e = a.engineer
        events.append({
            "title": e.first_name,
            "start": a.date.isoformat(),
            "allDay": True,
            "extendedProps": {
                "first_name": e.first_name,
                "phone": e.phone,
                "email": e.email
            }
        })

    return jsonify(events)
