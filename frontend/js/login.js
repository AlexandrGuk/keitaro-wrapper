const form = document.querySelector("#login-form");

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearError();
    const button = form.querySelector("button[type=submit]");
    button.disabled = true;
    try {
        await api("api/login", {
            method: "POST",
            allowUnauthorized: true,
            body: {
                username: document.querySelector("#username").value,
                password: document.querySelector("#password").value,
            },
        });
        location.href = "./";
    } catch (error) {
        showError(error);
        button.disabled = false;
    }
});
