from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2.extras
import psycopg2
import bcrypt
import jwt
import datetime
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
    return response
# 🔐 SECRET KEY (later ENV me shift karna)
SECRET_KEY = os.getenv("SECRET_KEY")  # default for development


# 🔥 CORS (JWT compatible)
CORS(app,
     resources={r"/*": {"origins": "*"}},
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "DELETE", "OPTIONS"],
     supports_credentials=True)


# 🔌 DB CONNECTION
def get_connection():
    return psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    port=os.getenv("DB_PORT"),
    sslmode="require"

    )

# 🧠 BMR LOGIC
def calculate_bmr(age, weight, height, gender):
    if gender == "male":
        return 10*weight + 6.25*height - 5*age + 5
    elif gender == "female":
        return 10*weight + 6.25*height - 5*age - 161
    return None

def generate_fitness_plan(age, weight, height, gender, activity, goal, diet_type):

    # 🔥 Activity multipliers
    activity_map = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725
    }

    bmr = calculate_bmr(age, weight, height, gender)
    tdee = bmr * activity_map.get(activity, 1.2)

    # 🎯 Goal calories
    if goal == "loss":
        target_cal = tdee - 500
    elif goal == "gain":
        target_cal = tdee + 500
    else:
        target_cal = tdee

    # 🥩 Macros
    protein = weight * 1.6
    fat = weight * 0.8
    remaining_cal = target_cal - (protein * 4 + fat * 9)
    carbs = remaining_cal / 4

    # 🥗 Diet suggestions
    if diet_type == "veg":
        diet = [
            "Paneer / Tofu",
            "Dal & Rice",
            "Oats + Milk",
            "Fruits & Nuts"
        ]
    else:
        diet = [
            "Chicken Breast",
            "Eggs",
            "Fish",
            "Rice + Veggies"
        ]

    # 🏋 Workout suggestion
    if goal == "loss":
        workout = "Cardio + Light Weight Training (4–5x/week)"
    elif goal == "gain":
        workout = "Heavy Strength Training (4–5x/week)"
    else:
        workout = "Balanced Training (3–4x/week)"

    return {
        "bmr": round(bmr, 2),
        "tdee": round(tdee, 2),
        "target_calories": round(target_cal, 2),
        "macros": {
            "protein": round(protein, 1),
            "fat": round(fat, 1),
            "carbs": round(carbs, 1)
        },
        "diet": diet,
        "workout": workout
    }

# 🔐 TOKEN VERIFY (HARDENED)
def verify_token(auth_header):
    if not auth_header:
        return None, "Token missing"

    try:
        # 🔥 Expect: "Bearer TOKEN"
        parts = auth_header.split()

        if len(parts) != 2 or parts[0] != "Bearer":
            return None, "Invalid token format"

        token = parts[1]

        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded["user_id"], None

    except jwt.ExpiredSignatureError:
        return None, "Token expired"

    except jwt.InvalidTokenError:
        return None, "Invalid token"


# 🔐 SIGNUP
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data['username']
    password = data['password']

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hashed)
        )
        conn.commit()
        return jsonify({"success": True})
    except:
        return jsonify({"success": False, "error": "User already exists"})
    finally:
        cursor.close()
        conn.close()


# 🔑 LOGIN (HARDENED JWT)
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:
        return jsonify({"success": False, "error": "Invalid credentials"})

    stored_hash = user['password']

    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode('utf-8')
        # 🔐 Password check
    
    try:
        if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return jsonify({"success": False, "error": "Invalid credentials"})
    except ValueError:
        return jsonify({"success": False, "error": "Invalid password format )"})

    # 🔥 JWT with expiry
    token = jwt.encode({
        "user_id": user["id"],
        "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=2),
        "iat": datetime.datetime.now(datetime.UTC)
    }, SECRET_KEY, algorithm="HS256")

    return jsonify({
        "success": True,
        "token": token
    })
    
