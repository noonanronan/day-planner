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
from random import choice

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

        # Fetch all workers from the database
        workers = Worker.query.all()
        today = datetime.now(tz=timezone.utc)
        logging.debug(f"Today's UTC date: {today}")

        # Define role-to-training mapping
        role_to_training = {
            'KITUP': ['Host', 'Dekit', 'Kit Up 1', 'Kit Up 2', 'Kit Up 3', 'Clip In 1', 'Clip In 2'],
            'AATT': ['TREE TREK 1', 'TREE TREK 2', 'Course Support 1', 'Course Support 2', 'Zip Top 1', 'Zip Top 2', 'Zip Ground', 'rotate to course 1'],
            'MT': ['Mini Trek'],
            'ICA': ['ICA 1', 'ICA 2', 'ICA 3', 'ICA 4']
        }

        # Separate workers into available and late-shift workers
        in_today_workers = []
        late_shift_workers = []

        for worker in workers:
            for availability in worker.availability:
                try:
                    start = parser.parse(availability['start']).astimezone(timezone.utc)
                    end = parser.parse(availability['end']).astimezone(timezone.utc)
                    logging.debug(f"Worker {worker.name} availability: start={start}, end={end}")

                    if start <= today <= end:
                        if start.hour >= 10:  # Late-shift workers start at or after 10:00
                            late_shift_workers.append(worker)
                        else:  # Early workers available before 10:00
                            in_today_workers.append(worker)
                        break
                except Exception as e:
                    logging.error(f"Error parsing availability for worker {worker.name}: {e}")

        logging.debug(f"Final In Today Workers: {[worker.name for worker in in_today_workers]}")
        logging.debug(f"Final Late Shift Workers: {[worker.name for worker in late_shift_workers]}")


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

        # Prioritized roles for assignment
        prioritized_roles = [
            'ICA 1', 'ICA 2', 'ICA 3', 'ICA 4',
            'Mini Trek',
            'Course Support 1', 'Course Support 2', 'Zip Top 1', 'Zip Top 2', 'Zip Ground', 'rotate to course 1',
            'TREE TREK 1', 'TREE TREK 2',
            'Kit Up 1', 'Kit Up 2', 'Kit Up 3', 'Clip In 1', 'Clip In 2', 'Dekit', 'Host'
        ]

        # Role restrictions for late-shift workers
        restricted_roles_for_late_shift = {
            'ICA 1', 'ICA 2', 'ICA 3', 'ICA 4'
        }

        valid_roles = {}
        used_workers = set()

        def get_eligible_workers(role):
            if role in role_to_training['KITUP']:
                return [
                    worker for worker in (in_today_workers + late_shift_workers)
                    if worker.name not in used_workers
                    and 'KITUP' in worker.roles  # Only select workers trained in KITUP
                ]
            elif role in role_to_training['AATT']:
                return [
                    worker for worker in (in_today_workers + late_shift_workers)
                    if worker.name not in used_workers
                    and 'AATT' in worker.roles  # Only select workers trained in AATT
                ]
            elif role in role_to_training['MT']:
                return [
                    worker for worker in in_today_workers
                    if worker.name not in used_workers
                    and 'MT' in worker.roles  # Only select workers trained in Mini Trek
                ]
            elif role in role_to_training['ICA']:
                return [
                    worker for worker in in_today_workers
                    if worker.name not in used_workers
                    and 'ICA' in worker.roles  # Only select workers trained in ICA
                ]
            else:
                return []



        morning_assignments = {}  # Dictionary to store the morning role assignments

        # Assign workers to the first time slot (9:00-9:30)
        for role in prioritized_roles:
            if role in role_to_column:
                eligible_workers = get_eligible_workers(role)
                if eligible_workers:
                    selected_worker = choice(eligible_workers)
                    valid_roles[role] = selected_worker.name
                    used_workers.add(selected_worker.name)
                    logging.info(f"Assigned {selected_worker.name} to {role}")
                else:
                    logging.warning(f"No eligible workers for {role}, skipping.")

        # Track morning assignments properly (store all roles)
        for role, worker in valid_roles.items():
            if worker not in morning_assignments:
                morning_assignments[worker] = []  # Initialize list if not present
            morning_assignments[worker].append(role)  # Store all roles they worked in the morning

        # Write the assignments for the first time slot (9:00-9:30) to the Excel file
        for role, column in role_to_column.items():
            assigned_worker = valid_roles.get(role)
            if assigned_worker:
                sheet.cell(row=2, column=column).value = assigned_worker

        # Identify spare workers
        assigned_worker_names = set(valid_roles.values())
        spare_workers = [
            worker.name for worker in in_today_workers + late_shift_workers
            if worker.name not in assigned_worker_names
        ]

        if spare_workers:
            logging.info(f"Spare workers: {spare_workers}")
        else:
            logging.info("No spare workers.")


        # Fill Shed (Host, Dekit, Kit Up 1), Tree Trek, Mini Trek, and ICA roles for all time slots till lunch
        lunch_slots = [3, 4, 5, 6, 7, 8]  # Rows corresponding to 9:30, 10:00, ..., 12:00-12:45
        for slot_row in lunch_slots:
            for role in ['Host', 'Dekit', 'Kit Up 1', 'TREE TREK 1', 'TREE TREK 2', 'Mini Trek', 'ICA 1', 'ICA 2', 'ICA 3', 'ICA 4']:
                column = role_to_column.get(role)
                if column:
                    sheet.cell(row=slot_row, column=column).value = valid_roles.get(role)

        # Handle Kit Up 2, Kit Up 3, Clip In 1, and Clip In 2
        for slot_row in lunch_slots:
            if slot_row == 5:  # 10:30 row
                # Swap Kit Up 2 with Clip In 1
                temp_kit_up_2 = valid_roles.get('Kit Up 2')
                temp_kit_up_3 = valid_roles.get('Kit Up 3')
                valid_roles['Kit Up 2'], valid_roles['Clip In 1'] = valid_roles.get('Clip In 1'), temp_kit_up_2
                valid_roles['Kit Up 3'], valid_roles['Clip In 2'] = valid_roles.get('Clip In 2'), temp_kit_up_3

            # Assign updated roles for Kit Up 2, Kit Up 3, Clip In 1, and Clip In 2
            for role in ['Kit Up 2', 'Kit Up 3', 'Clip In 1', 'Clip In 2']:
                column = role_to_column.get(role)
                if column:
                    sheet.cell(row=slot_row, column=column).value = valid_roles.get(role)

        # Handle Course role rotations till lunch
        course_roles = [
            'Course Support 1', 'Course Support 2', 'Zip Top 1',
            'Zip Top 2', 'Zip Ground', 'rotate to course 1'
        ]

        # Assign initial workers to course roles (9:00-9:30)
        course_workers = [valid_roles.get(role) for role in course_roles]

        # Rotate course roles for each subsequent time slot until lunch
        for slot_row in lunch_slots:
            # Rotate workers: Last worker moves to the first position
            course_workers = course_workers[-1:] + course_workers[:-1]

            # Assign rotated workers to their roles for this time slot
            for role, worker in zip(course_roles, course_workers):
                column = role_to_column.get(role)
                if column:
                    sheet.cell(row=slot_row, column=column).value = worker

        # Assign workers to their starting positions after lunch (12:45-1:30)
        logging.info("Assigning workers for 12:45-1:30 (after lunch)...")

        # Track afternoon usage
        afternoon_valid_roles = {}  # Roles assigned in the afternoon
        afternoon_used_workers = set()  # Workers used in the afternoon

        # Define role categories for clarity and maintainability
        shed_roles = {'Host', 'Dekit', 'Kit Up 1', 'Kit Up 2', 'Kit Up 3', 'Clip In 1', 'Clip In 2'}
        tree_trek_roles = {'TREE TREK 1', 'TREE TREK 2'}
        course_roles = {'Course Support 1', 'Course Support 2', 'Zip Top 1', 'Zip Top 2', 'Zip Ground', 'rotate to course 1'}
        mini_trek_roles = {'Mini Trek'}
        ica_roles = {'ICA 1', 'ICA 2', 'ICA 3', 'ICA 4'}



        # Function to get eligible workers for afternoon assignments
        def get_afternoon_eligible_workers(role):
            eligible = [
                worker for worker in (in_today_workers + late_shift_workers)
                if worker.name not in afternoon_used_workers
            ]

            if role in tree_trek_roles:
                eligible = [
                    worker for worker in eligible
                    if 'AATT' in worker.roles  # Must be trained in AATT
                    and not any(m_role in tree_trek_roles for m_role in morning_assignments.get(worker.name, []))
                ]
            elif role in course_roles:
                eligible = [
                    worker for worker in eligible
                    if 'AATT' in worker.roles  # Must be trained in AATT
                    and not any(m_role in course_roles for m_role in morning_assignments.get(worker.name, []))
                ]
            elif role in mini_trek_roles:
                eligible = [
                    worker for worker in eligible
                    if 'MT' in worker.roles  # Must be trained in Mini Trek
                    and not any(m_role in mini_trek_roles for m_role in morning_assignments.get(worker.name, []))
                ]
            elif role in ica_roles:
                eligible = [
                    worker for worker in in_today_workers  # Ensure only early workers can be assigned
                    if worker.name not in afternoon_used_workers
                    and 'ICA' in worker.roles  # Must be trained in ICA
                    and not any(m_role in ica_roles for m_role in morning_assignments.get(worker.name, []))
                ]
            elif role in shed_roles:
                non_repeating_workers = [
                    worker for worker in eligible
                    if 'KITUP' in worker.roles  # Must be trained in KITUP
                    and not any(m_role in shed_roles for m_role in morning_assignments.get(worker.name, []))
                ]
                if non_repeating_workers:
                    eligible = non_repeating_workers

            return eligible


        # Assign workers for 12:45-1:30
        for role in prioritized_roles:
            eligible_workers = get_afternoon_eligible_workers(role)
            logging.debug(f"Eligible workers for {role} (12:45-1:30): {[worker.name for worker in eligible_workers]}")
            if eligible_workers:
                selected_worker = choice(eligible_workers)  # Randomly select a worker
                afternoon_valid_roles[role] = selected_worker.name
                afternoon_used_workers.add(selected_worker.name)
                logging.info(f"Assigned {selected_worker.name} to {role} (12:45-1:30)")
            else:
                logging.warning(f"No eligible workers for {role} (12:45-1:30), skipping.")


        # Print assignments to console
        logging.info("Afternoon Assignments (12:45-1:30):")
        for role, worker in afternoon_valid_roles.items():
            logging.info(f"{role}: {worker}")

        # Write afternoon assignments (12:45-1:30) to the Excel sheet
        logging.info("Writing afternoon assignments (12:45-1:30) to the Excel sheet...")

        # Identify the row corresponding to 12:45-1:30
        afternoon_slot_row = None

        # Find the row for "12:45-1:30" in the Excel sheet
        for row in range(1, sheet.max_row + 1):
            cell_value = sheet.cell(row=row, column=1).value
            if cell_value and str(cell_value).strip() == "12:45-1:30":
                afternoon_slot_row = row
                break

        if afternoon_slot_row:
            for role, worker in afternoon_valid_roles.items():
                column = role_to_column.get(role)
                if column:
                    sheet.cell(row=afternoon_slot_row, column=column).value = worker
                    logging.info(f"Assigned {worker} to {role} (12:45-1:30, Row: {afternoon_slot_row}, Column: {column})")
        else:
            logging.warning("Unable to find the row for '12:45-1:30' in the Excel sheet.")


        # Define afternoon time slots in the Excel sheet based on actual labels
        afternoon_slots_rows = [11, 12, 13, 14, 15]  # Corresponding rows for 13:30, 14:00, ..., 15:30

        # Assign workers for each afternoon time slot
        for slot_index, slot_row in enumerate(afternoon_slots_rows):
            logging.info(f"Assigning workers for afternoon slot {slot_index + 1} (Row: {slot_row})...")

            # Handle Kit Up 2, Kit Up 3, Clip In 1, and Clip In 2 at 14:30
            if slot_row == 13:  # Row corresponding to 14:30
                # Swap Kit Up 2 with Clip In 1
                temp_kit_up_2 = afternoon_valid_roles.get('Kit Up 2')
                temp_kit_up_3 = afternoon_valid_roles.get('Kit Up 3')
                afternoon_valid_roles['Kit Up 2'], afternoon_valid_roles['Clip In 1'] = afternoon_valid_roles.get('Clip In 1'), temp_kit_up_2
                afternoon_valid_roles['Kit Up 3'], afternoon_valid_roles['Clip In 2'] = afternoon_valid_roles.get('Clip In 2'), temp_kit_up_3

            # Assign workers for the current time slot
            for role in prioritized_roles:
                eligible_workers = get_afternoon_eligible_workers(role)
                
                # Filter out workers not trained for ICA roles if assigning to ICA roles
                if role.startswith('ICA'):
                    eligible_workers = [worker for worker in eligible_workers if 'ICA' in worker.roles]

                logging.debug(f"Eligible workers for {role} (Row {slot_row}): {[worker.name for worker in eligible_workers]}")

                if eligible_workers:
                    selected_worker = choice(eligible_workers)  # Randomly select a worker
                    afternoon_valid_roles[role] = selected_worker.name
                    afternoon_used_workers.add(selected_worker.name)
                    logging.info(f"Assigned {selected_worker.name} to {role} (Row {slot_row})")
                else:
                    logging.warning(f"No eligible workers for {role} (Row {slot_row}), skipping.")

            # Write assignments for the current time slot to the Excel sheet
            logging.info(f"Writing assignments for Row {slot_row} to the Excel sheet...")
            for role, worker in afternoon_valid_roles.items():
                column = role_to_column.get(role)
                if column:
                    sheet.cell(row=slot_row, column=column).value = worker
                    logging.info(f"Assigned {worker} to {role} (Row: {slot_row}, Column: {column})")

            # Handle Course role rotations for every half-hour time slot
            course_roles = [
                'Course Support 1', 'Course Support 2', 'Zip Top 1',
                'Zip Top 2', 'Zip Ground', 'rotate to course 1'
            ]
            if slot_index == 0:  # Initialize course roles for the first slot
                course_workers = [afternoon_valid_roles.get(role) for role in course_roles]

            # Rotate course roles immediately after the first slot
            if slot_index >= 0:
                course_workers = course_workers[-1:] + course_workers[:-1]  # Rotate the roles
                for role, worker in zip(course_roles, course_workers):
                    column = role_to_column.get(role)
                    if column:
                        sheet.cell(row=slot_row, column=column).value = worker
                        logging.info(f"Rotated {worker} to {role} (Row: {slot_row}, Column: {column})")


        # Log completion of the afternoon schedule
        logging.info("Completed assigning workers for the afternoon schedule.")

        evening_slots_rows = [16, 17, 18, 19, 20, 21]  # Rows for 16:00, 16:30, 17:00, 17:30, 18:00, 18:30

        # Assign late-shift workers to ICA roles from 16:00 - 19:00
        logging.info("Assigning late-shift workers to ICA roles (4:00 - 7:00 PM)...")

        # Ensure we only assign available late workers (if fewer than 4 exist)
        late_workers_for_ica = late_shift_workers[:min(4, len(late_shift_workers))]


        # Assign them for each evening time slot
        for slot_row in evening_slots_rows:
            for i, ica_role in enumerate(['ICA 1', 'ICA 2', 'ICA 3', 'ICA 4']):
                if i < len(late_workers_for_ica):  # Ensure we have a worker
                    worker = late_workers_for_ica[i]
                    column = role_to_column.get(ica_role)
                    if column:
                        sheet.cell(row=slot_row, column=column).value = worker.name
                        logging.info(f"Assigned {worker.name} to {ica_role} (Row: {slot_row})")

        logging.debug(f"Evening ICA Assignments: {[(slot, worker.name) for slot in evening_slots_rows for worker in late_workers_for_ica]}")


        # Save and send the Excel file
        output = BytesIO()
        workbook.save(output)
        output.seek(0)
        return send_file(output, as_attachment=True, download_name="day_schedule.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        logging.error(f"Error generating schedule: {e}")
        return jsonify({'error': str(e)}), 500



# Remove when not needed
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

        # Validate and update name
        worker.name = data.get("name", worker.name)

        # Validate and update roles
        worker.roles = data.get("roles", worker.roles)

        # Validate and update availability
        if "availability" in data:
            # Ensure availability times are ISO 8601 strings
            worker.availability = [
                {
                    "start": parser.parse(a["start"]).isoformat(),
                    "end": parser.parse(a["end"]).isoformat(),
                }
                for a in data["availability"]
            ]

        db.session.commit()

        updated_worker_data = {
            "id": worker.id,
            "name": worker.name,
            "roles": worker.roles,
            "availability": worker.availability,
        }

        return jsonify({"message": "Worker updated successfully", "worker": updated_worker_data}), 200
    except Exception as e:
        logging.error(f"Error updating worker {worker_id}: {e}")
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