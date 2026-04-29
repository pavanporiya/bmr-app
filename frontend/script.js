let userId = null;
let token = null;

// 🔥 CHECK SESSION ON LOAD
window.onload = function () {
    const saved = localStorage.getItem("token");

    if (saved) {
        token = saved;
        showApp();
        loadHistory();
    } else {
        showAuth();
    }
};

function showAuth() {
    document.getElementById("authSection").style.display = "flex";
    document.getElementById("appSection").style.display = "none";
}

// 🔐 SHOW APP
function showApp() {
    const auth = document.getElementById("authSection");
    const app = document.getElementById("appSection");

    auth.classList.add("fade-out");

    setTimeout(() => {
        auth.style.display = "none";
        auth.classList.remove("fade-out");
    }, 300);

    app.style.display = "flex";
}

// 🔐 SHOW LOGIN
function showAuth() {
    const auth = document.getElementById("authSection");
    const app = document.getElementById("appSection");

    app.style.display = "none";
    auth.style.display = "flex";

    setTimeout(() => {
        auth.classList.remove("fade-out");
    }, 10);
}

// 🔐 LOGOUT
function logout() {
    userId = null;
    token = null;

    localStorage.removeItem("token");

    showAuth();
}

// 🔐 SIGNUP (🔥 LOADING ADDED)
async function signup() {
    const btn = event.target;
    btn.innerText = "Creating account...";
    btn.disabled = true;

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!username || !password) {
        alert("Enter username & password");
        btn.innerText = "Signup";
        btn.disabled = false;
        return;
    }

    try {
        const res = await fetch("https://bmr-backend-no2v.onrender.com/signup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();
        alert(data.success ? "Signup success" : data.error);

    } catch {
        alert("Server error");
    }

    btn.innerText = "Signup";
    btn.disabled = false;
}

// 🔑 LOGIN (🔥 LOADING ADDED)
async function login() {
    const btn = event.target;
    btn.innerText = "Logging in...";
    btn.disabled = true;

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!username || !password) {
        alert("Enter username & password");
        btn.innerText = "Login";
        btn.disabled = false;
        return;
    }

    try {
        const res = await fetch("https://bmr-backend-no2v.onrender.com/login", {
            method: "POST",
            mode: "cors",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();

        if (data.success) {
            token = data.token;
            localStorage.setItem("token", token);

            showApp();
            loadHistory();
        } else {
            alert("Login failed");
        }

    } catch {
        alert("Server error");
    }

    btn.innerText = "Login";
    btn.disabled = false;
}

// 🧠 VALIDATION
function validateInputs(age, weight, height, gender) {
    if (!age || !weight || !height || !gender) return "All fields required";
    if (age <= 0 || age > 120) return "Invalid age";
    if (weight <= 0 || weight > 300) return "Invalid weight";
    if (height <= 50 || height > 300) return "Invalid height";
    if (!["male", "female"].includes(gender)) return "Invalid gender";
    return null;
}

// 🚀 CALCULATE (🔥 IMPROVED LOADER)
async function calculateBMR() {
    if (!token) {
        alert("Login first");
        return;
    }

    const btn = document.querySelector(".btn.primary");
    btn.innerText = "Calculating...";
    btn.disabled = true;

    const resultDiv = document.getElementById("result");

    // 🔥 spinner UI
    resultDiv.innerHTML = `<div class="loader"></div><p style="text-align:center;">Calculating your plan...</p>`;

    const age = parseInt(document.getElementById("age").value);
    const weight = parseFloat(document.getElementById("weight").value);
    const height = parseFloat(document.getElementById("height").value);
    const gender = document.getElementById("gender").value;

    const activity = document.getElementById("activity")?.value || "sedentary";
    const goal = document.getElementById("goal")?.value || "maintain";
    const diet = document.getElementById("diet")?.value || "veg";

    const error = validateInputs(age, weight, height, gender);
    if (error) {
        alert(error);
        btn.disabled = false;
        btn.innerText = "Calculate";
        return;
    }

    try {
        const res = await fetch("https://bmr-backend-no2v.onrender.com/calculate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            },
            body: JSON.stringify({ age, weight, height, gender, activity, goal, diet })
        });

        const data = await res.json();

        renderResult(data);
        loadHistory();

    } catch {
        resultDiv.innerText = "Server error";
    }

    btn.disabled = false;
    btn.innerText = "Calculate";
}

// 📊 HISTORY
async function loadHistory() {
    try {
        const res = await fetch("https://bmr-backend-no2v.onrender.com/history", {
            headers: { "Authorization": "Bearer " + token }
        });

        const data = await res.json();

        if (!data.success) return;

        const list = document.getElementById("historyList");
        list.innerHTML = "";

        data.data.forEach(item => {
            const div = document.createElement("div");

            div.innerHTML = `
                <strong>${item.gender.toUpperCase()}</strong> | Age: ${item.age}
                <br>BMR: ${item.bmr}
                <button onclick="deleteRecord(${item.id})">✖</button>
            `;

            list.appendChild(div);
        });

    } catch (err) {
        console.error(err);
    }
}

// ❌ DELETE (🔥 LOADING FEEDBACK)
function deleteRecord(id) {
    const resultDiv = document.getElementById("result");
    resultDiv.innerText = "Deleting...";

    fetch(`https://bmr-backend-no2v.onrender.com/delete/${id}`, {
        method: "DELETE",
        headers: { "Authorization": "Bearer " + token }
    }).then(() => {
        loadHistory();
        resultDiv.innerText = "Deleted successfully";
    });
}

// 📊 RESULT
function renderResult(data) {
    if (!data.success) {
        document.getElementById("result").innerText = data.error;
        return;
    }

    const d = data.data;

    document.getElementById("result").innerHTML = `
        <h3>Fitness Report</h3>
        BMR: <b>${d.bmr}</b><br>
        TDEE: <b>${d.tdee}</b><br>
        Calories: <b>${d.target_calories}</b>

        <div class="macros">
            <div class="macro-box">Protein<br>${d.macros.protein}g</div>
            <div class="macro-box">Fat<br>${d.macros.fat}g</div>
            <div class="macro-box">Carbs<br>${d.macros.carbs}g</div>
        </div>

        <div class="info-box"><b>Diet:</b><br>${d.diet.join(", ")}</div>
        <div class="info-box"><b>Workout:</b><br>${d.workout}</div>
        <div class="info-box"><b>Insight:</b><br>${d.insight}</div>
    `;
}