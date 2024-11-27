from flask import Flask, render_template, request, redirect, url_for, session,jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
from flask_cors import CORS
import requests


import random
import string


app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes
# Placeholder for tracking homepage visits
homepage_visits = []

# Grid dimensions
GRID_ROWS = 10
GRID_COLS = 10

# Setup the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_counseling.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

app.config['SECRET_KEY'] = 'Akingbesote Babajide Created This Site 08134812419'  # Replace with a secure key

IPSTACK_API_KEY = 'b913fda9e7cde1ddf1f9615383cb05d0'


# Model for storing form data
class Registration(db.Model):
    __tablename__ = 'registration'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    service = db.Column(db.String(50), nullable=False)

    # Model for storing feedback
class Feedback(db.Model):
        __tablename__ = 'feedback'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)
        email = db.Column(db.String(100), nullable=False)
        message = db.Column(db.Text, nullable=False)
        submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()  # Create tables if they don't exist yet

def get_random_letter():
    return random.choice(string.ascii_uppercase)

def create_empty_grid():
    # Initialize grid with None to mark empty cells
    return [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

# List of HIV/AIDS-related words
WORDS = ["HIV", "AIDS", "PREVENTION", "TREATMENT", "PREP", "IMMUNITY", "HEALTH", "SUPPORT", "CARE", "TESTING"]

# Function to place a word in the grid in various directions
def place_word(grid, word):
    directions = [(0, 1), (1, 0), (1, 1), (1, -1), (-1, 0), (-1, -1), (0, -1), (-1, 1)]
    random.shuffle(directions)

    for _ in range(100):  # Try multiple times for best placement
        direction = random.choice(directions)
        row = random.randint(0, GRID_ROWS - 1)
        col = random.randint(0, GRID_COLS - 1)

        # Check if word fits in grid without conflict
        can_place = True
        for i in range(len(word)):
            new_row = row + i * direction[0]
            new_col = col + i * direction[1]
            if not (0 <= new_row < GRID_ROWS and 0 <= new_col < GRID_COLS) or (
                grid[new_row][new_col] not in [None, word[i]]
            ):
                can_place = False
                break

        if can_place:
            for i in range(len(word)):
                new_row = row + i * direction[0]
                new_col = col + i * direction[1]
                grid[new_row][new_col] = word[i]
            return True  # Return success after placing the word

    return False  # Return failure if the word couldn't be placed
# Function to generate the puzzle grid with placed words
def generate_puzzle():
    grid = create_empty_grid()
    for word in WORDS:
        place_word(grid, word)
    # Fill remaining empty cells with random letters
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            if grid[r][c] is None:  # Check for uninitialized cells
                grid[r][c] = get_random_letter()
    return grid

# Routes
@app.route('/')
def index():
    # Get visitor's IP address and location
    ip_address = request.remote_addr
    location = get_location(ip_address)

    # Get the current number of visits from cookies
    visit_count = int(request.cookies.get('visit_count', 0))
    visit_count += 1  # Increment visit count

    # Add this visit to the homepage_visits list with timestamp and location
    homepage_visits.append({
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'location': location
    })

    # Generate the word search puzzle
    grid = generate_puzzle()

    # Format the grid for display as a list of rows (used in the template)
    grid_display = [[cell for cell in row] for row in grid]

    # Store visit count and location in cookies
    resp = make_response(render_template('index.html', location=location, visit_count=visit_count, grid=grid_display, words=WORDS))

    # Set cookies for visit count and location
    resp.set_cookie('visit_count', str(visit_count))
    resp.set_cookie('location', location)

    return resp




@app.route('/visit')
def visit():
    # Get visit count and location from cookies
    visit_count = request.cookies.get('visit_count', 0)
    location = request.cookies.get('location', "Unknown")

    # Display the visit details (location and number of visits)
    return render_template('visit.html', visit_count=visit_count, homepage_visits=homepage_visits)


# Function to get location based on the IP address using ipstack
def get_location(ip):
    try:
        # Call the ipstack API to get location data
        url = f"http://api.ipstack.com/{ip}?access_key={IPSTACK_API_KEY}"
        response = requests.get(url)

        # Check the response from the API
        if response.status_code == 200:
            data = response.json()
            # Format the location as "City, Country"
            city = data.get('city', 'Unknown')
            country = data.get('country_name', 'Unknown')  # 'country_name' is the correct field name in ipstack
            location = f"{city}, {country}"
            return location
        else:
            return "Location unavailable"
    except Exception:
        return "Location unavailable"



# Function to calculate the age based on date of birth
def calculate_age(age):
    dob_date = datetime.strptime(age, '%Y-%m-%d')  # Convert string to date object
    today = datetime.today()  # Current date
    age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))  # Age calculation
    return age

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    age = calculate_age(request.form['age'])
    email = request.form['email']
    phone = request.form['phone']
    service = request.form['service']


    session['name'] = name
    session['age'] = age
    session['email'] = email
    session['phone'] = phone
    session['service'] = service

    new_registration = Registration(name=name, age=age, email=email, phone=phone, service=service)
    db.session.add(new_registration)
    db.session.commit()
    return redirect(url_for('confirmation'))

