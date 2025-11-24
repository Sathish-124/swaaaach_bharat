from flask import Blueprint, render_template, request, redirect, session, flash
from extensions import mysql
from flask import current_app as app


rider_routes = Blueprint('rider_routes', __name__)

# ---------------- RIDER LOGIN ----------------
@rider_routes.route("/rider/login", methods=["GET", "POST"])
def rider_login():
    if request.method == "POST":
        phone = request.form["phone"]

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM riders WHERE phone=%s", (phone,))
        rider = cur.fetchone()
        cur.close()

        if rider:
            session["rider_id"] = rider["id"]
            session["rider_name"] = rider["name"]
            return redirect("/rider/dashboard")
        else:
            flash("Rider not found!")

    return render_template("rider_login.html")


# ---------------- RIDER DASHBOARD ----------------
@rider_routes.route("/rider/dashboard")
def rider_dashboard():
    if "rider_id" not in session:
        return redirect("/rider/login")

    rider_id = session["rider_id"]

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM bookings WHERE rider_id=%s AND status='assigned'", (rider_id,))
    job = cur.fetchone()
    cur.close()

    return render_template("rider_dashboard.html", job=job)


# ---------------- UPDATE RIDER STATUS ----------------
@rider_routes.route("/rider/update_status/<int:booking_id>/<string:new_status>")
def update_status(booking_id, new_status):
    if "rider_id" not in session:
        return redirect("/rider/login")

    cur = mysql.connection.cursor()
    cur.execute("UPDATE bookings SET status=%s WHERE id=%s", (new_status, booking_id))
    mysql.connection.commit()
    cur.close()

    flash(f"Status updated to: {new_status}")
    return redirect("/rider/dashboard")


# ---------------- UPDATE RIDER LOCATION ----------------
@rider_routes.route("/rider/update_location", methods=["POST"])
def update_location():
    if "rider_id" not in session:
        return "Unauthorized", 401

    rider_id = session["rider_id"]
    lat = request.form["latitude"]
    lng = request.form["longitude"]

    cur = mysql.connection.cursor()
    cur.execute("UPDATE riders SET location_lat=%s, location_lng=%s WHERE id=%s",
                (lat, lng, rider_id))
    mysql.connection.commit()
    cur.close()

    return "Location updated"
