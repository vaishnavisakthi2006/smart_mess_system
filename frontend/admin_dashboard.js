// ================= SECTION SWITCHING =================
const dashboardBtn = document.getElementById("dashboard-btn");
const menuBtn = document.getElementById("menu-btn");
const studentsBtn = document.getElementById("students-btn");

const dashboardSection = document.getElementById("dashboard-section");
const menuSection = document.getElementById("menu-section");
const studentsSection = document.getElementById("students-section");

function switchSection(activeBtn, activeSection){
    document.querySelectorAll(".menu li").forEach(li => li.classList.remove("active"));
    document.querySelectorAll(".section").forEach(sec => sec.classList.remove("active"));
    activeBtn.classList.add("active");
    activeSection.classList.add("active");
}

// Tab click events
dashboardBtn.onclick = () => {
    switchSection(dashboardBtn, dashboardSection);
    loadDashboard();
};
menuBtn.onclick = () => {
    switchSection(menuBtn, menuSection);
    loadMenu();
};
studentsBtn.onclick = () => {
    switchSection(studentsBtn, studentsSection);
    loadStudents();
};

// ================= LOGOUT =================
function logout(){
    window.location.href = "login.html";
}

// ================= DASHBOARD =================
let ratingChart, foodChart,sentimentChart;

function loadDashboard(){
    fetch("/get_dashboard")
    .then(res => res.json())
    .then(data => {

        // Dashboard cards
        document.getElementById("avg-rating").textContent = `${data.avg_rating.toFixed(2)} / 5`;
document.getElementById("top-item").textContent = data.top_item || "-";
document.getElementById("needs-improvement").textContent = data.needs_improvement || "-";
document.getElementById("total-feedbacks").textContent = data.total_feedbacks || 0;
document.getElementById("total-change-requests").textContent = data.total_change_requests || 0;
        // Weekly Trend Chart
        if(ratingChart) ratingChart.destroy();
        ratingChart = new Chart(document.getElementById("ratingChart"), {
            type: 'line',
            data: {
                labels: data.weekly_labels,
                datasets: [{
                    label: 'Rating',
                    data: data.weekly_ratings,
                    borderWidth: 2,
                    fill: false,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                scales: { y: { min: 0, max: 5 } }
            }
        });

        // Food Performance Chart
        if(foodChart) foodChart.destroy();
        foodChart = new Chart(document.getElementById("foodChart"), {
            type: 'bar',
            data: {
                labels: data.food_items,
                datasets: [{
                    label: 'Average Rating',
                    data: data.food_ratings
                }]
            },
            options: { responsive: true }
        });

    })
    .catch(err => console.error("Dashboard error:", err));
}

function loadSentiment() {
    fetch("/get_feedback_sentiment")
    .then(res => res.json())
    .then(data => {

        if(sentimentChart) sentimentChart.destroy();

        const ctx = document.getElementById("sentimentChart");

         sentimentChart = new Chart(ctx, {
            type: "pie",
            data: {
                labels: ["Positive", "Negative", "Neutral"],
                datasets: [{
                    data: [data.positive, data.negative, data.neutral]
                }]
            },
            options: {
                responsive: true
            }
        });

    });
}
function downloadWeeklyReport()
{
    window.location.href="/download-weekly-report";
}


// ================= MENU MANAGEMENT =================
function loadMenu(){
    fetch("/get-menu")
    .then(res => res.json())
    .then(data => {
        const today = new Date().toISOString().split("T")[0];

        ["Breakfast", "Lunch", "Dinner"].forEach(meal => {
            const ul = document.getElementById(meal + "-list");
            ul.innerHTML = "";

            const todayItems = data.filter(item =>
                item.meal_type === meal && item.date.split("T")[0] === today
            );

            if(todayItems.length === 0){
                ul.innerHTML = "<li>No items added for today</li>";
                return;
            }

            todayItems.forEach(item => {
                const li = document.createElement("li");
                li.innerHTML = `
                    ${item.mess_menu}
                    <button onclick="deleteItem('${meal}','${item.mess_menu}')">Delete</button>
                `;
                ul.appendChild(li);
            });
        });
    })
    .catch(err => console.error("Menu load error:", err));
}

// Add new menu item
function addItem(){
    const mealType = document.getElementById("meal-type").value;
    const newItem = document.getElementById("new-item").value.trim();

    if(!newItem){
        alert("Enter food name");
        return;
    }

    fetch("/add-menu-item", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ meal_type: mealType, mess_menu: newItem })
    })
    .then(res => res.json())
    .then(data => {
        if(data.success){
            document.getElementById("new-item").value = "";
            loadMenu();
        } else {
            alert(data.error || "Failed to add item");
        }
    })
    .catch(err => console.error("Add item error:", err));
}

// Delete menu item
function deleteItem(mealType, itemName){
    fetch("/delete-menu-item", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ meal_type: mealType, mess_menu: itemName })
    })
    .then(res => res.json())
    .then(data => {
        if(data.success){
            loadMenu();
        } else {
            alert(data.error || "Failed to delete item");
        }
    })
    .catch(err => console.error("Delete error:", err));
}

// ================= STUDENT SECTION =================
function loadStudents(){
    fetch("/get_all_students_status")
    .then(res => res.json())
    .then(data => {
        const tableBody = document.getElementById("student-table-body");
        tableBody.innerHTML = "";

        if(!data || data.length === 0){
            tableBody.innerHTML = "<tr><td colspan='6'>No students found</td></tr>";
            return;
        }

        data.forEach(student => {
            const statusIcon = student.is_registered
                ? "<span style='color:green; font-size:18px;'>✔</span>"
                : "<span style='color:red; font-size:18px;'>✖</span>";

            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${student.register_no}</td>
                <td>${student.name || "-"}</td>
                <td>${student.sem_no || "-"}</td>
                <td>${student.department || "-"}</td>
                <td>${student.date || "-"}</td>
                <td>${statusIcon}</td>
            `;
            tableBody.appendChild(row);
        });
    })
    .catch(err => console.error("Students load error:", err));
}


// ================= AUTO LOAD ON PAGE LOAD =================
document.addEventListener("DOMContentLoaded", () => {
    // Show Dashboard and Menu by default
    switchSection(dashboardBtn, dashboardSection);
    loadDashboard();
    loadMenu();
    loadStudents();
    loadSentiment();
});