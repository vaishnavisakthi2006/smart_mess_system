from flask import Flask, request, jsonify, send_from_directory,send_file
from flask_cors import CORS
import os
import pandas as pd
import csv
from datetime import datetime,timedelta
from collections import defaultdict
from textblob import TextBlob
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

app = Flask(__name__)
CORS(app)

def get_sentiment(text):
    analysis = TextBlob(text)

    if analysis.sentiment.polarity > 0:
        return "Positive"
    elif analysis.sentiment.polarity < 0:
        return "Negative"
    else:
        return "Neutral"
    
@app.route("/get_feedback_sentiment")
def get_feedback_sentiment():

    positive = 0
    negative = 0
    neutral = 0

    if os.path.exists(SENTIMENT_FILE):
        with open(SENTIMENT_FILE, "r") as f:
            reader = csv.DictReader(f)

            for row in reader:
                sentiment = get_sentiment(row["feedback"])

                if sentiment == "Positive":
                    positive += 1
                elif sentiment == "Negative":
                    negative += 1
                else:
                    neutral += 1

    return jsonify({
        "positive": positive,
        "negative": negative,
        "neutral": neutral
    })
# ---------------- PATH SETUP ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
DATA_DIR = os.path.join(BASE_DIR, "datasets")
os.makedirs(DATA_DIR, exist_ok=True)
FEEDBACK_FILE = os.path.join(DATA_DIR,"feedback.csv")

USER_FILE = os.path.join(DATA_DIR, "users.csv")  # Admin + Students
ADMIN_REGISTER_FILE = os.path.join(DATA_DIR, "admin_registers.csv")  # Allowed student register numbers
RATING_FILE = os.path.join(DATA_DIR, "ratings.csv")
SENTIMENT_FILE = os.path.join(BASE_DIR, "datasets", "feedback.csv")
# ---------------- MENU MANAGEMENT --------------
# ---------------- FILE PATHS ----------------
MESS_MENU_FILE = os.path.join(DATA_DIR, "mess_menu.csv")
MENU_REQUESTS_FILE = os.path.join(DATA_DIR, "menu_requests.csv")
STUDENT_LOGIN_FILE = os.path.join(DATA_DIR, "student_login.csv")

# ---------------- HELPER FUNCTIONS ----------------
def load_csv(file, columns):
    if not os.path.exists(file):
        return pd.DataFrame(columns=columns)
    return pd.read_csv(file)

def save_csv(df, file):
    df.to_csv(file, index=False)

# ---------------- FRONTEND ROUTES ----------------
@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "login.html")

@app.route("/register-page")
def register_page():
    return send_from_directory(FRONTEND_DIR, "register.html")

@app.route("/rating-page")
def rating_page():
    return send_from_directory(FRONTEND_DIR, "rating.html")

