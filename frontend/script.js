let userId = null;
let token = null;

const API = "https://bmr-backend-no2v.onrender.com";

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

function showApp() {
    document.getElementById("authSection").style.display = "none";
    document.getElementById("appSection").style.display = "flex";
}

function logout() {
    userId = null;
    token = null;
    localStorage.removeItem("token");
    showAuth();
}

async function signup(e) {
    const btn = e.target;
    btn.innerText = "Creating...";
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
        const res = await fetch(API + "/signup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();

        if (data.success) {
            alert("Signup success");
        } else {
            alert(data.error);
        }

    } catch (err) {
        alert("Server error");
    }

    btn.innerText = "Signup";
    btn.disabled = false;
}

async function login(e) {
    const btn = e.target;
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
        const res = await fetch(API + "/login", {
            method: "POST",
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
            alert(data.error);
        }

    } catch (err) {
        alert("Server error");
    }

    btn.innerText = "Login";
    btn.disabled = false;
}

function validateInputs(age, weight, height, gender) {
    if (!age || !weight || !height || !gender) return "All fields required";
    if (age <= 0 || age > 120) return "Invalid age";
    if (weight <= 0 || weight > 300) return "Invalid weight";
    if (height <= 50 || height > 300) return "Invalid height";
    if (gender !== "male" && gender !== "female") return "Invalid gender";
    return null;
}

async function calculateBMR() {
    if (!token) {
        alert("Login first");
        return;
    }

    const btn = document.querySelector(".btn.primary");
    btn.innerText = "Calculating...";
    btn.disabled = true;

    const resultDiv = document.getElementById("result");
    resultDiv.innerHTML = "Calculating...";

    const age = parseInt(document.getElementById("age").value);
    const weight = parseFloat(document.getElementById("weight").value);
    const height = parseFloat(document.getElementById("height").value);
    const gender = document.getElementById("gender").value;

    const activity = document.getElementById("activity").value;
    const goal = document.getElementById("goal").value;
    const diet = document.getElementById("diet").value;

    const error = validateInputs(age, weight, height, gender);
    if (error) {
        alert(error);
        btn.innerText = "Calculate";
        btn.disabled = false;
        return;
    }

    try {
        const res = await fetch(API + "/calculate", {
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

    } catch (err) {
        resultDiv.innerText = "Server error";
    }

    btn.innerText = "Calculate";
    btn.disabled = false;
}

async function loadHistory() {
    if (!token) return;

    try {
        const res = await fetch(API + "/history", {
            headers: { "Authorization": "Bearer " + token }
        });

        const data = await res.json();

        if (!data.success) return;

        const list = document.getElementById("historyList");
        list.innerHTML = "";

        data.data.forEach(item => {
            const div = document.createElement("div");

            div.innerHTML = `
                <strong>${item.gender}</strong> | Age: ${item.age}
                <br>BMR: ${item.bmr}
                <button onclick="deleteRecord(${item.id})">X</button>
            `;

            list.appendChild(div);
        });

    } catch (err) { }
}

function deleteRecord(id) {
    fetch(API + "/delete/" + id, {
        method: "DELETE",
        headers: { "Authorization": "Bearer " + token }
    }).then(() => loadHistory());
}

function renderResult(data) {
    if (!data.success) {
        document.getElementById("result").innerText = data.error;
        return;
    }

    const d = data.data;

    document.getElementById("result").innerHTML = `
        <h3>Result</h3>
        BMR: ${d.bmr} <br>
        TDEE: ${d.tdee} <br>
        Calories: ${d.target_calories}
    `;
}
