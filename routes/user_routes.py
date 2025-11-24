from flask import Blueprint, render_template, request, redirect, session, flash
from flask_bcrypt import Bcrypt
from flask_mail import Message
from extensions import mysql, mail
from flask import current_app as app


bcrypt = Bcrypt()
user_routes = Blueprint('user_routes', __name__)

otp_storage = {}  # temporary OTP storage

# ---------------- REGISTER ----------------
@user_routes.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        phone = request.form['phone']
        address = request.form['address']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (name, email, password, phone, address) VALUES (%s,%s,%s,%s,%s)",
                    (name, email, password, phone, address))
        mysql.connection.commit()
        cur.close()

        flash("Registration Successful! Please Login.")
        return redirect("/login")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@user_routes.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_input = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.check_password_hash(user['password'], password_input):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            return redirect("/user/dashboard")
        else:
            flash("Invalid Credentials")

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@user_routes.route("/user/dashboard")
def user_dashboard():
    if 'user_id' not in session:
        return redirect("/login")
    return render_template("user_dashboard.html")

# ---------------- LOGOUT ----------------
@user_routes.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- FORGOT PASSWORD (OTP) ----------------
@user_routes.route("/forgot", methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        email = request.form['email']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if user:
            import random
            otp = random.randint(100000, 999999)
            otp_storage[email] = otp

            msg = Message("Your OTP Code", sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f"Your OTP to reset your password is: {otp}"
            mail.send(msg)

            flash("OTP sent to your email!")
            return redirect(f"/reset/{email}")
        else:
            flash("Email not found!")

    return render_template("forgot.html")

# ---------------- RESET PASSWORD ----------------
@user_routes.route("/reset/<email>", methods=['GET', 'POST'])
def reset(email):
    if request.method == 'POST':
        otp_entered = int(request.form['otp'])
        new_password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        if email in otp_storage and otp_storage[email] == otp_entered:
            cur = mysql.connection.cursor()
            cur.execute("UPDATE users SET password=%s WHERE email=%s", (new_password, email))
            mysql.connection.commit()
            cur.close()

            flash("Password reset successful!")
            return redirect("/login")
        else:
            flash("Invalid OTP!")

    return render_template("reset.html", email=email)
# ---------------- BOOK WASTE PICKUP ----------------
@user_routes.route("/book", methods=['GET', 'POST'])
def book():
    if 'user_id' not in session:
        return redirect("/login")

    if request.method == 'POST':
        waste_type = request.form['waste_type']
        weight = request.form['weight']
        location_lat = request.form['latitude']
        location_lng = request.form['longitude']

        # Price calculation:
        # biodegradable: 20 Rs
        # non-biodegradable: 30 Rs
        # recyclable: admin pays user

        if waste_type == "biodegradable":
            price = float(weight) * 2   # example: ₹2 per kg
        elif waste_type == "non-biodegradable":
            price = float(weight) * 3   # example: ₹3 per kg
        else:
            price = 0  # recyclable = free (admin pays user)

        user_id = session['user_id']

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO bookings 
            (user_id, waste_type, weight, price, location_lat, location_lng)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, waste_type, weight, price, location_lat, location_lng))
        mysql.connection.commit()
        cur.close()

        flash("Booking placed successfully!")
        return redirect("/user/dashboard")

    return render_template("book.html")

@user_routes.route("/track/<int:booking_id>")
def track(booking_id):
    if "user_id" not in session:
        return redirect("/login")

    return render_template("track_user.html", booking_id=booking_id)

# ---------------- USER PAYMENT ----------------
@user_routes.route("/pay/<int:booking_id>", methods=['GET', 'POST'])
def pay(booking_id):
    if "user_id" not in session:
        return redirect("/login")

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM bookings WHERE id=%s", (booking_id,))
    booking = cur.fetchone()

    if request.method == "POST":
        user_id = session['user_id']

        cur.execute("""
            INSERT INTO payments (booking_id, user_id, amount, payment_type, status)
            VALUES (%s, %s, %s, 'user_pay', 'completed')
        """, (booking_id, user_id, booking['price']))
        
        cur.execute("UPDATE bookings SET status='paid' WHERE id=%s", (booking_id,))
        mysql.connection.commit()
        cur.close()

        flash("Payment Successful!")
        return redirect("/user/dashboard")

    cur.close()
    return render_template("payment_user.html", booking=booking)
# ---------------- USER BOOKING HISTORY ----------------
@user_routes.route("/user/bookings")
def user_bookings():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT * FROM bookings 
        WHERE user_id=%s ORDER BY id DESC
    """, (user_id,))
    bookings = cur.fetchall()
    cur.close()

    return render_template("user_bookings.html", bookings=bookings)