@app.route("/admin-page")
def admin_page():
    return send_from_directory(FRONTEND_DIR, "admin_dashboard.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)

# ---------------- STUDENT REGISTER ----------------
@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        register_no = data.get("register_no", "").strip()
        password = data.get("password", "").strip()

        if not register_no or not password:
            return jsonify({"message": "Missing fields"}), 400

        # 1️⃣ Check if register number exists in admin_registers.csv
        if not os.path.exists(ADMIN_REGISTER_FILE):
            return jsonify({"message": "Admin register file not found"}), 500

        admin_df = pd.read_csv(ADMIN_REGISTER_FILE)
        admin_df["register_no"] = admin_df["register_no"].astype(str).str.strip()

        if register_no not in admin_df["register_no"].values:
            return jsonify({"message": "Register number not allowed"}), 403

        # 2️⃣ Create student_login.csv if not exists
        if not os.path.exists(STUDENT_LOGIN_FILE):
            df = pd.DataFrame(columns=["register_no", "password"])
            df.to_csv(STUDENT_LOGIN_FILE, index=False)

        login_df = pd.read_csv(STUDENT_LOGIN_FILE)
        login_df["register_no"] = login_df["register_no"].astype(str).str.strip()

        # 3️⃣ Prevent duplicate registration
        if register_no in login_df["register_no"].values:
            return jsonify({"message": "Already registered"}), 400

        # 4️⃣ Save directly
        new_row = {
            "register_no": register_no,
            "password": password
        }

        login_df = pd.concat([login_df, pd.DataFrame([new_row])], ignore_index=True)
        login_df.to_csv(STUDENT_LOGIN_FILE, index=False)

        return jsonify({"message": "Registered Successfully"}), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500
# ---------------- STUDENT LOGIN ----------------
@app.route("/login", methods=["POST"])
def student_login():
    try:
        data = request.get_json()
        register_no = data.get("register_no", "").strip()
        password = data.get("password", "").strip()

        if not register_no or not password:
            return jsonify({"status": "error", "message": "Missing fields"}), 400

        file_path = os.path.join(DATA_DIR, "student_login.csv")

        if not os.path.exists(file_path):
            return jsonify({"status": "error", "message": "student_login.csv not found"}), 500

        # Read CSV and normalize headers
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip().str.lower()  # remove spaces & lowercase

        # Check required columns
        if "register_no" not in df.columns or "password" not in df.columns:
            return jsonify({"status": "error", "message": "Column mismatch in student_login.csv"}), 500

        # Filter user
        user = df[
            (df["register_no"].astype(str).str.strip() == register_no) &
            (df["password"].astype(str).str.strip() == password)
        ]

        if not user.empty:
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "fail", "message": "Invalid credentials"}), 401

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
# ---------------- ADMIN LOGIN ----------------
@app.route("/admin_login", methods=["POST"])
def admin_login():
    data = request.get_json()
    username = data.get("username")  # <-- match JS
    password = data.get("password")

    file_path = os.path.join(os.path.dirname(__file__), "datasets", "users.csv")

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("username") == username and row.get("password") == password and row.get("role") == "admin":
                return jsonify({"status": "success", "username": username})

    return jsonify({"status": "error", "message": "Invalid admin credentials"}), 401
# ------------------------------------ Submit Rating
RATING_REQUESTS_FILE = os.path.join(DATA_DIR, "rating_requests.csv")  # for admin dashboard

