from flask import Flask, request, jsonify, render_template, redirect, session
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from groq import Groq
from dotenv import load_dotenv
import os

# ================= LOAD ENV =================
load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

# ================= FLASK SETUP =================
app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

app.secret_key = "super_secret_key"

CORS(app, supports_credentials=True)
bcrypt = Bcrypt(app)

# ================= DATABASE =================
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ================= GROQ CLIENT =================
client = Groq(api_key=API_KEY)

# ===================================================
# ================= DATABASE MODELS =================
# ===================================================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

with app.app_context():
    db.create_all()

# ===================================================
# ======================== ROUTES ===================
# ===================================================

@app.route("/")
def home():
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")
    return render_template("index.html")


# ================= REGISTER =================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"success": False, "message": "Missing fields"})

    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "message": "User already exists"})

    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

    new_user = User(email=email, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"success": True})


# ================= LOGIN =================

@app.route("/login", methods=["POST"])
def login():

    data = request.json
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if user and bcrypt.check_password_hash(user.password, password):
        session.clear()
        session["user_id"] = user.id
        return jsonify({"success": True})

    return jsonify({"success": False, "message": "Invalid credentials"})


# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ================= FORGOT PASSWORD PAGE =================

@app.route("/forgot-password")
def forgot_password_page():
    return render_template("forgot.html")


# ================= RESET PASSWORD (NO OTP) =================

@app.route("/reset-password", methods=["POST"])
def reset_password():

    data = request.json
    email = data.get("email")
    new_password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"success": False, "message": "User not found"})

    user.password = bcrypt.generate_password_hash(new_password).decode("utf-8")
    db.session.commit()

    return jsonify({"success": True})


# ================= AI GENERATION =================

SYSTEM_PROMPT = """
You are DIYA – Developer Intelligent Voice Assistant.
Generate clean and complete programming code.
Add comments.
If no language is specified, default to Python.
Only return code.
"""

@app.route("/generate-code", methods=["POST"])
def generate_code():

    if "user_id" not in session:
        return jsonify({"code": "Unauthorized", "language": "Error"})

    data = request.json
    user_text = data.get("text", "")

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            temperature=0.2
        )

        ai_response = completion.choices[0].message.content

        return jsonify({
            "code": ai_response,
            "language": "AI Generated"
        })

    except Exception as e:
        return jsonify({
            "code": f"Error: {str(e)}",
            "language": "Error"
        })


if __name__ == "__main__":
    app.run(debug=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)