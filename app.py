import email
from flask import Flask, render_template, request, redirect, session, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from dotenv import load_dotenv
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
import pandas as pd
from flask import send_file
import random
from flask import session

load_dotenv()

app = Flask(__name__)

app.secret_key = "my_secret_key_123"

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=False)
    otp_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Enquiry(db.Model):
    __tablename__ = 'enquiries'

    id = db.Column(db.Integer, primary_key=True)

    customer_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(255), nullable=False)

    address = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)

    product_requirement = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    customer_note = db.Column(
    db.Text,
    nullable=True
)

    status = db.Column(
    db.String(20),
    default="New"
)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def send_confirmation_email(customer_email, customer_name):

    print("Sending email to:", customer_email)
    subject = "Enquiry Received"

    body = f"""
Hello {customer_name},

Thank you for contacting us.

We have received your enquiry successfully.

Our team will contact you shortly.

Regards,
Lead Generation Team
"""

    msg = MIMEText(body)

    msg["Subject"] = subject
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = customer_email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()

    server.login(
        os.getenv("EMAIL_USER"),
        os.getenv("EMAIL_PASSWORD")
    )

    server.send_message(msg)
    server.quit()

def send_otp_email(customer_email, otp):

    print("SENDING OTP TO:", customer_email)
    print("OTP VALUE:", otp)

    try:

        subject = "Email Verification OTP"

        body = f"""
Hello,

Your OTP for verification is:

{otp}

This OTP is valid for one use only.

Regards,
Lead Generation Team
"""

        msg = MIMEText(body)

        msg["Subject"] = subject
        msg["From"] = os.getenv("EMAIL_USER")
        msg["To"] = customer_email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()

        print("LOGGING IN...")

        server.login(
            os.getenv("EMAIL_USER"),
            os.getenv("EMAIL_PASSWORD")
        )

        print("LOGIN SUCCESS")

        server.send_message(msg)

        print("EMAIL SENT SUCCESSFULLY")

        server.quit()

    except Exception as e:
        print("EMAIL ERROR:", e)


