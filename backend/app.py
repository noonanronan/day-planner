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


# API endpoint to generate the schedule and save to Excel
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

        print_excel_file(filepath)

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
                    if start.hour >= 10:  # Late-shift workers start at or after 10:00
                        late_shift_workers.append(worker)
                    else:  # Early workers available before 10:00
                        in_today_workers.append(worker)
                    break

        logging.debug(f"Workers available today: {[worker.name for worker in in_today_workers]}")
        logging.debug(f"Late shift workers: {[worker.name for worker in late_shift_workers]}")

        # Dynamically map roles based on the Excel file
        workbook = openpyxl.load_workbook(filepath)
        sheet = workbook.active
        role_to_column = {}
        header_row = 1  # Assuming the first row contains headers

        for col in range(1, sheet.max_column + 1):
            role = sheet.cell(row=header_row, column=col).value
            if role:  # Skip empty cells
                role_to_column[role.strip()] = col

        logging.debug(f"Dynamically mapped roles: {role_to_column}")

        # Define starting roles
        valid_roles = {}

        # Prioritized roles for assignment
        prioritized_roles = [
            'ICA 1', 'ICA 2', 'ICA 3', 'ICA 4',
            'Mini Trek',
            'Course Support 1', 'Course Support 2', 'Zip Top 1', 'Zip Top 2', 'Zip Ground', 'rotate to course 1',
            'TREE TREK 1', 'TREE TREK 2',
            'Kit Up 2', 'Kit Up 3', 'Clip In 1', 'Clip In 2', 'Dekit', 'Host', 'Kit Up 1'
        ]

        restricted_roles_for_late_shift = {
            'ICA 1', 'ICA 2', 'ICA 3', 'ICA 4',
            'Mini Trek',
            'Course Support 2', 'Zip Top 1', 'Zip Top 2', 'Zip Ground'
        }

        def get_eligible_workers(role):
            """Determine eligible workers for a role."""
            if role in restricted_roles_for_late_shift:
                # Only consider early workers for restricted roles
                eligible_workers = [worker for worker in in_today_workers if worker.name not in valid_roles.values()]
            elif role.startswith('ICA'):
                # ICA roles are handled with early workers only
                eligible_workers = [worker for worker in in_today_workers if 'ICA' in worker.roles and worker.name not in valid_roles.values()]
            elif role == 'Mini Trek':
                # Mini Trek is also restricted to early workers
                eligible_workers = [worker for worker in in_today_workers if 'MT' in worker.roles and worker.name not in valid_roles.values()]
            elif role in ['Course Support 1', 'rotate to course 1', 'TREE TREK 1', 'TREE TREK 2']:
                # These roles can use both early and late-shift workers
                eligible_workers = [worker for worker in (in_today_workers + late_shift_workers) if 'AATT' in worker.roles and worker.name not in valid_roles.values()]
            else:
                # Other roles, fallback to late-shift workers if no early workers are available
                eligible_workers = [worker for worker in in_today_workers if 'AATT' in worker.roles and worker.name not in valid_roles.values()]
                if not eligible_workers:  # Fallback to late-shift workers
                    eligible_workers = [worker for worker in late_shift_workers if 'AATT' in worker.roles and worker.name not in valid_roles.values()]
            return eligible_workers

        for role in prioritized_roles:
            if role in role_to_column:  # Only process roles present in the Excel file
                eligible_workers = get_eligible_workers(role)
                if eligible_workers:
                    selected_worker = random.choice(eligible_workers)
                    valid_roles[role] = selected_worker.name
                    logging.info(f"Assigned {selected_worker.name} to {role}")
                else:
                    logging.warning(f"No eligible workers for {role}, skipping.")

        # Write assigned workers to the Excel file
        nine_am_row = 2  
        for role, column in role_to_column.items():
            assigned_worker = valid_roles.get(role)
            if assigned_worker:
                sheet.cell(row=nine_am_row, column=column).value = assigned_worker

        # Save to memory and send back
        output = BytesIO()
        workbook.save(output)
        output.seek(0)
        return send_file(output, as_attachment=True, download_name="day_schedule.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        logging.error(f"Error generating schedule: {e}")
        return jsonify({'error': str(e)}), 500

def print_excel_file(filepath):
    try:
        logging.debug("Attempting to load Excel file for inspection.")
        workbook = openpyxl.load_workbook(filepath)
        sheet = workbook.active

        logging.info("Excel File Contents:")
        for row in sheet.iter_rows(values_only=True):
            logging.info(row)

        # Print merged cell ranges
        logging.info("Merged Cell Ranges:")
        for merged_range in sheet.merged_cells.ranges:
            logging.info(f"Range: {merged_range}, Min Row: {merged_range.min_row}, Max Row: {merged_range.max_row}, "
                         f"Min Col: {merged_range.min_col}, Max Col: {merged_range.max_col}")

    except Exception as e:
        logging.error(f"Error reading Excel file: {e}")



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
