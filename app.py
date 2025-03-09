from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Load user data (FIXED)
# Load user data
def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as file:
            try:
                data = json.load(file)
                if isinstance(data, dict) and "doctors" in data and "patients" in data:
                    return data  # Ensure expected structure
                else:
                    return {"doctors": [], "patients": []}
            except json.JSONDecodeError:
                return {"doctors": [], "patients": []}
    return {"doctors": [], "patients": []}


# Load patient appointment data (FIXED)
def load_appointments():
    if os.path.exists("patient-details.json"):
        with open("patient-details.json", "r") as file:
            try:
                data = json.load(file)
                if isinstance(data, list):
                    return data
                else:
                    return []
            except json.JSONDecodeError:
                return []
    return []


# Save user data
def save_users(users):
    with open("users.json", "w") as file:
        json.dump(users, file, indent=4)



# Save patient appointment data
def save_appointments(appointments):
    with open("patient-details.json", "w") as file:
        json.dump(appointments, file, indent=4)

# -------------------- LOGIN PAGE --------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user_type = request.form["user_type"]

        users = load_users()

        if user_type == "doctor":
            for doctor in users["doctors"]:
                if doctor["username"] == username and doctor["password"] == password:
                    session["username"] = username
                    session["user_type"] = "doctor"
                    return redirect(url_for("doctor_dashboard"))

        elif user_type == "patient":
            for patient in users["patients"]:
                if patient["username"] == username and patient["password"] == password:
                    session["username"] = username
                    session["user_type"] = "patient"
                    return redirect(url_for("patient_dashboard"))

        return "Invalid credentials. Try again!"

    return render_template("login.html")


# -------------------- PATIENT REGISTRATION --------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]
        contact = request.form["contact"]
        email = request.form["email"]

        users = load_users()

        # Check if username already exists
        for patient in users["patients"]:
            if patient["username"] == name:
                return "User already exists!"

        # Add new patient
        users["patients"].append({
            "username": name,
            "password": password,
            "contact": contact,
            "email": email
        })

        # Save updated user data
        with open("users.json", "w") as file:
            json.dump(users, file, indent=4)

        return redirect(url_for("login"))

    return render_template("register.html")


# -------------------- PATIENT DASHBOARD --------------------
@app.route("/patient-dashboard")
def patient_dashboard():
    if "username" not in session or session["user_type"] != "patient":
        return redirect(url_for("login"))

    username = session["username"]
    appointments = load_appointments()

    patient_appointments = [appt for appt in appointments if appt["name"] == username]
    completed_appointments = [appt for appt in patient_appointments if appt["status"] == "Completed"]

    return render_template("patient-dashboard.html", appointments=patient_appointments, completed_appointments=completed_appointments)

# -------------------- BOOK AN APPOINTMENT --------------------
@app.route("/book-appointment", methods=["POST"])
def book_appointment():
    if "username" not in session or session["user_type"] != "patient":
        return redirect(url_for("login"))

    username = session["username"]
    age = request.form["age"]
    symptoms = request.form["symptoms"]
    date = datetime.today().strftime('%Y-%m-%d')

    appointments = load_appointments()
    appointments.append({
        "name": username,
        "age": age,
        "symptoms": symptoms,
        "status": "Pending",
        "date": date
    })

    save_appointments(appointments)
    return redirect(url_for("patient_dashboard"))

# -------------------- DOCTOR DASHBOARD --------------------
@app.route("/doctor-dashboard")
def doctor_dashboard():
    if "username" not in session or session["user_type"] != "doctor":
        return redirect(url_for("login"))

    appointments = load_appointments()
    today_date = datetime.today().strftime('%Y-%m-%d')

    # Debugging
    print("Today's Date:", today_date)
    print("All Appointments:", appointments)

    # Normalize status comparison (convert to lowercase)
    today_cases = [appt for appt in appointments if appt["date"] == today_date and appt["status"].lower() == "pending"]
    print("Filtered Today's Cases:", today_cases)
    completed_cases = [appt for appt in appointments if appt["status"].lower() == "completed"]
    pending_cases = [appt for appt in appointments if appt["status"].lower() == "pending" and appt["date"] != today_date]

    # Debugging Output
    #print("Filtered Today's Cases:", today_cases)

    return render_template("doctors-dashboard.html", today_cases=today_cases, completed_cases=completed_cases, pending_cases=pending_cases)


# -------------------- UPDATE APPOINTMENT STATUS --------------------
@app.route("/update-status/<name>", methods=["POST"])
def update_status(name):
    if "username" not in session or session["user_type"] != "doctor":
        return redirect(url_for("login"))

    status = request.form["status"]
    appointments = load_appointments()

    for appt in appointments:
        if appt["name"] == name:
            appt["status"] = status

    save_appointments(appointments)
    return redirect(url_for("doctor_dashboard"))


@app.route("/mark_completed/<patient_name>", methods=["POST"])
def mark_completed(patient_name):
    appointments = load_appointments()
    
    for appointment in appointments:
        if appointment["name"] == patient_name and appointment["status"].lower() == "pending":
            appointment["status"] = "Completed"
            break  # Assuming only one match needs to be updated
    
    save_appointments(appointments)
    return redirect(url_for("patient_dashboard"))


# -------------------- LOGOUT --------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -------------------- RUN APPLICATION --------------------
if __name__ == "__main__":
    app.run(debug=True)