@app.route('/confirmation')
def confirmation():
    # Retrieve the data from the database (most recent submission)
    latest_submission = Registration.query.order_by(Registration.id.desc()).first()

    if latest_submission:
        return render_template(
            'confirmation.html',
            name=latest_submission.name,
            age=latest_submission.age,
            email=latest_submission.email,
            phone=latest_submission.phone,
            service=latest_submission.service,
                   )
    else:
        return "No submission found."

    # Route to fetch all comments


@app.route('/debug-data')
def debug_data():
    registrations = Registration.query.all()
    for reg in registrations:
        app.logger.info(f"DB Record - Name: {reg.name}, Age: {reg.age}, Email: {reg.email}, Phone: {reg.phone}, Service: {reg.service}")
    return "Data logged to console"

@app.route('/admin/registrations')
def admin_registrations():
    # Fetch all registrations from the database
    registrations = Registration.query.all()

    # Get the latest data from the session
    latest_data = {
        "name": session.get('name'),
        "age": session.get('age'),
        "email": session.get('email'),
        "phone": session.get('phone'),
        "service": session.get('service'),
    }

    return render_template(
        'admin_registrations.html',
        registrations=registrations,
        latest=latest_data,
        datetime=datetime  # Pass datetime to the template
    )
@app.route('/admin/delete_submission/<int:id>', methods=['POST'])
def delete_submission(id):
    try:
        submission = Registration.query.get(id)
        if submission:
            db.session.delete(submission)
            db.session.commit()
            return jsonify({"success": True, "message": "Submission deleted successfully."})
        else:
            return jsonify({"success": False, "message": "Submission not found."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)})


EXCEL_FILE = r"C:\Users\OWMER\sascp-web\facility_geolocations.xlsx"

@app.route('/api/facilities', methods=['GET'])
def get_facilities():
    try:
        # Attempt to read the Excel file
        data = pd.read_excel(EXCEL_FILE)

        # Check if the required columns exist
        required_columns = ['Facility Name', 'Address', 'LGA','Contact Number']
        missing_columns = [col for col in required_columns if col not in data.columns]

        if missing_columns:
            app.logger.error(f"Missing required columns: {', '.join(missing_columns)}")
            return jsonify({"status": "error", "message": f"Missing required columns: {', '.join(missing_columns)}"}), 500

        # Clean and sanitize the data
        data = data.fillna('')  # Replace NaN with empty string for all columns

        # Convert all columns to string for uniformity and remove leading/trailing spaces
        data['Facility Name'] = data['Facility Name'].astype(str).str.strip()
        data['Address'] = data['Address'].astype(str).str.strip()
        data['Contact Number'] = data['Contact Number'].astype(str).str.strip()
        data['LGA'] = data['LGA'].astype(str).str.strip()

        # Convert the dataframe to a list of dictionaries
        facilities = data.to_dict(orient='records')

        # Prepare the response
        response = jsonify({"status": "success", "facilities": facilities})
        response.headers['Content-Type'] = 'application/json'  # Ensure the content-type is correct
        return response

    except FileNotFoundError:
        app.logger.error("Excel file not found")
        return jsonify({"status": "error", "message": "Excel file not found"}), 500
    except pd.errors.EmptyDataError:
        app.logger.error("Excel file is empty")
        return jsonify({"status": "error", "message": "Excel file is empty"}), 500
    except Exception as e:
        app.logger.error(f"An error occurred: {str(e)}")
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500



@app.route('/testing-counseling')
def testing_counseling():
    return render_template('testing-counseling.html')

@app.route('/prevention-program')
def prevention_program():
    return render_template('prevention-program.html')

@app.route('/treatment-support')
def treatment_support():
    return render_template('treatment-support.html')

@app.route('/prep-pep')
def prep_pep():
    return render_template('prep-pep.html')

@app.route('/hiv-awareness-brochure')
def hiv_awareness_brochure():
    return render_template('hiv-awareness-brochure.html')

@app.route('/sti-prevention-guide')
def sti_prevention_guide():
    return render_template('sti-prevention-guide.html')

@app.route('/pep-prep-faqs')
def pep_prep_faqs():
    return render_template('pep-prep-faqs.html')

@app.route('/helpful-videos')
def helpful_videos():
  return render_template('helpful-videos.html')

@app.route('/hepatitis-care')
def hepatitis():
    return render_template('hepatitis-care.html')

@app.route('/pmtct-services')
def pmtct():
    return render_template('pmtct.html')

@app.route('/hiv_facilities')
def facilities():
    return render_template('hiv_facilities.html')

@app.route('/ghr')
def gender_and_human_right():
    return render_template('ghr.html')


# Run only in development
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)