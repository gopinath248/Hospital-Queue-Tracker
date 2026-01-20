from flask import Flask, render_template, request, redirect, session, jsonify
import psycopg2
import psycopg2.extras
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.secret_key = "hospital_secret_key"

# ================= DATABASE CONNECTION =================
def get_db():
    return psycopg2.connect(
        host="localhost",
        database="hospital_Db",
        user="postgres",
        password="amma123"
    )

def get_queue_table(department):
    tables = {
        "Cardiology": "cardio_queue",
        "Dental": "dental_queue",
        "Dermatology": "derma_queue",
        "ENT": "ent_queue",
        "General": "general_queue"
    }
    return tables.get(department)

# ================= HOME =================
@app.route("/")
def main():
    return render_template("main.html")

@app.route("/About")
def About():
    return render_template("About.html")

@app.route('/favicon.ico')
def favicon():
    return '', 204

# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role")
        username = request.form.get("username")
        password = request.form.get("password")
        department = request.form.get("department")

        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # --- ADMIN LOGIN ---
        if role.lower() == "admin":
            cur.execute("SELECT * FROM users WHERE username=%s AND password=%s AND role='Ent'",
                        (username,password))
            admin = cur.fetchone()
            conn.close()
            if admin:
                session["role"]="admin"
                session["username"]=username
                session["password"]=password
                return redirect("/admin/dashboard")
            else:
                return render_template("login.html",error="Invalid admin login.")

        # --- USER LOGIN ---
        elif role.lower() == "user":
            cur.execute("SELECT * FROM users WHERE username=%s AND password=%s AND role='user'",
                        (username,password))
            user = cur.fetchone()
            conn.close()
            if user:
                session["role"]="user"
                session["username"]=username
                session["password"]=password
                session["department"]=department
                return redirect("/user/dashboard")
            else:
                return render_template("login.html",error="Invalid user login.")

        # --- DOCTOR LOGIN ---
        elif role.lower() == "doctors":
            # check if doctor credentials match admin
            cur.execute("SELECT * FROM users WHERE username=%s AND password=%s AND role='admin'",
                        (username,password))
            admin_as_doc = cur.fetchone()
            if admin_as_doc:
                conn.close()
                session["role"]="admin"
                session["username"]=username
                return redirect("/admin/dashboard")

            # normal doctor check
            cur.execute("SELECT * FROM doctors WHERE username=%s AND password=%s AND department=%s",
                        (username,password,department))
            doctor = cur.fetchone()
            conn.close()
            if doctor:
                session["role"]="doctors"
                session["username"]=username
                session["department"]=department
                return redirect(f"/doctors/{department}/dashboard")
            else:
                return render_template("login.html",error="Invalid doctor login.")

        else:
            conn.close()
            return render_template("login.html",error="Invalid role.")

    return render_template("login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role")!="admin":
        return redirect("/login")

    conn=get_db()
    cur=conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM users ORDER BY id")
    users=cur.fetchall()
    cur.execute("SELECT * FROM doctors ORDER BY id")
    doctors=cur.fetchall()
    conn.close()

    return render_template("admin-dashboard.html",users=users,doctors=doctors)
@app.route("/get_token", methods=["POST"])
def get_token():
    if session.get("role") != "user":
        return jsonify({"status": "error", "error": "Unauthorized"}), 401

    name = request.form["name"]
    phone = request.form["phone"]
    problem = request.form["problem"]
    department = request.form["department"]
    table = get_queue_table(department)

    if not table:
        return jsonify({"status": "error", "error": "Invalid department"}), 400

    conn = get_db()
    cur = conn.cursor()

    # Generate next token
    cur.execute(f"SELECT COALESCE(MAX(token), 0) FROM {table}")
    new_token = cur.fetchone()[0] + 1

    # Insert patient into department queue

    cur.execute(
        f"INSERT INTO {table} (name, phone, problem, token, status) VALUES (%s, %s, %s, %s, 'waiting')",
    (name, phone, problem, new_token)
 
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "token": new_token})

