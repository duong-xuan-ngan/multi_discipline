"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import Flask, redirect, render_template, request, session, url_for, jsonify, flash
from flask_session import Session
from Multi_Project import app
import pandas as pd
import os
import csv
import json
import re


app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)






@app.route("/")
def index():
    return render_template("Login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        if not email or not password:
            flash("Please enter both email and password.")
            return redirect(url_for("index"))
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid email format.")
            return redirect(url_for("index"))
        
        user = check_user_credentials(email, password)
        if user:
            session["email"] = email
            return redirect(url_for("mainpage"))
        else:
            flash("Wrong email or password")
            return redirect(url_for("index"))
    
    return redirect(url_for("index"))

def check_user_credentials(email, password):
    try:
        with open('user.csv', 'r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                if row['username'] == email and row['password'] == password:
                    return True
    except FileNotFoundError:
        print("User database file not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return False

@app.route("/mainpage", methods=["GET"])
def mainpage():
    return render_template("Mainpage.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        # Check if email already exists
        if email_exists(email):
            return jsonify({"success": False, "message": "Email already exists"})
        # Validate password
        if not is_valid_password(password):
            return jsonify({"success": False, "message": "Invalid password"})
        # Add user to CSV
        add_user_to_csv(email, password)
        return jsonify({"success": True})
@app.route("/check_email", methods=["POST"])
def check_email():
    email = request.form.get("email")
    exists = email_exists(email)
    return jsonify({"exists": exists})
def email_exists(email):
   def email_exists(email):
    try:
        with open('user.csv', 'r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                if row['username'] == email:
                    return True
    except FileNotFoundError:
        # If the file doesn't exist, create it with a header
        with open('user.csv', 'w', newline='') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow(['username', 'password'])
    except Exception as e:
        print(f"An error occurred: {e}")

    return False
def is_valid_password(password):
    return len(password) >= 8 and re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
def add_user_to_csv(email, password):
    file_exists = os.path.isfile('user.csv')

    with open('user.csv', 'a', newline='') as file:
        csv_writer = csv.writer(file)
        if not file_exists:
            csv_writer.writerow(['username', 'password'])  # Write header if file is new
        csv_writer.writerow([email, password])


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        return render_template("forgot_password.html")
    elif request.method == "POST":
        email = request.form.get("email")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not email or not new_password or not confirm_password:
            flash("Please fill in all fields.")
            return redirect(url_for("forgot_password"))

        if new_password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("forgot_password"))

        if not is_valid_password(new_password):
            flash("Password must be at least 8 characters long and contain at least one special character.")
            return redirect(url_for("forgot_password"))

        if reset_password(email, new_password):
            flash("Password reset successful. Please login with your new password.")
            return redirect(url_for("login"))
        else:
            flash("Account not found.")
            return redirect(url_for("forgot_password"))

def reset_password(email, new_password):
    users = []
    found = False
    try:
        with open('user.csv', 'r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                if row['username'] == email:
                    row['password'] = new_password
                    found = True
                users.append(row)
        
        if found:
            with open('user.csv', 'w', newline='') as file:
                fieldnames = ['username', 'password']
                csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
                csv_writer.writeheader()
                csv_writer.writerows(users)
            return True
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return False


@app.route("/application")
def application():
    # Read the CSV device file
    device_location = os.path.dirname(os.path.abspath(__file__))
    device_path = os.path.join(device_location, 'device.csv')
    device = pd.read_csv(device_path, skiprows=1)
    gps_data_device = []
    
    # Read the CSV human file
    human_location = os.path.dirname(os.path.abspath(__file__))
    human_path = os.path.join(human_location, 'monitoring.csv')
    human = pd.read_csv(human_path, skiprows=1)
    gps_data_human = []
    
    # Iterate for each human position
    for index, row in human.iterrows():
        timestamps = row[0]
        data_lat = row[1]
        data_lon = row[2]
        truncated_timestamp = timestamps[:26] + 'Z'
        dt = datetime.strptime(truncated_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
        date = dt.date()
        time = dt.time()
        # Clean and convert lat and lon values to float
        lat = float(data_lat.replace('{"lat":', ''))
        lon = float(data_lon.replace('lon:', '').replace('}', ''))
        
        gps_data_human.append({'timestamp': timestamps, 'date': str(date), 'time': str(time),'lat': lat, 'lng': lon})
    
    # Iterate for each device position
    for index, row in device.iterrows():
        data_lat = row[1]
        data_lon = row[2]    
        # Clean and convert lat and lon values to float
        lat = float(data_lat.replace('{"lat":', ''))
        lon = float(data_lon.replace('lon:', '').replace('}', ''))
        
        gps_data_device.append({'lat': lat, 'lng': lon})        
    return render_template("application.html", human_journey=json.dumps(gps_data_human), device_journey=json.dumps(gps_data_device))

@app.route("/about", methods=["GET"])
def about():
    return render_template("about.html")

@app.route("/feedback", methods=["GET"])
def feedback():
    return render_template("feedback.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))  # Redirect to index after logout

if __name__ == "__main__":
    app.run(debug=True)