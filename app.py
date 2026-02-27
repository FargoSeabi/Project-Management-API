from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project_manager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -----------------------
# Models
# -----------------------

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tasks = db.relationship('Task', backref='project', cascade="all, delete")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at
        }


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))
    status = db.Column(db.String(50), default="pending")  # pending, in-progress, completed
    priority = db.Column(db.String(20), default="medium")  # low, medium, high
    due_date = db.Column(db.DateTime)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "due_date": self.due_date,
            "project_id": self.project_id
        }


# Create database
with app.app_context():
    db.create_all()

# -----------------------
# Routes
# -----------------------

@app.route("/")
def home():
    return jsonify({"message": "Project Management API Running"}), 200


# Create Project
@app.route("/projects", methods=["POST"])
def create_project():
    data = request.get_json()

    if not data or not data.get("name"):
        return jsonify({"error": "Project name required"}), 400

    project = Project(name=data["name"])
    db.session.add(project)
    db.session.commit()

    return jsonify(project.to_dict()), 201


# Get All Projects
@app.route("/projects", methods=["GET"])
def get_projects():
    projects = Project.query.all()
    return jsonify([p.to_dict() for p in projects]), 200


# Create Task
@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json()

    required_fields = ["title", "project_id"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Title and project_id required"}), 400

    task = Task(
        title=data["title"],
        description=data.get("description"),
        status=data.get("status", "pending"),
        priority=data.get("priority", "medium"),
        project_id=data["project_id"]
    )

    db.session.add(task)
    db.session.commit()

    return jsonify(task.to_dict()), 201


# Get All Tasks (with optional filters)
@app.route("/tasks", methods=["GET"])
def get_tasks():
    status = request.args.get("status")
    priority = request.args.get("priority")

    query = Task.query

    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)

    tasks = query.all()

    return jsonify([t.to_dict() for t in tasks]), 200


# Update Task
@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    task = Task.query.get(task_id)

    if not task:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json()

    task.title = data.get("title", task.title)
    task.description = data.get("description", task.description)
    task.status = data.get("status", task.status)
    task.priority = data.get("priority", task.priority)

    db.session.commit()

    return jsonify(task.to_dict()), 200


# Delete Task
@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = Task.query.get(task_id)

    if not task:
        return jsonify({"error": "Task not found"}), 404

    db.session.delete(task)
    db.session.commit()

    return jsonify({"message": "Task deleted"}), 200


if __name__ == "__main__":
    app.run(debug=True)
