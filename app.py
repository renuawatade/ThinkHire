from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, send_file
import io
import csv
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
        # Some .docx files are not valid zip archives (corrupted or misnamed).
        # Check first to avoid docx2txt raising BadZipFile.
        try:
            if zipfile.is_zipfile(file_path):
                try:
                    text = docx2txt.process(file_path) or ""
                except Exception:
                    # If docx2txt fails for any reason, fallback to best-effort decode
                    try:
                        with open(file_path, "rb") as f:
                            data = f.read()
                            text = data.decode("utf-8", errors="ignore")
                    except Exception:
                        text = ""
            else:
                # Not a valid zip -> fallback to reading as plain text
                try:
                    with open(file_path, "rb") as f:
                        data = f.read()
                        text = data.decode("utf-8", errors="ignore")
                except Exception:
                    text = ""
        except Exception:
            # Any unexpected error: return empty string rather than crashing
            text = ""
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
    # Clear previous analysis results when user starts a new one
    session.pop('last_results', None)
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

    # --- Handle uploaded ZIP files (input name: resume_zips) ---
    if "resume_zips" in request.files:
        for zip_file in request.files.getlist("resume_zips"):
            if not zip_file or not zip_file.filename:
                continue
            zip_name = os.path.basename(zip_file.filename)
            if not zip_name.lower().endswith(".zip"):
                continue
            zip_path = os.path.join(UPLOAD_FOLDER, zip_name)
            zip_file.save(zip_path)
            try:
                with zipfile.ZipFile(zip_path, "r") as z:
                    extract_dir = os.path.join(UPLOAD_FOLDER, os.path.splitext(zip_name)[0])
                    os.makedirs(extract_dir, exist_ok=True)
                    z.extractall(extract_dir)

                    for member in z.namelist():
                        if member.endswith("/") or member.endswith("\\"):
                            continue
                        member_basename = os.path.basename(member)
                        if not member_basename:
                            continue
                        member_path = os.path.join(extract_dir, member)
                        if not os.path.exists(member_path):
                            continue
                        if member_basename.lower().endswith((".pdf", ".docx", ".txt")):
                            text = extract_text(member_path)
                            resumes_raw.append(text)
                            info = parse_resume(text, jd_text)
                            info["FileName"] = member_basename
                            info["Skills"] = info.get("skills", [])
                            info["Name"] = info.get("name", "")
                            info["Email"] = info.get("email", "")
                            info["Phone"] = info.get("phone", "")
                            resumes_info.append(info)
            except zipfile.BadZipFile:
                flash(f"Uploaded zip '{zip_name}' is not a valid archive.", "danger")


    # --- Handle resumes (multiple files, directories, and zip archives) ---
    if "resume_files" in request.files:
        for resume in request.files.getlist("resume_files"):
            if not resume or not resume.filename:
                continue

            filename = os.path.basename(resume.filename)

            # --- ZIP archive support ---
            if filename.lower().endswith(".zip"):
                zip_path = os.path.join(UPLOAD_FOLDER, filename)
                resume.save(zip_path)
                try:
                    with zipfile.ZipFile(zip_path, "r") as z:
                        extract_dir = os.path.join(UPLOAD_FOLDER, os.path.splitext(filename)[0])
                        os.makedirs(extract_dir, exist_ok=True)
                        z.extractall(extract_dir)

                        for member in z.namelist():
                            # skip directories
                            if member.endswith("/") or member.endswith("\\"):
                                continue
                            member_basename = os.path.basename(member)
                            if not member_basename:
                                continue
                            member_path = os.path.join(extract_dir, member)
                            if not os.path.exists(member_path):
                                # some zip entries may have nested directories; ensure path
                                continue
                            if member_basename.lower().endswith((".pdf", ".docx", ".txt")):
                                text = extract_text(member_path)
                                resumes_raw.append(text)
                                info = parse_resume(text, jd_text)
                                info["FileName"] = member_basename
                                info["Skills"] = info.get("skills", [])
                                info["Name"] = info.get("name", "")
                                info["Email"] = info.get("email", "")
                                info["Phone"] = info.get("phone", "")
                                resumes_info.append(info)
                except zipfile.BadZipFile:
                    flash(f"Uploaded zip '{filename}' is not a valid archive.", "danger")
                continue

            # --- Regular file (including files uploaded via folder input) ---
            resume_path = os.path.join(UPLOAD_FOLDER, filename)
            resume.save(resume_path)
            # If the browser provided a relative path (from directory upload), sanitize name above
            text = extract_text(resume_path)
            resumes_raw.append(text)
            info = parse_resume(text, jd_text)
            info["FileName"] = filename
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
    # Ensure every candidate has a numeric Score (default 0.0) and Suggestions key
    for r in resumes_info:
        r.setdefault("Score", 0.0)
        r.setdefault("Suggestions", r.get("Suggestions", []))

    # Sort candidates by Score descending so highest match appears first
    resumes_info.sort(key=lambda x: float(x.get("Score", 0.0)), reverse=True)

    # Store a lightweight serializable copy of results in session for downloads
    try:
        serializable = []
        for r in resumes_info:
            serializable.append({
                "FileName": r.get("FileName", ""),
                "Score": float(r.get("Score", 0.0)),
                "Skills": ", ".join(r.get("Skills", [])) if isinstance(r.get("Skills", []), (list, tuple)) else str(r.get("Skills", "")),
                "Suggestions": (", ".join(r.get("Suggestions")) if isinstance(r.get("Suggestions"), (list, tuple)) else str(r.get("Suggestions", "")))
            })
        session["last_results"] = serializable
    except Exception:
        # do not crash on session serialization; skip storing if any issue
        pass
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