@app.route('/calculate', methods=['POST'])
def calculate():
    user_id, error = verify_token(request.headers.get("Authorization"))

    if error:
        return jsonify({"success": False, "error": error})

    try:
        data = request.json

        age = int(data['age'])
        weight = float(data['weight'])
        height = float(data['height'])
        gender = data['gender']

        activity = data.get("activity", "sedentary")
        goal = data.get("goal", "maintain")
        diet_type = data.get("diet", "veg")

        # VALIDATION
        if age <= 0 or age > 120:
            return jsonify({"success": False, "error": "Invalid age"})

        if weight <= 0 or weight > 300:
            return jsonify({"success": False, "error": "Invalid weight"})

        if height <= 50 or height > 300:
            return jsonify({"success": False, "error": "Invalid height"})

        if gender not in ["male", "female"]:
            return jsonify({"success": False, "error": "Invalid gender"})

        # 🔥 BASE PLAN
        plan = generate_fitness_plan(
            age, weight, height, gender,
            activity, goal, diet_type
        )

        # 🔥 PERSONALIZATION
        new_calories, old_insight = personalize_calories(
            user_id,
            plan["target_calories"],
            goal
        )

        plan["target_calories"] = new_calories

        macros = plan["macros"]
        tdee = plan["tdee"]
        target = plan["target_calories"]

        insights = []

        # =========================
        # 🎯 GOAL LOGIC
        # =========================
        if goal == "loss":
            if target >= tdee:
                insights.append("⚠️ Not in calorie deficit for fat loss")
            else:
                insights.append("🔥 Calorie deficit detected — fat loss possible")

        elif goal == "gain":
            if target <= tdee:
                insights.append("⚠️ Calories too low for muscle gain")
            else:
                insights.append("💪 Calorie surplus — muscle gain supported")

        else:
            insights.append("⚖️ Maintenance mode — focus on consistency")

        # =========================
        # 🥩 PROTEIN
        # =========================
        ideal_protein = round(weight * 1.6)
        if macros["protein"] < ideal_protein:
            insights.append(f"⚠️ Protein low (Recommended: {ideal_protein}g)")
        else:
            insights.append("✅ Protein intake is good")

        # =========================
        # 🧈 FAT
        # =========================
        if macros["fat"] < (0.6 * weight):
            insights.append("⚠️ Fat too low — may affect hormones")

        # =========================
        # 🚶 ACTIVITY
        # =========================
        if activity == "sedentary":
            insights.append("🚶 Increase daily movement")
        elif activity == "active":
            insights.append("🔥 High activity — ensure recovery")

        # =========================
        # 🔁 PERSONALIZATION INSIGHT
        # =========================
        if old_insight:
            insights.append(old_insight)

        # =========================
        # 📊 MULTI-RECORD ANALYSIS
        # =========================
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
            SELECT * FROM bmr_records 
            WHERE user_id=%s 
            ORDER BY id DESC LIMIT 5
        """, (user_id,))

        records = cursor.fetchall()[::-1]  # oldest → newest

        if len(records) >= 3:
            weights = [r["weight"] for r in records]

            # 📉 consistent drop
            if all(weights[i] > weights[i+1] for i in range(len(weights)-1)):
                insights.append("📉 Consistent weight drop — fat loss working")

            # 📈 consistent gain
            elif all(weights[i] < weights[i+1] for i in range(len(weights)-1)):
                insights.append("📈 Consistent weight gain — surplus working")

            else:
                diff = max(weights) - min(weights)

                if diff < 1:
                    insights.append("➖ Plateau detected — adjust calories/activity")
                else:
                    insights.append("🔄 Weight fluctuating — track consistency")

        # =========================
        # 📊 LAST RECORD COMPARISON
        # =========================
        if records:
            last = records[-1]

            if weight > last["weight"]:
                insights.append("📈 Weight increasing")
            elif weight < last["weight"]:
                insights.append("📉 Weight decreasing")

            if target > last.get("target_calories", 0):
                insights.append("🔺 Calories increased")
            elif target < last.get("target_calories", 0):
                insights.append("🔻 Calories reduced")

            if macros["protein"] > last.get("protein", 0):
                insights.append("💪 Protein improved")

        # FINAL INSIGHT
        plan["insight"] = " | ".join(insights)

        # =========================
        # 🔁 DUPLICATE CHECK
        # =========================
        cursor.execute("""
            SELECT * FROM bmr_records 
            WHERE user_id=%s AND age=%s AND weight=%s AND height=%s AND gender=%s
            ORDER BY id DESC LIMIT 1
        """, (user_id, age, weight, height, gender))

        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "error": "Same data already exists"})

        # =========================
        # 💾 INSERT
        # =========================
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO bmr_records 
            (age, weight, height, gender, bmr, user_id, target_calories,
             tdee, protein, fat, carbs, goal, activity)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            age, weight, height, gender,
            plan["bmr"], user_id,
            plan["target_calories"],
            plan["tdee"],
            plan["macros"]["protein"],
            plan["macros"]["fat"],
            plan["macros"]["carbs"],
            goal,
            activity
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": plan
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    
        
# 📊 HISTORY
@app.route('/history', methods=['GET'])
def history():
    user_id, error = verify_token(request.headers.get("Authorization"))

    if error:
        return jsonify({"success": False, "error": error})

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute(
        "SELECT * FROM bmr_records WHERE user_id=%s ORDER BY id DESC",
        (user_id,)
    )

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({"success": True, "data": data})


# ❌ DELETE
@app.route('/delete/<int:id>', methods=['DELETE'])
def delete_record(id):
    user_id, error = verify_token(request.headers.get("Authorization"))

    if error:
        return jsonify({"success": False, "error": error})

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM bmr_records WHERE id=%s AND user_id=%s",
        (id, user_id)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"success": True})

def personalize_calories(user_id, current_calories, goal):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT target_calories FROM bmr_records
        WHERE user_id=%s
        ORDER BY id DESC LIMIT 1
    """, (user_id,))

    last = cursor.fetchone()

    cursor.close()
    conn.close()

    if not last:
        return current_calories, "First entry — baseline set"

    prev = last['target_calories']

    if goal == "loss":
        new = prev - 100
    elif goal == "gain":
        new = prev + 100
    else:
        new = current_calories

    return round(new, 2), f"Previous: {prev} → Adjusted: {new}"

