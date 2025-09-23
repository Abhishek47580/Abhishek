from flask import Flask, render_template, request, redirect, url_for, session
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend
import matplotlib.pyplot as plt
import io
import base64
from flask_mysqldb import MySQL
from barcode import QRcode
from datetime import date
from dayspassed import total_days_passed

app = Flask(__name__)

# App config
app.secret_key = 'abhishek'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'attan_manage'

# Initialize MySQL
con = MySQL(app)


# ---------- ROUTES ---------- #
#main routes
@app.route("/")
def home():
    return render_template("front/login.html")

#----- login interfaces-----#
@app.route("/register")
def register():
    return render_template("front/new-user.html")

@app.route("/check_user", methods=['POST'])
def login():
    role = request.form.get('role')
    username = request.form.get('username')
    password = request.form.get('password')

    data = [role, username, password]

    cur = con.connection.cursor()
    cur.execute("SELECT role, username, password FROM login_data WHERE username=%s", (username,))
    users = cur.fetchall()

    for user_row in users:
        if data == list(user_row):
            session['username']=username
            if role == "admin":
                cur.close()
                return redirect(url_for("admin"))
            elif role == "student":
                cur.close()
                return redirect(url_for("student_dashboard"))
            elif role == "teacher":
                cur.close()
                return redirect(url_for("teacher"))
            elif role == "counselor":
                cur.close()
                return redirect(url_for("home"))
        else:
            return redirect(url_for("home"))

    cur.close()


@app.route("/new_user", methods=['POST'])
def dbuser():
    try:
        role = request.form.get('role')
        username = request.form.get('username')
        password = request.form.get('password')
        c_password = request.form.get('c-password')

        if password != c_password:
            return "Passwords do not match", 400

        cur = con.connection.cursor()
        cur.execute("SELECT 1 FROM login_data WHERE username = %s", (username,))
        if cur.fetchone():
            cur.close()
            return "Username already exists", 400

        cur.execute("""
            INSERT INTO login_data (role, username, password, c_password)
            VALUES (%s, %s, %s, %s)
        """, (role, username, password, c_password))
        con.connection.commit()
        cur.close()
        return redirect(url_for("home"))

    except Exception as e:
        print("Error during /new_user:", str(e))
        return f"An error occurred: {e}", 500


@app.route("/profile", methods=['POST'])
def profile():
    try:
        role = request.form.get("role")
        cur = con.connection.cursor()

        if role == "admin":
            cur.execute("""
                INSERT INTO admin_profile(username,full_name,email,phone,password,account_status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                session.get('username'),
                request.form.get("full_name"),
                request.form.get("email"),
                request.form.get("phone"),
                request.form.get("address"),
                request.form.get("password"),
                request.form.get("account_status")
            ))

        elif role == "student":
            cur.execute("""
                INSERT into student_profile(username,full_name,gender,dob,phone,email,address,parent_name,parent_contact,
                class_name,roll_number,admission_number,section,year_of_admission,current_year)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s)
            """, (
                session.get('username'),
                request.form.get("full_name"),
                request.form.get("gender"),
                request.form.get("dob"),
                request.form.get("phone"),
                request.form.get("email"),
                request.form.get("address"),
                request.form.get("parent_name"),
                request.form.get("parent_contact"),
                request.form.get("class_name"),
                request.form.get("roll_number"),
                request.form.get("admission_number"),
                request.form.get("section"),
                request.form.get("year_of_admission"),
                request.form.get("current_year"),

            ))

        elif role == "teacher":
            cur.execute("""INSERT INTO teacher_profile(username,full_name,gender,dob,phone,email,address,qualification,
            experience_years,subject_specialization,department) 
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,(
                    session.get('username'),
                    request.form.get("full_name"),
                    request.form.get("gender"),
                    request.form.get("dob"),
                    request.form.get("phone"),
                    request.form.get("email"),
                    request.form.get("address"),
                    request.form.get("qualification"),
                    request.form.get("experience_years"),
                    request.form.get("subject_specialization"),
                    request.form.get("department")
            ))

        con.connection.commit()
        cur.close()
        return "Profile data was saved successfully"

    except Exception as e:
        print("Error during /profile:", str(e))
        return f"An error occurred: {e}", 500


