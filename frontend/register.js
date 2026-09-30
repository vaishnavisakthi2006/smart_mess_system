document.getElementById("registerForm").addEventListener("submit", function(e) {

    e.preventDefault();

    const register_no = document.getElementById("register_no").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!register_no || !password) {
        alert("Please enter register number and password");
        return;
    }

    fetch("http://127.0.0.1:5000/register", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ register_no, password })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        window.location.href = "login.html";
    })
    .catch(error => {
        console.error(error);
        alert("Error connecting to server");
    });

});