# ------------------------------------ Submit Rating
# ------------------------------------ Submit Rating
@app.route("/submit-rating", methods=["POST"])
def submit_rating():
    try:
        data = request.get_json()

        register_no = data.get("register_no")
        item_name = data.get("item_name")
        rating = data.get("rating")
        meal_type = data.get("meal_type")

        # Validation
        if not register_no or not item_name or not rating or not meal_type:
            return jsonify({"message": "Missing required fields"}), 400

        rating = int(rating)
        today = datetime.now().strftime("%Y-%m-%d")

        # Create file if not exists
        if not os.path.exists(RATING_FILE):
            df = pd.DataFrame(columns=[
                "register_no",
                "item_name",
                "rating",
                "date",
                "meal_type"
            ])
            df.to_csv(RATING_FILE, index=False)

        df = pd.read_csv(RATING_FILE)

        new_row = {
            "register_no": register_no,
            "item_name": item_name,
            "rating": rating,
            "date": today,
            "meal_type": meal_type
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(RATING_FILE, index=False)

        return jsonify({"message": "Rating submitted successfully"}), 200

    except Exception as e:
        print("Submit rating error:", e)
        return jsonify({"message": str(e)}), 500
# ================= GET HISTORY =================
@app.route("/get-history/<regno>", methods=["GET"])
def get_history(regno):
    try:
        if not os.path.exists(RATING_FILE):
            return jsonify([])

        df = pd.read_csv(RATING_FILE)

        if df.empty:
            return jsonify([])

        # Ensure required columns exist
        required_cols = ["register_no", "item_name", "rating", "date"]
        for col in required_cols:
            if col not in df.columns:
                return jsonify([])

        # Clean values
        df["register_no"] = df["register_no"].astype(str).str.strip().str.upper()
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
        df = df.dropna(subset=["rating"])

        regno = str(regno).strip().upper()

        student_data = df[df["register_no"] == regno]

        if student_data.empty:
            return jsonify([])

        return jsonify(student_data.to_dict(orient="records"))

    except Exception as e:
        print("History error:", e)
        return jsonify([]), 500
#-----------profile----------

def clean_string(s):
    """Remove all non-alphanumeric characters and trim spaces."""
    return ''.join(c for c in s if c.isalnum()).upper()
#=======================================Student Profile ============================
@app.route("/get-profile/<reg_no>")
def get_profile(reg_no):
    # Path to CSV inside backend/datasets
    file_path = os.path.join(os.path.dirname(__file__), "datasets", "admin_registers.csv")
    
    if not os.path.exists(file_path):
        return jsonify({"error": "CSV file not found"}), 404

    profile = None
    clean_input = clean_string(reg_no)

    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
        if not lines:
            return jsonify({"error": "CSV file is empty"}), 500

        # First line is header
        header = [h.strip() for h in lines[0].split(",")]

        # Loop through all other lines
        for line in lines[1:]:
            values = [v.strip() for v in line.split(",")]
            row = dict(zip(header, values))
            clean_csv_reg = clean_string(row.get("register_no", ""))
            if clean_csv_reg == clean_input:
                # Found the profile
                profile = {
                    "register_no": row.get("register_no", ""),
                    "name": row.get("name", ""),
                    "sem_no": row.get("sem_no", ""),
                    "department": row.get("department", "")
                }
                break

    if profile:
        return jsonify(profile)
    else:
        return jsonify({"error": f"No profile found for {reg_no}"}), 404
    
# ---------------- ADMIN DASHBOARD ----------------
@app.route("/dashboard", methods=["GET"])
def dashboard():
    try:
        ratings_df = load_csv(RATING_FILE, ["register_no","food_name","meal","rating","feedback"])
        if ratings_df.empty:
            return jsonify({"total_ratings":0,"average_rating":0,"latest":[]})
        ratings_df["rating"] = ratings_df["rating"].astype(float)
        return jsonify({
            "total_ratings":len(ratings_df),
            "average_rating":round(ratings_df["rating"].mean(),2),
            "latest":ratings_df.tail(5).to_dict(orient="records")
        })
    except Exception as e:
        return jsonify({"message":str(e)}),500
    
    # ---------------- GET PENDING RATING REQUESTS (ADMIN) ----------------
@app.route("/get-pending-ratings", methods=["GET"])
def get_pending_ratings():
    try:
        if not os.path.exists(RATING_REQUESTS_FILE):
            return jsonify([])  # No pending ratings yet

        df = pd.read_csv(RATING_REQUESTS_FILE)

        # Only include pending requests
        pending_df = df[df["status"] == "Pending"]

        return jsonify(pending_df.to_dict(orient="records")), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500

    #-----------------------Route for live data-----------------
# ================= GET DASHBOARD DATA =================
@app.route("/get_dashboard", methods=["GET"])
def get_dashboard():
    try:
        all_ratings = []
        item_ratings = defaultdict(list)
        weekly_ratings = defaultdict(list)
        today = datetime.now().date()

        # Read ratings.csv
        if os.path.exists(RATING_FILE):
            with open(RATING_FILE, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        rating = float(row.get("rating", 0))
                        item = row.get("item_name","")
                        date = datetime.strptime(row.get("date","2026-01-01"), "%Y-%m-%d").date()
                    except Exception:
                        continue

                    all_ratings.append(rating)
                    item_ratings[item].append(rating)

                    if today - timedelta(days=6) <= date <= today:
                        day_name = date.strftime("%a")
                        weekly_ratings[day_name].append(rating)

        avg_rating = round(sum(all_ratings)/len(all_ratings), 2) if all_ratings else 0
        top_item = max(item_ratings.items(), key=lambda x: sum(x[1])/len(x[1]))[0] if item_ratings else "N/A"
        needs_improvement = min(item_ratings.items(), key=lambda x: sum(x[1])/len(x[1]))[0] if item_ratings else "N/A"

        weekly_labels = []
        weekly_ratings_list = []
        for i in range(7):
            day_date = today - timedelta(days=6-i)
            day_name = day_date.strftime("%a")
            weekly_labels.append(day_name)
            day_vals = weekly_ratings.get(day_name, [])
            weekly_ratings_list.append(round(sum(day_vals)/len(day_vals), 2) if day_vals else 0)

        food_items = []
        food_ratings = []
        for item, ratings_list in item_ratings.items():
            food_items.append(item)
            food_ratings.append(round(sum(ratings_list)/len(ratings_list), 2))

                # ✅ Total feedbacks (from feedback.csv)
        total_feedbacks = 0
        if os.path.exists(FEEDBACK_FILE):
            df_feedback = pd.read_csv(FEEDBACK_FILE)
            total_feedbacks = len(df_feedback)

        # ✅ Total change requests
        total_change_requests = 0
        if os.path.exists(MENU_REQUESTS_FILE):
            df_req = pd.read_csv(MENU_REQUESTS_FILE)
            total_change_requests = len(df_req)

        return jsonify({
            "avg_rating": avg_rating,
            "top_item": top_item,
            "needs_improvement": needs_improvement,
            "weekly_labels": weekly_labels,
            "weekly_ratings": weekly_ratings_list,
            "food_items": food_items,
            "food_ratings": food_ratings,
            "total_feedbacks": total_feedbacks,
            "total_change_requests": total_change_requests
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- FETCH MENU FOR STUDENTS / ADMIN ----------------
@app.route("/get-menu", methods=["GET"])
def get_menu():
    try:
        if not os.path.exists(MESS_MENU_FILE):
            return jsonify([])

        df = pd.read_csv(MESS_MENU_FILE)

        if df.empty:
            return jsonify([])

        today = datetime.now().strftime("%Y-%m-%d")

        # Convert date column to string and match today
        df["date"] = df["date"].astype(str)
        df_today = df[df["date"].str.contains(today)]

        return jsonify(df_today.to_dict(orient="records"))

    except Exception as e:
        return jsonify({"error": str(e)}), 500

#====================================
@app.route("/add-menu-item", methods=["POST"])
def add_menu_item():
    try:
        data = request.get_json()
        meal_type = data.get("meal_type")
        mess_menu = data.get("mess_menu")
        if not meal_type or not mess_menu:
            return jsonify({"success": False, "error": "Missing fields"}), 400

        today = datetime.now().strftime("%Y-%m-%d")
        day_name = datetime.now().strftime("%A")
        df = pd.read_csv(MESS_MENU_FILE) if os.path.exists(MESS_MENU_FILE) else pd.DataFrame(columns=["date","day","meal_type","mess_menu","category"])
        new_row = {"date": today, "day": day_name, "meal_type": meal_type, "mess_menu": mess_menu, "category": "Main"}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(MESS_MENU_FILE, index=False)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------- DELETE MENU ITEM (ADMIN) ----------------
@app.route("/delete-menu-item", methods=["POST"])
def delete_menu_item():
    try:
        data = request.get_json()
        meal_type = data.get("meal_type")
        mess_menu = data.get("mess_menu")
        df = pd.read_csv(MESS_MENU_FILE) if os.path.exists(MESS_MENU_FILE) else pd.DataFrame()
        df = df[~((df["meal_type"]==meal_type) & (df["mess_menu"]==mess_menu))]
        df.to_csv(MESS_MENU_FILE, index=False)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    # ================= SUBMIT MENU REQUEST =================

@app.route("/submit-menu-request", methods=["POST"])
def submit_menu_request():
    try:
        data = request.get_json()
        register_no = data.get("register_no")
        meal_type = data.get("meal_type")
        item_name = data.get("item_name", "")
        message = data.get("message")

        if not register_no or not meal_type or not message:
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        if not os.path.exists(MENU_REQUESTS_FILE):
            df = pd.DataFrame(columns=["register_no","meal_type","item_name","message","date"])
            df.to_csv(MENU_REQUESTS_FILE, index=False)

        df = pd.read_csv(MENU_REQUESTS_FILE)

        new_row = {
            "register_no": register_no,
            "meal_type": meal_type,
            "item_name": item_name,
            "message": message,
            "date": datetime.now().strftime("%Y-%m-%d")
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(MENU_REQUESTS_FILE, index=False)

        return jsonify({"success": True, "message": "Menu request submitted successfully!"}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    #------------------------------------Approve Student------------------------------
@app.route("/get_all_students_status", methods=["GET"])
def get_all_students_status():
    try:
        if not os.path.exists(ADMIN_REGISTER_FILE):
            return jsonify([])

        admin_df = pd.read_csv(ADMIN_REGISTER_FILE)
        admin_df.columns = admin_df.columns.str.strip()
        admin_df["register_no"] = admin_df["register_no"].astype(str).str.strip()

        # Read student login file
        if os.path.exists(STUDENT_LOGIN_FILE):
            login_df = pd.read_csv(STUDENT_LOGIN_FILE)
            login_list = login_df["register_no"].astype(str).str.strip().tolist()
        else:
            login_list = []

        students = []

        for _, row in admin_df.iterrows():
            reg_no = str(row["register_no"]).strip()

            students.append({
                "register_no": reg_no,
                "name": row.get("name", ""),
                "sem_no": row.get("sem_no", ""),
                "department": row.get("department", ""),
                "date": row.get("date", ""),
                "is_registered": reg_no in login_list
            })

        return jsonify(students)

    except Exception as e:
        print("Student status error:", str(e))
        return jsonify([])
# ---------------- SUBMIT FEEDBACK ----------------
# ================= FEEDBACK FILE =================
@app.route("/submit-feedback", methods=["POST"])
def submit_feedback():
    try:
        data = request.get_json()
        register_no = data.get("register_no")
        meal_type = data.get("meal_type")
        feedback = data.get("feedback", "").strip()

        if not register_no or not meal_type or not feedback:
            return jsonify({"message": "Missing fields"}), 400

        today = datetime.now().strftime("%Y-%m-%d")

        # Create feedback.csv if it doesn't exist
        if not os.path.exists(FEEDBACK_FILE):
            df = pd.DataFrame(columns=["register_no", "meal_type", "feedback", "date"])
            df.to_csv(FEEDBACK_FILE, index=False)

        # Append feedback
        df = pd.read_csv(FEEDBACK_FILE)
        new_row = {
            "register_no": register_no,
            "meal_type": meal_type,
            "feedback": feedback,
            "date": today
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(FEEDBACK_FILE, index=False)

        return jsonify({"message": "Feedback saved successfully"}), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 500
    
    #===============================================
    #              Pdf report                      #
    #==============================================#
@app.route("/download-weekly-report")
def download_weekly_report():

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    ratings_path = os.path.join(BASE_DIR,"datasets","ratings.csv")
    pdf_path = os.path.join(BASE_DIR,"datasets","weekly_report.pdf")

    ratings = pd.read_csv(ratings_path)

    ratings["date"] = pd.to_datetime(ratings["date"])

    last_week = datetime.now() - timedelta(days=7)

    weekly_data = ratings[ratings["date"] >= last_week]

    report = weekly_data.groupby("item_name").agg(
        avg_rating=("rating","mean"),
        total_ratings=("rating","count")
    ).reset_index()

    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("MessMate Weekly Report", styles["Title"]))
    elements.append(Spacer(1,20))

    data = [["Food Item","Average Rating","Total Ratings"]]

    for _, row in report.iterrows():
        data.append([
            row["item_name"],
            round(row["avg_rating"],2),
            row["total_ratings"]
        ])

    table = Table(data)

    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.orange),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),1,colors.grey)
    ]))

    elements.append(table)

    pdf = SimpleDocTemplate(pdf_path)
    pdf.build(elements)

    return send_file(pdf_path, as_attachment=True)
    
# ---------------- MAIN ----------------
if __name__=="__main__":
    print("Backend running on http://127.0.0.1:5000")
    app.run(debug=True)