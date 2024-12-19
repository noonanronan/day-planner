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

# API endpoint to create a worker
@app.route("/workers", methods=["POST"])
def create_worker():
    print("Received request at /workers")
    try:
        data = request.get_json()
        print("Data received:", data)
        # Rest of your code here...
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500
    try:
        # Get JSON data from the request
        data = request.get_json()
        
        # Extract worker details
        name = data.get("name")
        roles = data.get("roles")
        availability = data.get("availability")
        
        # Validate the input
        if not name or not roles or not availability:
            return jsonify({"error": "Missing required fields: name, roles, or availability"}), 400
        
        # Create a new worker object
        new_worker = Worker(name=name, roles=roles, availability=availability)
        
        # Add to the database
        db.session.add(new_worker)
        db.session.commit()
        
        return jsonify({"message": "Worker created successfully", "worker": {
            "id": new_worker.id,
            "name": new_worker.name,
            "roles": new_worker.roles,
            "availability": new_worker.availability
        }}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API endpoint to get all workers
@app.route("/workers", methods=["GET"])
def get_all_workers():
    try:
        # Query all workers from the database
        workers = Worker.query.all()

        # Format the workers as a list of dictionaries
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
