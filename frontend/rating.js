document.addEventListener("DOMContentLoaded", function () {
    const regno = localStorage.getItem("register_no");
    if (!regno) {
        alert("No register number found. Please login first.");
        window.location.href = "login.html";
        return;
    }

    // ===== PROFILE FETCH =====
    fetch(`http://127.0.0.1:5000/get-profile/${regno}`)
        .then(res => res.json())
        .then(data => {
            if (!data.error) {
                document.getElementById("profile-name").innerText = data.name;
                document.getElementById("profile-reg").innerText = data.register_no;
                document.getElementById("detail-name").innerText = data.name;
                document.getElementById("detail-reg").innerText = data.register_no;
                document.getElementById("detail-dept").innerText = data.department;
                document.getElementById("detail-sem").innerText = data.sem_no;
                document.getElementById("profile-initials").innerText = data.name.split(" ").map(n => n[0].toUpperCase()).join("");
                document.getElementById("signed-name").innerText = data.name;
                document.getElementById("signed-regno").innerText = data.register_no;
            }
        })
        .catch(err => console.error("Profile fetch error:", err));

    // ===== SIDEBAR NAVIGATION =====
    const menuBtn = document.getElementById("menu-btn");
    const historyBtn = document.getElementById("history-btn");
    const profileBtn = document.getElementById("profile-btn");
    const menuSection = document.getElementById("menu-section");
    const historySection = document.getElementById("history-section");
    const profileSection = document.getElementById("profile-section");

    function hideAllSections() {
        menuSection.style.display = "none";
        historySection.style.display = "none";
        profileSection.style.display = "none";
        menuBtn.classList.remove("active");
        historyBtn.classList.remove("active");
        profileBtn.classList.remove("active");
    }

    menuBtn.addEventListener("click", () => { hideAllSections(); menuSection.style.display = "block"; menuBtn.classList.add("active"); });
    historyBtn.addEventListener("click", () => { hideAllSections(); historySection.style.display = "block"; historyBtn.classList.add("active"); loadHistory(); });
    profileBtn.addEventListener("click", () => { hideAllSections(); profileSection.style.display = "block"; profileBtn.classList.add("active"); });

    hideAllSections();
    menuSection.style.display = "block";
    menuBtn.classList.add("active");

    // ===== LOAD TODAY'S MENU =====
    function loadTodayMenu() {
        fetch("http://127.0.0.1:5000/get-menu")
            .then(res => res.json())
            .then(menu => {

                const today = new Date().toISOString().split("T")[0];
                const containerIds = ["breakfast-items","lunch-items","dinner-items"];

                ["Breakfast", "Lunch", "Dinner"].forEach((meal, index) => {
                    const container = document.getElementById(containerIds[index]);
                    if (!container) return;
                    container.innerHTML = `<h3>${meal} - ${new Date().toLocaleDateString()}</h3>`;

                    const mealItems = menu.filter(item => item.meal_type === meal && item.date.split("T")[0] === today);

                    if (mealItems.length === 0) {
                        container.innerHTML += `<p>No ${meal.toLowerCase()} menu available today.</p>`;
                        return;
                    }

                    mealItems.forEach(item => {
                        const card = document.createElement("div");
                        card.classList.add("card");
                        card.dataset.rating = 0;
                        card.dataset.item = item.mess_menu;
                        card.dataset.meal = meal;

                        card.innerHTML = `
                            <h4>${item.mess_menu}</h4>
                            <p>${item.category || ""}</p>
                            <div class="stars">
                                <span class="star">&#9733;</span>
                                <span class="star">&#9733;</span>
                                <span class="star">&#9733;</span>
                                <span class="star">&#9733;</span>
                                <span class="star">&#9733;</span>
                            </div>
                            <button class="submit-btn" disabled>Submit Rating</button>
                            <p class="last-rated" style="font-size:0.9em;color:green;"></p>
                        `;

                        container.appendChild(card);

                        const stars = card.querySelectorAll(".star");
                        const submitBtn = card.querySelector(".submit-btn");
                        const lastRated = card.querySelector(".last-rated");

                        // Hover & click effect
                        stars.forEach((star, idx) => {
                            star.addEventListener("mouseenter", () => {
                                stars.forEach((s, i) => s.style.color = i <= idx ? "#ff7f32" : "#ccc");
                            });
                            star.addEventListener("mouseleave", () => {
                                const rating = parseInt(card.dataset.rating);
                                stars.forEach((s, i) => s.style.color = i < rating ? "#ff7f32" : "#ccc");
                            });
                            star.addEventListener("click", () => {
                                card.dataset.rating = idx + 1;
                                submitBtn.disabled = false;
                                stars.forEach((s, i) => s.style.color = i <= idx ? "#ff7f32" : "#ccc");
                            });
                        });

                        // Submit rating
                        submitBtn.addEventListener("click", (e) => {
                            e.preventDefault();
                            const rating = parseInt(card.dataset.rating);
                            if (!rating) { alert("Select rating first"); return; }

                            fetch("http://127.0.0.1:5000/submit-rating", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ register_no: regno, item_name: item.mess_menu, rating:rating,meal_type:card.dataset.meal})
                            })
                                .then(res => res.json())
                                .then(d => {
                                    alert(d.message);
                                    submitBtn.disabled = true;
                                    lastRated.innerText = `Last rated on: ${new Date().toLocaleTimeString()}`;
                                    loadHistory();
                                })
                                .catch(err => console.error("Rating submit error:", err));
                        });
                    });
                });
            })
            .catch(err => console.error("Menu fetch error:", err));
    }

    // ===== LOAD STUDENT HISTORY =====
   function loadHistory() {
    const container = document.getElementById("history-container");
    if (!container) return;

    // ✅ STEP 3 ADD THIS HERE
    container.innerHTML = "<p>Loading...</p>";

    fetch(`http://127.0.0.1:5000/get-history/${regno}`)
        .then(res => res.json())
        .then(data => {

            // ✅ CLEAR AFTER DATA ARRIVES
            container.innerHTML = "";

            if (!data || data.length === 0) {
                container.innerHTML = "<p>No recent activity found.</p>";
                return;
            }

            // Sort by latest date
            data.sort((a, b) => new Date(b.date) - new Date(a.date));

            data.forEach(item => {
                if (!item.rating || item.rating <= 0) return;

                let stars = "";
                for (let i = 1; i <= 5; i++) {
                    stars += i <= item.rating ? "&#9733;" : "&#9734;";
                }

                const date = item.date 
                    ? new Date(item.date).toLocaleDateString("en-IN") 
                    : "";

                const card = document.createElement("div");
                card.classList.add("card");

                card.innerHTML = `
                    <h3>${item.item_name}</h3>
                    <p><strong>Meal:</strong> ${item.meal_type || "N/A"}</p>
                    <p><strong>Rating:</strong> ${stars} (${item.rating})</p>
                    <p><strong>Date:</strong> ${date}</p>
                `;

                container.appendChild(card);
            });
        })
        .catch(err => {
            container.innerHTML = "<p>Error loading history.</p>";
            console.error("History fetch error:", err);
        });
}
//========================Feedback==============================
const feedbackForm = document.querySelector(".feedback-box form");

