import os
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

# --- 1. CONFIGURATION ---
# Base directory for the database file
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
# Configure the SQLite database file location
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'timetable.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- 2. DATABASE MODEL ---
# Define the structure of the 'schedule' table
class Schedule(db.Model):
    # This creates the table name 'schedule'
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Date, nullable=False, default=date.today())
    time = db.Column(db.String(50), nullable=False) # e.g., "10:00 - 11:30"
    activity = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='No description provided')
    
    def __repr__(self):
        return f'<Schedule {self.day} {self.activity}>'

# --- 3. ROUTES (Web Pages) ---

# Initialize the database (must be run once)
@app.before_request
def create_tables():
    # Only creates tables if they don't exist
    db.create_all()

# Home Page: Display the Timetable
@app.route('/')
def index():
    # Query all schedule entries, ordered by day and then time
    all_schedules = Schedule.query.order_by(Schedule.day, Schedule.time).all()
    
    # Group schedules by day for easier display in the HTML template
    schedules_by_day = {}
    for entry in all_schedules:
        # Convert date object to a formatted string (e.g., 'Monday, Dec 15')
        day_str = entry.day.strftime("%A, %b %d, %Y")
        if day_str not in schedules_by_day:
            schedules_by_day[day_str] = []
        schedules_by_day[day_str].append(entry)
        
    # Pass the grouped data to the template
    return render_template('index.html', schedules=schedules_by_day)

# Admin/Single User Page: Add New Entry
@app.route('/add', methods=['GET', 'POST'])
def add_schedule():
    if request.method == 'POST':
        # Get data from the form
        day_str = request.form['day']
        time = request.form['time']
        activity = request.form['activity']
        description = request.form['description']
        
        # Convert the string date to a date object
        try:
            day_obj = datetime.strptime(day_str, '%Y-%m-%d').date()
        except ValueError:
            # Handle invalid date format
            # In a real app, you would flash an error message
            return redirect(url_for('add_schedule'))

        # Create a new Schedule object
        new_entry = Schedule(
            day=day_obj, 
            time=time, 
            activity=activity, 
            description=description
        )
        
        # Add to the database session and commit
        db.session.add(new_entry)
        db.session.commit()
        
        # Redirect to the home page
        return redirect(url_for('index'))
    
    # For GET request, just show the form
    return render_template('add.html')

if __name__ == '__main__':
    # Creates the database file (timetable.db) if it doesn't exist
    with app.app_context():
        db.create_all()
    app.run(debug=True)