#-----student interface-----#
@app.route("/student-dashboard")
def student_dashboard():
    username = session.get('username')
    cur=con.connection.cursor()
    cur.execute("""SELECT * from student_profile where username=%s""",(username,))
    data=list(cur.fetchall())
    
    check_d=False
    if not data:
        print("empty")
    else:
        check_d=True


    # this has to done in every dashboard
    if not username:
        return redirect(url_for("home"))

    start_date = date(2025, 3, 5)
    total_days = total_days_passed(start_date)

    cur.execute("SELECT present FROM login_data WHERE username=%s", (username,))
    total_day_present = cur.fetchone()
    if total_day_present is None:
        cur.close()
        return "No attendance data found", 404

    present_per = (total_day_present[0] / total_days) * 100
    absent_per = 100 - present_per

    # Generate pie chart
    count = [present_per, absent_per]
    labels = ["Present", "Absent"]
    plt.pie(count, labels=labels)
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format="png")
    img_buffer.seek(0)
    chart_data = base64.b64encode(img_buffer.read()).decode('utf-8')
    plt.close()

    # Generate QR code
    qr = QRcode(username)

    cur.close()
    return render_template("students/dashboard.html", chart=chart_data, qr_code=qr, user=username,check=check_d)

@app.route("/student-profile")
def student_profile():
    username=session.get('username')
    cur=con.connection.cursor()
    cur.execute("""SELECT * from student_profile where username=%s""",(username,))
    data=list(cur.fetchall())
    print(data)
    cur.close()
    return render_template("students/sprofile.html",user=username,data=data)



#-----teacher interfaces-----#
@app.route("/teacher-dashboard")
def teacher():
    username = session.get('username')
    cur=con.connection.cursor()
    cur.execute("""SELECT * from student_profile where username=%s""",(username,))
    data=list(cur.fetchall())
    check_d=False
    if not data:
        print("empty")
    else:
        check_d=True


    # this has to done in every dashboard
    if not username:
        return redirect(url_for("home"))

    start_date = date(2025, 3, 5)
    total_days = total_days_passed(start_date)

    cur.execute("SELECT present FROM login_data WHERE username=%s", (username,))
    total_day_present = list(cur.fetchone())
    if total_day_present is None:
        cur.close()
        return "No attendance data found", 404
    print(total_day_present)
    present_per = (total_day_present[0] / total_days) * 100
    absent_per = 100 - present_per

    # Generate pie chart
    count = [present_per, absent_per]
    labels = ["Present", "Absent"]
    plt.pie(count, labels=labels)
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format="png")
    img_buffer.seek(0)
    chart_data = base64.b64encode(img_buffer.read()).decode('utf-8')
    plt.close()

    # Generate QR code
    qr = QRcode(username)

    cur.close()
    return render_template("teacher/dashboard.html",user=username,check=check_d,qr_code=qr,chart=chart_data)

@app.route("/teacher-profile")
def teacher_profile():
    username=session.get('username')
    cur=con.connection.cursor()
    cur.execute("""SELECT * from teacher_profile where username=%s""",(username,))
    data=list(cur.fetchall())
    cur.close()
    return render_template("teacher/tprofile.html",user=username,data=data)

#-----admin interfaces-----#
@app.route("/admin-dashboard")
def admin():
    username = session.get('username')
    cur=con.connection.cursor()
    cur.execute("""SELECT * from student_profile where username=%s""",(username,))
    data=list(cur.fetchall())
    check_d=False
    if not data:
        print("empty")
    else:
        check_d=True


    # this has to done in every dashboard
    if not username:
        return redirect(url_for("home"))

    start_date = date(2025, 3, 5)
    total_days = total_days_passed(start_date)

    cur.execute("SELECT present FROM login_data WHERE username=%s", (username,))
    total_day_present = list(cur.fetchone())
    if total_day_present is None:
        cur.close()
        return "No attendance data found", 404
    print(total_day_present)
    present_per = (total_day_present[0] / total_days) * 100
    absent_per = 100 - present_per

    # Generate pie chart
    count = [present_per, absent_per]
    labels = ["Present", "Absent"]
    plt.pie(count, labels=labels)
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format="png")
    img_buffer.seek(0)
    chart_data = base64.b64encode(img_buffer.read()).decode('utf-8')
    plt.close()

    # Generate QR code
    qr = QRcode(username)
    cur.close()
    return render_template("admin/dashboard.html",user=username,check=check_d,qr_code=qr,chart=chart_data)


@app.route("/admin-profile")
def admin_profile():
    username=session.get('user')
    cur=con.connection.cursor()
    cur.execute("""SELECT * from admin_profile where username=%s""",(username,))
    data=list(cur.fetchall())
    cur.close()
    return render_template("admin/aprofile.html",data=data)



# ---------- MAIN ---------- #
if __name__ == "__main__":
    app.run(debug=True)
