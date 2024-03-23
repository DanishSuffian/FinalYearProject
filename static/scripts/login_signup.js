const login__btn = document.querySelector("#login__btn");
const signup__btn = document.querySelector("#signup__btn");
const container = document.querySelector(".container");

signup__btn.addEventListener("click", () => {
    container.classList.add("signup__mode");
});

login__btn.addEventListener("click", () => {
    container.classList.remove("signup__mode");
});