if (feedbackForm) {

    feedbackForm.addEventListener("submit", function(e){

        e.preventDefault();

        const meal = feedbackForm.querySelector("input[name='meal_type']").value;
        const feedback = feedbackForm.querySelector("textarea[name='feedback']").value.trim();

        const today = new Date().toISOString().split("T")[0];

        if(!feedback){
            alert("Enter feedback");
            return;
        }

        fetch("http://127.0.0.1:5000/submit-feedback",{
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
                register_no: regno,
                meal_type: meal,
                feedback: feedback,
                date: today
            })
        })
        .then(res => res.json())
        .then(data => {
            alert(data.message || "Feedback submitted");
            feedbackForm.reset();
        })
        .catch(err => {
            console.error("Feedback error:", err);
            alert("Error submitting feedback");
        });

    });

}

    // ===== MENU REQUEST SUBMIT =====
    const requestForm = document.querySelector(".request-box form");
    if (requestForm) {
        requestForm.addEventListener("submit", e => {
            e.preventDefault();
            const meal = requestForm.querySelector("input[name='meal_type']").value;
            const message = requestForm.querySelector("textarea[name='message']").value;
            if (!message) { alert("Enter request"); return; }
            fetch("http://127.0.0.1:5000/submit-menu-request", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ register_no: regno, meal_type: meal, message })
            })
                .then(res => res.json())
                .then(d => { alert(d.message || "Request submitted"); requestForm.reset(); })
                .catch(err => console.error("Request error:", err));
        });
    }

    // ===== LOGOUT =====
    document.getElementById("logout-btn")?.addEventListener("click", () => {
        localStorage.removeItem("register_no");
        window.location.href = "login.html";
    });

    // ===== INITIAL LOAD =====
    loadTodayMenu();
    loadHistory();
});