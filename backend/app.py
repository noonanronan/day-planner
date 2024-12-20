from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

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
        return jsonify({"workers": workers_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# API endpoint to get a worker by ID
@app.route("/workers/<int:worker_id>", methods=["GET"])
def get_worker_by_id(worker_id):
    try:
        # Query the worker by ID
        worker = Worker.query.get(worker_id)
        
        if not worker:
            return jsonify({"error": f"No worker found with ID {worker_id}"}), 404

        # Format the worker as a dictionary
        worker_data = {
            "id": worker.id,
            "name": worker.name,
            "roles": worker.roles,
            "availability": worker.availability
        }

        return jsonify({"worker": worker_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API endpoint to update a worker by ID
@app.route("/workers/<int:worker_id>", methods=["PUT"])
def update_worker(worker_id):
    try:
        # Query the worker by ID
        worker = Worker.query.get(worker_id)
        
        if not worker:
            return jsonify({"error": f"No worker found with ID {worker_id}"}), 404

        # Get JSON data from the request
        data = request.get_json()

        # Update worker fields
        worker.name = data.get("name", worker.name)
        worker.roles = data.get("roles", worker.roles)
        worker.availability = data.get("availability", worker.availability)

        # Commit changes to the database
        db.session.commit()

        # Return the updated worker details
        updated_worker_data = {
            "id": worker.id,
            "name": worker.name,
            "roles": worker.roles,
            "availability": worker.availability
        }

        return jsonify({"message": "Worker updated successfully", "worker": updated_worker_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/workers/<int:worker_id>", methods=["DELETE"])
def delete_worker(worker_id):
    try:
        # Query the worker by ID
        worker = Worker.query.get(worker_id)

        # Check if worker exists
        if not worker:
            return jsonify({"error": f"Worker with ID {worker_id} not found"}), 404

        # Delete the worker
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
    print("Database tables created successfully!")

# Run the app
if __name__ == "__main__":
    print("Starting Flask app...")
    app.run(debug=True, port=5001)