@app.route('/download_csv')
@login_required
def download_csv():
    data = session.get('last_results')
    if not data:
        flash('No results available to download. Run an analysis first.', 'warning')
        return redirect(url_for('results'))

    # Create CSV in-memory
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Rank', 'FileName', 'MatchScore', 'Skills', 'Suggestions'])
    for idx, row in enumerate(data, start=1):
        cw.writerow([idx, row.get('FileName', ''), '{:.4f}'.format(float(row.get('Score', 0.0))), row.get('Skills', ''), row.get('Suggestions', '')])

    output = si.getvalue()
    mem = io.BytesIO()
    mem.write(output.encode('utf-8'))
    mem.seek(0)

    return send_file(mem, as_attachment=True, download_name='matching_results.csv', mimetype='text/csv')


@app.route('/export_pdf')
@login_required
def export_pdf():
    data = session.get('last_results')
    if not data:
        flash('No results available to export. Run an analysis first.', 'warning')
        return redirect(url_for('results'))

    # Try to import reportlab; if missing, inform the user
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch
    except Exception:
        flash("PDF export requires the 'reportlab' package. Install it with: pip install reportlab", 'danger')
        return redirect(url_for('results'))

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Header
    c.setFont('Helvetica-Bold', 14)
    c.drawString(40, height - 40, 'Candidate Matching Results')
    c.setFont('Helvetica', 10)
    c.drawString(40, height - 60, f'Generated for: {session.get("username", "") or "User"}')

    y = height - 90
    line_height = 14

    # Table header
    c.setFont('Helvetica-Bold', 10)
    c.drawString(40, y, 'Rank')
    c.drawString(80, y, 'FileName')
    c.drawString(300, y, 'Score')
    c.drawString(360, y, 'Skills')
    y -= line_height
    c.setFont('Helvetica', 9)

    for idx, row in enumerate(data, start=1):
        if y < 80:
            c.showPage()
            y = height - 50
            c.setFont('Helvetica', 9)

        fname = str(row.get('FileName', ''))
        score = '{:.1f}%'.format(float(row.get('Score', 0.0)) * 100)
        skills = str(row.get('Skills', ''))

        c.drawString(40, y, str(idx))
        c.drawString(80, y, (fname[:28] + '...') if len(fname) > 31 else fname)
        c.drawString(300, y, score)
        c.drawString(360, y, (skills[:60] + '...') if len(skills) > 63 else skills)
        y -= line_height

        # Suggestions on next line (wrapped)
        sugg = str(row.get('Suggestions', ''))
        if sugg:
            # naive wrap at ~90 chars
            parts = [sugg[i:i+90] for i in range(0, len(sugg), 90)]
            for p in parts:
                if y < 60:
                    c.showPage()
                    y = height - 50
                    c.setFont('Helvetica', 9)
                c.drawString(80, y, p)
                y -= line_height

    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='matching_results.pdf', mimetype='application/pdf')


# ---------- Run ----------
if __name__ == "__main__":
    app.run(debug=True)
