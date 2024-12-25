from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import time
import openpyxl
import os
import logging
from pyexcel_ods3 import get_data  # For .ods files

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins

# Enable logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

# Configure the MySQL database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Wabbeylodge1987%23@localhost/day_planner'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

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

# API to handle Excel/ODS upload and parsing
@app.route('/upload-excel', methods=['POST'])
def upload_excel():
    try:
        # Check if a file is uploaded
        if 'file' not in request.files:
            app.logger.warning("No file selected in the request.")
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            app.logger.warning("No file selected in the request.")
            return jsonify({'error': 'No selected file'}), 400

        # Save the file temporarily
        temp_path = os.path.join('temp', file.filename)
        file.save(temp_path)

        # Determine the file format and open accordingly
        rows = []
        if temp_path.endswith('.xlsx'):
            app.logger.info("Processing an .xlsx file.")
            workbook = openpyxl.load_workbook(temp_path)
            sheet = workbook.active

            # Extract rows, converting time objects to strings
            for row in sheet.iter_rows(min_row=2, values_only=True):  # Skip the header
                processed_row = [
                    cell.strftime("%H:%M:%S") if isinstance(cell, time) else cell
                    for cell in row
                ]
                rows.append(processed_row)

        elif temp_path.endswith('.ods'):
            app.logger.info("Processing an .ods file.")
            data = get_data(temp_path)
            for row in data[list(data.keys())[0]]:  # Read the first sheet
                processed_row = [
                    cell.strftime("%H:%M:%S") if isinstance(cell, time) else cell
                    for cell in row
                ]
                rows.append(processed_row)

        else:
            app.logger.error("Unsupported file format.")
            return jsonify({'error': 'Unsupported file format. Only .xlsx and .ods are allowed.'}), 400

        # Delete the temp file after processing
        os.remove(temp_path)

        app.logger.info("File processed successfully.")
        return jsonify({'data': rows}), 200

    except Exception as e:
        app.logger.error(f"Error processing file: {e}")
        return jsonify({'error': str(e)}), 500

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
