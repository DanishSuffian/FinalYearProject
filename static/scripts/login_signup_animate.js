const login__btn = document.querySelector("#login__btn");
const signup__btn = document.querySelector("#signup__btn");
const container = document.querySelector(".container");
const login_form = document.getElementById("login_form");
const signup_form = document.getElementById("signup_form");

function clearInputFields(form) {
    const inputFields = form.querySelectorAll("input");
    inputFields.forEach((input) => {
        input.value = "";
    });
}

signup__btn.addEventListener("click", () => {
    container.classList.add("signup__mode");
    clearInputFields(login_form);
});

login__btn.addEventListener("click", () => {
    container.classList.remove("signup__mode");
    clearInputFields(signup_form);
});
