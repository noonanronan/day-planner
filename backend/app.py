from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import time
from datetime import datetime, timezone
from dateutil import parser
from pyexcel_ods3 import get_data, save_data
from io import BytesIO
import openpyxl
import os
import logging
import random

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins

# Enable logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

# Configure the MySQL database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Wabbeylodge1987%23@localhost/day_planner'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Directory for storing uploaded files
UPLOAD_FOLDER = 'uploaded_templates'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Define a Worker model
class Worker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roles = db.Column(db.JSON, nullable=False)  # Roles as a JSON column
    availability = db.Column(db.JSON, nullable=False)  # Availability as a JSON column

    def __repr__(self):
        return f"<Worker {self.name}>"

# API endpoint to get all workers
@app.route("/workers", methods=["GET"])
def get_all_workers():
    try:
        workers = Worker.query.all()
        workers_list = [
            {
                "id": worker.id,
                "name": worker.name,
                "roles": worker.roles,
                "availability": worker.availability
            }
            for worker in workers
        ]
        logging.info("Fetched all workers successfully.")
        return jsonify({"workers": workers_list}), 200
    except Exception as e:
        logging.error(f"Error fetching workers: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/upload-excel', methods=['POST'])
def upload_excel():
    try:
        file = request.files['file']
        if not file:
            return jsonify({'error': 'No file provided'}), 400

        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        return jsonify({'message': f'File {filename} uploaded successfully'}), 200
    except Exception as e:
        logging.error(f"Error uploading file: {e}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/list-templates', methods=['GET'])
def list_templates():
    try:
        files = os.listdir(UPLOAD_FOLDER)
        logging.debug(f"Templates found: {files}")
        return jsonify({'templates': files}), 200
    except Exception as e:
        logging.error(f"Error listing templates: {e}")
        return jsonify({'error': str(e)}), 500


# API endpoint to upload Excel/ODS files
@app.route('/generate-schedule', methods=['POST'])
def generate_schedule():
    try:
        selected_file = request.json.get('template')
        logging.debug(f"Selected file: {selected_file}")
        if not selected_file:
            return jsonify({'error': 'No template selected'}), 400

        filepath = os.path.join(UPLOAD_FOLDER, selected_file)
        logging.debug(f"Filepath: {filepath}")
        if not os.path.exists(filepath):
            return jsonify({'error': 'Selected template not found'}), 404

        # Fetch all workers from the database
        workers = Worker.query.all()
        today = datetime.now(tz=timezone.utc)
        logging.debug(f"Today's UTC date: {today}")

        # Separate workers into available and late-shift workers
        in_today_workers = []
        late_shift_workers = []

        for worker in workers:
            for availability in worker.availability:
                start = parser.parse(availability['start']).astimezone(timezone.utc)
                end = parser.parse(availability['end']).astimezone(timezone.utc)
                if start <= today <= end:
                    if start.hour >= 10:
                        late_shift_workers.append(worker)
                    else:
                        in_today_workers.append(worker)
                    break

        logging.debug(f"Workers available today: {[worker.name for worker in in_today_workers]}")
        logging.debug(f"Late shift workers: {[worker.name for worker in late_shift_workers]}")

        # Define starting roles
        starting_roles = {
            'Host': None,
            'Dekit': None,
            'Kit Up 1': None,
            'Kit Up 2': None,
            'Kit Up 3': None,
            'Clip In 1': None,
            'Clip In 2': None,
            'Tree Trek 1': None,
            'Tree Trek 2': None,
            'Course Support 1': None,
            'Course Support 2': None,
            'Zip Top 1': None,
            'Zip Top 2': None,
            'Zip Ground': None,
            'Rotate to Course 1': None,
            'Mini Trek': None,
            'ICA 1': None,
            'ICA 2': None,
            'ICA 3': None,
            'ICA 4': None,
        }

        # Role priority
        prioritized_roles = (
            ['ICA 1', 'ICA 2', 'ICA 3', 'ICA 4'] +  # ICA roles first
            ['Mini Trek'] +                         # Then Mini Trek
            ['Course Support 1', 'Course Support 2', 'Zip Top 1', 'Zip Top 2', 'Zip Ground', 'Rotate to Course 1'] +  # Course
            ['Tree Trek 1', 'Tree Trek 2'] +        # Tree Trek
            ['Kit Up 2', 'Kit Up 3', 'Clip In 1', 'Clip In 2', 'Dekit', 'Host', 'Kit Up 1']  # Shed (Dekit last)
        )

        # Helper function to get eligible workers for a role
        def get_eligible_workers(role):
            if role.startswith('ICA'):
                return [
                    worker for worker in in_today_workers
                    if 'ICA' in worker.roles and worker.name not in starting_roles.values()
                ]
            elif role == 'Mini Trek':
                return [
                    worker for worker in in_today_workers
                    if 'MT' in worker.roles and worker.name not in starting_roles.values()
                ]
            elif role in ['Course Support 1', 'Rotate to Course 1']:
                # Allow late-shift workers for these specific roles
                return [
                    worker for worker in (in_today_workers + late_shift_workers)
                    if 'AATT' in worker.roles and worker.name not in starting_roles.values()
                ]
            elif role in ['Course Support 2', 'Zip Top 1', 'Zip Top 2', 'Zip Ground']:
                return [
                    worker for worker in in_today_workers
                    if 'AATT' in worker.roles and worker.name not in starting_roles.values()
                ]
            elif role in ['Tree Trek 1', 'Tree Trek 2']:
                return [
                    worker for worker in in_today_workers
                    if 'AATT' in worker.roles and worker.name not in starting_roles.values()
                ]
            else:  # Shed roles
                return [
                    worker for worker in (in_today_workers + late_shift_workers)
                    if 'AATT' in worker.roles and worker.name not in starting_roles.values()
                ]


        # Assign roles based on priority
        for role in prioritized_roles:
            eligible_workers = get_eligible_workers(role)
            if eligible_workers:
                selected_worker = random.choice(eligible_workers)
                starting_roles[role] = selected_worker.name
                logging.info(f"Assigned {selected_worker.name} to {role}")
            else:
                logging.warning(f"Unfilled position: {role}")


        # Check for unfilled positions
        for role, worker in starting_roles.items():
            if worker is None:
                logging.error(f"Unfilled position: {role}")
                return jsonify({'error': f"Could not assign all roles. Missing: {role}"}), 500

        # Log the final assignments
        logging.info("Starting positions:")
        for role, worker in starting_roles.items():
            if worker:
                logging.info(f"{role}: {worker}")
            else:
                logging.warning(f"{role}: Unfilled")

        # Return starting positions
        return jsonify({
            'message': 'Starting positions assigned',
            'starting_positions': starting_roles
        }), 200

    except Exception as e:
        logging.error(f"Error generating schedule: {e}")
        return jsonify({'error': str(e)}), 500


# API endpoint to create a worker
@app.route("/workers", methods=["POST"])
def create_worker():
    try:
        logging.debug("Incoming request data: %s", request.json)
        data = request.get_json()

        if not data or "name" not in data or "roles" not in data or "availability" not in data:
            return jsonify({"error": "Missing required fields: name, roles, or availability"}), 400

        new_worker = Worker(
            name=data["name"],
            roles=data["roles"],
            availability=data["availability"],
        )
        db.session.add(new_worker)
        db.session.commit()

        logging.info(f"Worker {new_worker.name} created successfully.")
        return jsonify({
            "message": "Worker created successfully",
            "worker": {
                "id": new_worker.id,
                "name": new_worker.name,
                "roles": new_worker.roles,
                "availability": new_worker.availability,
            },
        }), 201
    except Exception as e:
        logging.error(f"Error creating worker: {e}")
        return jsonify({"error": str(e)}), 500

# API endpoint to update a worker by ID
@app.route("/workers/<int:worker_id>", methods=["PUT"])
def update_worker(worker_id):
    try:
        worker = Worker.query.get(worker_id)
        if not worker:
            return jsonify({"error": f"No worker found with ID {worker_id}"}), 404

        data = request.get_json()
        worker.name = data.get("name", worker.name)
        worker.roles = data.get("roles", worker.roles)
        worker.availability = data.get("availability", worker.availability)

        db.session.commit()

        updated_worker_data = {
            "id": worker.id,
            "name": worker.name,
            "roles": worker.roles,
            "availability": worker.availability
        }

        return jsonify({"message": "Worker updated successfully", "worker": updated_worker_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API endpoint to delete a worker by ID
@app.route("/workers/<int:worker_id>", methods=["DELETE"])
def delete_worker(worker_id):
    try:
        worker = Worker.query.get(worker_id)
        if not worker:
            return jsonify({"error": f"Worker with ID {worker_id} not found"}), 404

        db.session.delete(worker)
        db.session.commit()

        return jsonify({"message": "Worker deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Home route to confirm the app is running
@app.route("/")
def home():
    return "Flask app is running!"

# Create the database tables
with app.app_context():
    db.create_all()
    logging.info("Database tables created successfully!")

# Run the app
if __name__ == "__main__":
    logging.info("Starting Flask app...")
    app.run(debug=True, port=5001)
