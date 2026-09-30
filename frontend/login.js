document.addEventListener("DOMContentLoaded", function () {

    // =============================
    // TAB SWITCH (Student / Admin)
    // =============================

    const studentTab = document.getElementById("student-tab");
    const adminTab = document.getElementById("admin-tab");

    const studentForm = document.getElementById("student-form");
    const adminForm = document.getElementById("admin-form");

    studentTab.addEventListener("click", function () {
        studentForm.style.display = "block";
        adminForm.style.display = "none";
        studentTab.classList.add("active-tab");
        adminTab.classList.remove("active-tab");
    });

    adminTab.addEventListener("click", function () {
        studentForm.style.display = "none";
        adminForm.style.display = "block";
        adminTab.classList.add("active-tab");
        studentTab.classList.remove("active-tab");
    });


    // =============================
    // STUDENT LOGIN
    // =============================

    document.getElementById("student-login-btn").addEventListener("click", function () {

        const regno = document.getElementById("student-username").value.trim();
        const password = document.getElementById("student-password").value.trim();

        if (!regno || !password) {
            alert("Please enter Register Number and Password");
            return;
        }

        fetch("http://127.0.0.1:5000/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                register_no: regno,
                password: password
            })
        })
        .then(res => res.json())
        .then(data => {

            console.log("Server response:", data);

            if (data.status === "success") {

    localStorage.setItem("register_no", regno);
    window.location.href = "rating.html";

} 
else if (data.status === "pending") {

    alert("Your registration is not approved yet!");

} 
else if (data.status === "rejected") {

    alert("Your registration was rejected by admin!");

} 
else {

    alert(data.message || "Invalid login credentials");

}

        })
        .catch(error => {
            console.error("Error:", error);
            alert("Server error. Make sure backend is running.");
        });

    });


    document.getElementById("admin-login-btn").addEventListener("click", function () {

    const username = document.getElementById("admin-username").value.trim();
    const password = document.getElementById("admin-password").value.trim();

    if (!username || !password) {
        alert("Please enter Username and Password");
        return;
    }

    fetch("http://127.0.0.1:5000/admin_login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    })
    .then(res => res.json())
    .then(data => {

        console.log("Admin response:", data);

        if (data.status === "success") {

            window.location.href = "admin_dashboard.html";

        } else {

            alert(data.message || "Invalid admin credentials");

        }

    })
    .catch(error => {
        console.error("Error:", error);
        alert("Server error. Make sure backend is running.");
    });

});

});