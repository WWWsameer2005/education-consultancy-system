from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
import json

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ==============================
# MongoDB Connection
# ==============================
try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["education_ai"]
    students_collection = db["students"]
    admins_collection = db["admins"]
except:
    students_collection = None
    admins_collection = None


# ==============================
# Load Colleges Data
# ==============================
with open("colleges.json", "r", encoding="utf-8") as f:
    colleges = json.load(f)


# ==============================
# HOME
# ==============================
@app.route("/")
def home():
    return render_template("index.html")


# ==============================
# COLLEGES (Search + Filter)
# ==============================
@app.route("/colleges")
def colleges_page():

    search = request.args.get("search", "")
    state = request.args.get("state", "")
    level = request.args.get("level", "")

    filtered = colleges

    if search:
        filtered = [
            c for c in filtered
            if search.lower() in c.get("name", "").lower()
        ]

    if state:
        filtered = [
            c for c in filtered
            if c.get("state", "") == state
        ]

    if level:
        filtered = [
            c for c in filtered
            if c.get("level", "") == level
        ]

    return render_template("colleges.html", colleges=filtered)


# ==============================
# COLLEGE DETAIL
# ==============================
@app.route("/college/<int:college_id>")
def college_detail(college_id):

    selected_college = next(
        (c for c in colleges if c["id"] == college_id),
        None
    )

    return render_template("college_detail.html", college=selected_college)

# ==============================
# ADMIN REGISTER
# ==============================
@app.route("/admin_register", methods=["GET", "POST"])
def admin_register():

    error = None
    success = None

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            error = "Please fill all fields"

        elif admins_collection is not None and admins_collection.find_one({"username": username}):
            error = "Username already exists"

        else:
            if admins_collection is not None:
                admins_collection.insert_one({
                    "username": username,
                    "password": password
                })

            success = "Admin registered successfully! You can login now."

    return render_template("admin_register.html", error=error, success=success)


# ==============================
# ADMIN LOGIN
# ==============================
@app.route("/admin", methods=["GET", "POST"])
def admin():

    error = None

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        admin_user = None

        if admins_collection is not None:
            admin_user = admins_collection.find_one({
                "username": username,
                "password": password
            })

        if admin_user:
            session["admin"] = True
            return redirect(url_for("dashboard"))

        else:
            error = "Invalid Username or Password"

    return render_template("admin_login.html", error=error)


# ==============================
# DASHBOARD
# ==============================
@app.route("/dashboard")
def dashboard():

    if not session.get("admin"):
        return redirect(url_for("admin"))

    students = []

    if students_collection is not None:
        students = list(students_collection.find())

        for student in students:
            student["_id"] = str(student["_id"])

    total_students = len(students)

    states = {}

    for s in students:
        st = s.get("state", "Unknown")
        states[st] = states.get(st, 0) + 1

    return render_template(
        "dashboard.html",
        students=students,
        total_students=total_students,
        states=states
    )


# ==============================
# ADD STUDENT
# ==============================
@app.route("/add_student", methods=["POST"])
def add_student():

    if students_collection is not None:

        students_collection.insert_one({
            "name": request.form.get("name"),
            "marks": request.form.get("marks"),
            "state": request.form.get("state")
        })

    return redirect(url_for("dashboard"))


# ==============================
# CONTACT
# ==============================
@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST" and students_collection is not None:

        students_collection.insert_one({
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "marks": request.form.get("marks"),
            "state": request.form.get("state"),
            "message": request.form.get("message")
        })

        return redirect(url_for("contact"))

    return render_template("contact.html")


# ==============================
# LOGOUT
# ==============================
@app.route("/logout")
def logout():

    session.pop("admin", None)

    return redirect(url_for("home"))


# ==============================
# DELETE STUDENT
# ==============================
@app.route("/delete_student/<student_id>", methods=["POST"])
def delete_student(student_id):

    if students_collection is not None:

        students_collection.delete_one({
            "_id": ObjectId(student_id)
        })

    return redirect(url_for("dashboard"))


# ==============================
# UNDO DELETE
# ==============================
@app.route("/undo_delete", methods=["POST"])
def undo_delete():

    data = request.json

    if students_collection is not None:
        students_collection.insert_one(data)

    return jsonify({"success": True})


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    app.run(debug=True)