def send_client_notification(
    name,
    phone,
    email,
    address,
    category,
    product_requirement,
    quantity
):

    print("CLIENT EMAIL =", os.getenv("CLIENT_EMAIL"))

    subject = "New Lead Received"

    body = f"""
New enquiry received

Name: {name}

Phone: {phone}

Email: {email}

Address: {address}

Category: {category}

Product Requirement: {product_requirement}

Quantity: {quantity}

Please contact the customer.
"""

    msg = MIMEText(body)

    msg["Subject"] = subject
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = os.getenv("CLIENT_EMAIL")

    server = smtplib.SMTP("smtp.gmail.com", 587)

    server.starttls()

    server.login(
        os.getenv("EMAIL_USER"),
        os.getenv("EMAIL_PASSWORD")
    )

    server.send_message(msg)

    server.quit()

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        session.clear()


    name = None
    phone = None
    email = None
    address = None
    category = None
    product_requirement = None
    customer_note = None
    quantity = None

    otp_verified = session.get("otp_verified", False)

    if request.method == "POST":

        name = request.form.get("name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        otp = request.form.get("otp")

        print("EMAIL =", email)
        print("OTP =", otp)

        print("EMAIL CHECK =", email)
        print("SESSION OTP =", session.get("otp"))
        print("SESSION VERIFIED =", session.get("otp_verified"))

        if email and not session.get("otp_verified") and not session.get("otp"):

            print("ENTERED OTP GENERATION BLOCK")

            generated_otp = str(random.randint(100000, 999999))

            session["otp"] = generated_otp

            print("OTP =", generated_otp)

            send_otp_email(
                email,
                generated_otp
            )

        address = request.form.get("address")
        category = request.form.get("category")
        print("CATEGORY =", category)

        product_requirement = request.form.get("product_requirement")
        quantity = request.form.get("quantity")
        customer_note = request.form.get("customer_note")

        print("Customer Note =", customer_note)

        if otp and otp == session.get("otp"):
            otp_verified = True
            session["otp_verified"] = True

        if quantity and customer_note is not None:

            enquiry = Enquiry(
                customer_name=name,
                phone=phone,
                email=email,
                address=address,
                category=category,
                product_requirement=product_requirement,
                quantity=int(quantity),
                customer_note=customer_note
            )

            db.session.add(enquiry)
            db.session.commit()

            send_confirmation_email(
                email,
                name
            )

            send_client_notification(
                name,
                phone,
                email,
                address,
                category,
                product_requirement,
                quantity
            )

            print("Enquiry saved successfully!")

            session.pop("otp", None)
            session.pop("otp_verified", None)

            return redirect("/thankyou")

        return render_template(
            "index.html",
            name=name,
            phone=phone,
            email=email,
            address=address,
            category=category,
            product_requirement=product_requirement,
            quantity=quantity,
            otp_verified=otp_verified,
            customer_note=customer_note
        )

    return render_template("index.html")




@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin123":

            session["admin_logged_in"] = True

            return redirect("/admin")

    return render_template("admin_login.html")

@app.route("/admin")
def admin():

    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    search = request.args.get("search")

    if search:

        enquiries = Enquiry.query.filter(
            (Enquiry.customer_name.ilike(f"%{search}%")) |
            (Enquiry.phone.ilike(f"%{search}%")) |
            (Enquiry.email.ilike(f"%{search}%"))
        ).all()

    else:

        enquiries = Enquiry.query.filter(
            Enquiry.status != "Delivered"
        ).order_by(
            Enquiry.created_at.desc()
        ).all()

    total_enquiries = Enquiry.query.count()

    chocolate_count = Enquiry.query.filter_by(
        category="Chocolates"
    ).count()

    fragrance_count = Enquiry.query.filter_by(
        category="Fragrances"
    ).count()

    return render_template(
        "admin.html",
        enquiries=enquiries,
        total_enquiries=total_enquiries,
        chocolate_count=chocolate_count,
        fragrance_count=fragrance_count
    )

@app.route("/delivered-orders")
def delivered_orders():

    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    enquiries = Enquiry.query.filter_by(
        status="Delivered"
    ).order_by(
        Enquiry.created_at.desc()
    ).all()

    return render_template(
        "delivered_orders.html",
        enquiries=enquiries
    )

@app.route("/delivered/<int:id>")
def delivered(id):

    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    enquiry = Enquiry.query.get_or_404(id)

    enquiry.status = "Delivered"

    db.session.commit()

    return redirect("/admin")

@app.route("/analytics")
def analytics():

    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    total_orders = Enquiry.query.count()

    delivered_orders = Enquiry.query.filter_by(
        status="Delivered"
    ).count()

    pending_orders = Enquiry.query.filter(
        Enquiry.status != "Delivered"
    ).count()

    chocolate_orders = Enquiry.query.filter_by(
        category="Chocolates"
    ).count()

    fragrance_orders = Enquiry.query.filter_by(
        category="Fragrances"
    ).count()
    
    daily_orders = db.session.query(
    func.date(Enquiry.created_at),
    func.count(Enquiry.id)
    ).group_by(
    func.date(Enquiry.created_at)
    ).all()

    dates = [str(item[0]) for item in daily_orders]

    counts = [item[1] for item in daily_orders]
    return render_template(
        "analytics.html",
        total_orders=total_orders,
        delivered_orders=delivered_orders,
        pending_orders=pending_orders,
        chocolate_orders=chocolate_orders,
        fragrance_orders=fragrance_orders,
        dates=dates,
        counts=counts
    )


@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route("/thankyou")
def thankyou():
    return render_template("thankyou.html")


@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect("/admin/login")

@app.route("/export")
def export():

    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    enquiries = Enquiry.query.all()

    data = []

    for enquiry in enquiries:

        data.append({
            "Name": enquiry.customer_name,
            "Phone": enquiry.phone,
            "Email": enquiry.email,
            "Address": enquiry.address,
            "Category": enquiry.category,
            "Requirement": enquiry.product_requirement,
            "Quantity": enquiry.quantity,
            "Date": enquiry.created_at
        })

    df = pd.DataFrame(data)

    file_name = "enquiries.xlsx"

    df.to_excel(file_name, index=False)

    return send_file(
        file_name,
        as_attachment=True
    )

@app.route("/enquiry/<int:id>")
def enquiry_details(id):

    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    enquiry = Enquiry.query.get_or_404(id)

    return render_template(
        "enquiry_details.html",
        enquiry=enquiry,
    )

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Tables created successfully!")
    app.run(debug=True)