# ================= QUEUE STATUS =================
@app.route("/queue_status/<department>")
def queue_status(department):
    table = get_queue_table(department)
    if not table:
        return jsonify({"error": "Invalid department"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table} WHERE status='waiting'")
    waiting = cur.fetchone()[0]
    conn.close()
    return jsonify({"department": department, "waiting": waiting})

@app.route("/queues_status")
def queues_status():
    data = {}
    conn = get_db()
    cur = conn.cursor()
    for dept, table in {
        "Cardiology": "cardio_queue",
        "Dental": "dental_queue",
        "Dermatology": "derma_queue",
        "ENT": "ent_queue",
        "General": "general_queue"
    }.items():
        cur.execute(f"SELECT COUNT(*) FROM {table} WHERE status='waiting'")
        data[dept] = cur.fetchone()[0]
    conn.close()
    return jsonify(data)

# ================= DOCTORS DASHBOARD =================
@app.route("/doctors/<department>/dashboard")
def doctor_dashboard(department):
    if session.get("role") != "doctors":
        return redirect("/login")
    table=get_queue_table(department)
    conn=get_db()
    cur=conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(f"SELECT * FROM {table} ORDER BY token")
    patients=cur.fetchall()
    conn.close()

    return render_template("doctors-dashboard.html",
                           username=session["username"],
                           department=department,
                           patients=patients)

@app.route("/doctors/<department>/patients")
def doctor_patients(department):
    if session.get("role") != "doctors":
        return jsonify([])
    table = get_queue_table(department)
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(f"SELECT * FROM {table} ORDER BY token")
    patients = cur.fetchall()
    conn.close()
    return jsonify(patients)

@app.route("/doctor/call_patient", methods=["POST"])
def call_patient():
    if session.get("role") != "doctors":
        return jsonify({"status": "error"}), 401

    token = request.form["token"]
    department = session.get("department")
    table = get_queue_table(department)

    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE {table} SET status='called' WHERE token=%s", (token,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})

@app.route("/user/dashboard")
def user_dashboard():
    if session.get("role") != "user":
        return redirect("/login")
    return render_template("user-dashboard.html", username=session["username"])
@app.route("/doctor/complete_patient", methods=["POST"])
def complete_patient():
    if session.get("role") != "doctors":
        return jsonify({"status": "error"}), 401

    token = request.form["token"]
    department = session.get("department")
    table = get_queue_table(department)

    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE {table} SET status='completed' WHERE token=%s", (token,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})
@app.route("/doctor/followup", methods=["POST"])
def followup_patient():
    if session.get("role") != "doctors":
        return jsonify({"status": "error"}), 401

    token = request.form["token"]
    followup_date = request.form["followup_date"]
    department = session.get("department")
    table = get_queue_table(department)

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        f"UPDATE {table} SET status='followup', followup_date=%s WHERE token=%s",
        (followup_date, token)
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})

@app.route("/live_status")
def live_status():
    if session.get("role") != "user":
        return jsonify({"status": "error", "error": "Unauthorized"}), 401

    department = session.get("department")
    table = get_queue_table(department)

    if not table:
        return jsonify({"status": "error", "error": "Department not set"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table} WHERE status='waiting'")
    waiting = cur.fetchone()[0]
    conn.close()

    return jsonify({"waiting": waiting})

@app.route("/get_token", methods=["POST"])
def get_token_with_position():
    if session.get("role") != "user":
        return jsonify({"status": "error", "error": "Unauthorized"}), 401

    name = request.form["name"]
    phone = request.form["phone"]
    problem = request.form["problem"]
    department = request.form["department"]
    table = get_queue_table(department)

    if not table:
        return jsonify({"status": "error", "error": "Invalid department"}), 400

    conn = get_db()
    cur = conn.cursor()

    # Generate next token
    cur.execute(f"SELECT COALESCE(MAX(token), 0) FROM {table}")
    new_token = cur.fetchone()[0] + 1

    # Insert patient into department queue
    cur.execute(
        f"INSERT INTO {table} (name, phone, problem, token, status) VALUES (%s, %s, %s, %s, 'waiting')",
        (name, phone, problem, new_token)
    )

    # Count before and after
    cur.execute(f"SELECT COUNT(*) FROM {table} WHERE token < %s", (new_token,))
    before = cur.fetchone()[0]
    cur.execute(f"SELECT COUNT(*) FROM {table} WHERE token > %s", (new_token,))
    after = cur.fetchone()[0]

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "token": new_token,
        "before": before,
        "after": after
    })

# ================= ADMIN VIEW ALL QUEUES =================
@app.route("/admin/queues")
def admin_queues():
    if session.get("role") != "admin":
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    data = {}
    for dept, table in {
        "Cardiology": "cardio_queue",
        "Dental": "dental_queue",
        "Dermatology": "derma_queue",
        "ENT": "ent_queue",
        "General": "general_queue"
    }.items():
        cur.execute(f"SELECT * FROM {table} ORDER BY token")
        data[dept] = cur.fetchall()
    conn.close()
    return render_template("admin-queues.html", queues=data)

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True) 