def generate_insight(age, weight, height, gender, goal, activity, tdee, target_calories, macros):
    
    insights = []

    protein = macros["protein"]
    fat = macros["fat"]
    carbs = macros["carbs"]

    # 🔥 GOAL CHECK
    if goal == "loss":
        if target_calories >= tdee:
            insights.append("⚠️ You are not in calorie deficit for fat loss")
        else:
            insights.append("🔥 Good deficit — fat loss possible")

    elif goal == "gain":
        if target_calories <= tdee:
            insights.append("⚠️ You are not eating enough for muscle gain")
        else:
            insights.append("💪 Calorie surplus detected — muscle gain possible")

    else:
        insights.append("⚖️ Maintenance mode — focus on consistency")


    # 🔥 PROTEIN CHECK
    ideal_protein = round(weight * 1.6)

    if protein < ideal_protein:
        insights.append(f"⚠️ Protein too low (Recommended: {ideal_protein}g)")
    else:
        insights.append("✅ Protein intake is sufficient")


    # 🔥 FAT CHECK
    if fat < (0.6 * weight):
        insights.append("⚠️ Fat intake too low — may affect hormones")


    # 🔥 ACTIVITY CHECK
    if activity == "sedentary":
        insights.append("🚶 Increase daily movement (steps/cardio recommended)")
    elif activity == "active":
        insights.append("🔥 High activity — ensure proper recovery")


    # 🔥 FINAL SUMMARY
    return " | ".join(insights)

def get_previous_record(user_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT * FROM bmr_records 
        WHERE user_id=%s 
        ORDER BY id DESC LIMIT 1
    """, (user_id,))

    data = cursor.fetchone()

    cursor.close()
    conn.close()

    return data

def get_last_records(user_id, limit=5):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT * FROM bmr_records 
        WHERE user_id=%s 
        ORDER BY id DESC LIMIT %s
    """, (user_id, limit))

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data[::-1]  # oldest → newest

if __name__ == '__main__':
    app.run(debug=True)