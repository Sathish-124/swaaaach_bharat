from flask import Blueprint, render_template, request, redirect, session, flash
from flask_bcrypt import Bcrypt
from extensions import mysql
from flask import current_app as app


admin_routes = Blueprint('admin_routes', __name__)

bcrypt = Bcrypt()

# ---------- ADMIN LOGIN ----------
@admin_routes.route("/admin/login", methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password_input = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM admins WHERE email=%s", (email,))
        admin = cur.fetchone()
        cur.close()

        if admin and bcrypt.check_password_hash(admin['password'], password_input):
            session['admin_id'] = admin['id']
            session['admin_email'] = admin['email']
            return redirect("/admin/dashboard")
        else:
            flash("Invalid admin credentials")

    return render_template("admin_login.html")


# ---------- ADMIN DASHBOARD ----------
@admin_routes.route("/admin/dashboard")
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect("/admin/login")

    return render_template("admin_dashboard.html")


# ---------- ADMIN LOGOUT ----------
@admin_routes.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/admin/login")
# ---------------- VIEW ALL BOOKINGS ----------------
@admin_routes.route("/admin/manage_bookings")
def manage_bookings():
    if 'admin_id' not in session:
        return redirect("/admin/login")

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT bookings.*, users.name AS user_name, users.phone AS user_phone 
        FROM bookings
        JOIN users ON bookings.user_id = users.id
        ORDER BY bookings.id DESC
    """)
    bookings = cur.fetchall()
    cur.close()

    return render_template("admin_bookings.html", bookings=bookings)


# ---------------- ASSIGN RIDER ----------------
@admin_routes.route("/admin/assign/<int:booking_id>", methods=['GET', 'POST'])
def assign_rider(booking_id):
    if 'admin_id' not in session:
        return redirect("/admin/login")

    cur = mysql.connection.cursor()

    # fetch available riders
    cur.execute("SELECT * FROM riders WHERE status='available'")
    riders = cur.fetchall()

    if request.method == 'POST':
        rider_id = request.form['rider_id']

        # update booking + rider status
        cur.execute("UPDATE bookings SET rider_id=%s, status='assigned' WHERE id=%s", (rider_id, booking_id))
        cur.execute("UPDATE riders SET status='busy' WHERE id=%s", (rider_id,))
        mysql.connection.commit()

        cur.close()

        flash("Rider assigned successfully!")
        return redirect("/admin/manage_bookings")

    # get booking details
    cur.execute("SELECT * FROM bookings WHERE id=%s", (booking_id,))
    booking = cur.fetchone()
    cur.close()

    return render_template("assign_rider.html", booking=booking, riders=riders)
# ---------------- GET RIDER LOCATION (Admin + User) ----------------
@admin_routes.route("/get_rider_location/<int:rider_id>")
def get_rider_location(rider_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT location_lat, location_lng FROM riders WHERE id=%s", (rider_id,))
    data = cur.fetchone()
    cur.close()

    return {"lat": data["location_lat"], "lng": data["location_lng"]}
# ---------------- ADMIN PAY USER FOR RECYCLABLE WASTE ----------------
@admin_routes.route("/admin/pay_user/<int:booking_id>", methods=['GET', 'POST'])
def admin_pay_user(booking_id):
    if "admin_id" not in session:
        return redirect("/admin/login")

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM bookings WHERE id=%s", (booking_id,))
    booking = cur.fetchone()

    if request.method == "POST":
        user_id = booking['user_id']
        amount = float(booking['weight']) * 5   # admin pays ₹5 per kg

        cur.execute("""
            INSERT INTO payments (booking_id, user_id, amount, payment_type, status)
            VALUES (%s, %s, %s, 'admin_pay', 'completed')
        """, (booking_id, user_id, amount))

        cur.execute("UPDATE bookings SET status='completed' WHERE id=%s", (booking_id,))
        mysql.connection.commit()
        cur.close()

        flash("Admin payment completed!")
        return redirect("/admin/manage_bookings")

    cur.close()
    return render_template("payment_admin.html", booking=booking, pay_amount=float(booking['weight']) * 5)

# ---------------- VIEW ALL USERS ----------------
@admin_routes.route("/admin/users")
def admin_users():
    if 'admin_id' not in session:
        return redirect("/admin/login")

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users ORDER BY id DESC")
    users = cur.fetchall()
    cur.close()

    return render_template("admin_users.html", users=users)




# ---------------- VIEW ALL RIDERS ----------------
@admin_routes.route("/admin/riders")
def admin_riders():
    if 'admin_id' not in session:
        return redirect("/admin/login")

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM riders ORDER BY id DESC")
    riders = cur.fetchall()
    cur.close()

    return render_template("admin_riders.html", riders=riders)

# ---------------- ADD RIDER ----------------
@admin_routes.route("/admin/add_rider", methods=['GET', 'POST'])
def add_rider():
    if 'admin_id' not in session:
        return redirect("/admin/login")

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO riders (name, phone, status) VALUES (%s, %s, 'available')",
                    (name, phone))
        mysql.connection.commit()
        cur.close()

        flash("Rider added successfully!")
        return redirect("/admin/riders")

    return render_template("add_rider.html")

# ---------------- VIEW PAYMENTS ----------------
@admin_routes.route("/admin/payments")
def admin_payments():
    if 'admin_id' not in session:
        return redirect("/admin/login")

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT payments.*, users.name AS user_name 
        FROM payments 
        JOIN users ON payments.user_id = users.id
        ORDER BY payments.id DESC
    """)
    payments = cur.fetchall()
    cur.close()

    return render_template("admin_payments.html", payments=payments)


# ---------------- STATISTICS ----------------
@admin_routes.route("/admin/stats")
def admin_stats():
    if 'admin_id' not in session:
        return redirect("/admin/login")

    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) AS total FROM bookings")
    total = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) AS pending FROM bookings WHERE status='pending'")
    pending = cur.fetchone()['pending']

    cur.execute("SELECT COUNT(*) AS completed FROM bookings WHERE status='completed'")
    completed = cur.fetchone()['completed']

    cur.close()

    return render_template("admin_stats.html",
                           total=total,
                           pending=pending,
                           completed=completed)
