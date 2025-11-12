from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import json
import docx2txt
import pdfplumber
import zipfile
from werkzeug.security import generate_password_hash, check_password_hash
from resume_parser import parse_resume
from matcher import match_job_to_candidates, suggest_improvements

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Folder for uploaded files
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Dummy credentials
FAKE_USERNAME = "admin"
FAKE_PASSWORD = "password123"

# Users file (simple JSON store for demo purposes)
USERS_FILE = os.path.join(app.root_path, "users.json")


def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_users(users):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2)
    except Exception:
        pass


# ---------- Helper Functions ----------
def extract_text(file_path):
    """Extracts text content from PDF, DOCX, or TXT files."""
    text = ""
    if file_path.endswith(".pdf"):
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        except Exception:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() or ""
    elif file_path.endswith(".docx"):
        text = docx2txt.process(file_path) or ""
    elif file_path.endswith(".txt"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read() or ""
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as f:
                text = f.read() or ""
    return text


# ---------- Authentication Helper ----------
def login_required(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper


# ---------- Routes ----------
@app.route("/")
def home():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/index")
def index():
    """Alias route for templates that expect an 'index' endpoint."""
    return home()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Check admin demo account first
        if username == FAKE_USERNAME and password == FAKE_PASSWORD:
            session["logged_in"] = True
            session["username"] = username
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard"))

        # Then check persisted users (if any)
        users = load_users()
        if username in users and check_password_hash(users[username].get("password", ""), password):
            session["logged_in"] = True
            session["username"] = username
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=session.get("username"))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        print(f"📩 Message from {name} ({email}): {message}")
        flash("Thank you for contacting us!", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return render_template("signup.html")

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("signup.html")

        users = load_users()
        if username in users:
            flash("Username already exists. Please choose another.", "danger")
            return render_template("signup.html")

        users[username] = {
            "full_name": full_name,
            "email": email,
            "password": generate_password_hash(password)
        }
        save_users(users)
        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/upload", methods=["POST"])
@login_required
def upload_files():  # 👈 renamed to match dashboard.html
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    jd_text = ""
    jd_file = request.files.get("jd_file")

    # --- Handle JD file upload ---
    if jd_file and jd_file.filename:
        jd_path = os.path.join(UPLOAD_FOLDER, jd_file.filename)
        jd_file.save(jd_path)
        jd_text = extract_text(jd_path)

    resumes_raw = []
    resumes_info = []

    # --- Handle resumes ---
    if "resume_files" in request.files:
        for resume in request.files.getlist("resume_files"):
            if resume and resume.filename:
                resume_path = os.path.join(UPLOAD_FOLDER, resume.filename)
                resume.save(resume_path)
                text = extract_text(resume_path)
                resumes_raw.append(text)
                info = parse_resume(text, jd_text)
                # ensure keys expected by templates (capitalized) exist
                info["FileName"] = resume.filename
                info["Skills"] = info.get("skills", [])
                info["Name"] = info.get("name", "")
                info["Email"] = info.get("email", "")
                info["Phone"] = info.get("phone", "")
                resumes_info.append(info)

    # --- AI Matching ---
    matches = match_job_to_candidates(jd_text, resumes_raw, top_k=len(resumes_raw))
    for idx, score in matches:
        if 0 <= idx < len(resumes_info):
            resumes_info[idx]["Score"] = score
            resumes_info[idx]["Suggestions"] = suggest_improvements(jd_text, resumes_raw[idx], resumes_info[idx].get("Skills", []))

    return render_template(
        "results.html",
        resumes_info=resumes_info,
        jd_text=jd_text,
        username=session.get("username")
    )


@app.route("/results")
@login_required
def results():
    return render_template("results.html", jd_text="", resumes_info=[], username=session.get("username"))


# ---------- Run ----------
if __name__ == "__main__":
    app.run(debug=True)
