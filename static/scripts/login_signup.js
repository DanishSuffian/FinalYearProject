var pass = document.getElementById("signup_password");
var confirmPass = document.getElementById("confirm_password");
var msg = document.getElementById("message");
var str = document.getElementById("strength");

document.addEventListener('DOMContentLoaded', function() {
    const passwordFields = document.querySelectorAll('input[type="password"]');
    const togglePasswordIcons = document.querySelectorAll('.password-toggle-icon i');

    togglePasswordIcons.forEach(icon => {
        icon.addEventListener('click', function () {
            const passwordField = this.parentNode.previousElementSibling;
            if (passwordField.type === "password") {
                passwordField.type = "text";
                this.classList.remove("ri-eye-line");
                this.classList.add("ri-eye-off-line");
            } else {
                passwordField.type = "password";
                this.classList.remove("ri-eye-off-line");
                this.classList.add("ri-eye-line");
            }
        });
    });
});

function displayPasswordStrength() {
    var strength = 0;

    if(pass.value.length > 0) {
        msg.style.display = "block";
        confirmPass.parentNode.style.marginTop = "30px";
    } else {
        msg.style.display = "none";
        confirmPass.parentNode.style.marginTop = "10px";
        pass.parentNode.style.borderColor = "transparent";
    }

    if(pass.value.length >= 8) {
        strength++;
    }
    if(/[a-z]/.test(pass.value)) {
        strength++;
    }
    if(/[A-Z]/.test(pass.value)) {
        strength++;
    }
    if(/\d/.test(pass.value)) {
        strength++;
    }
    if(/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(pass.value)) {
        strength++;
    }

    switch(strength) {
        case 1:
            str.innerHTML = "weak";
            pass.parentNode.style.borderColor = "#ff0000";
            msg.style.color = "#ff0000"
            break;
        case 2:
            str.innerHTML = "fair";
            pass.parentNode.style.borderColor = "#ffa500";
            msg.style.color = "#ffa500"
            break;
        case 3:
            str.innerHTML = "medium";
            pass.parentNode.style.borderColor = "#ffff00";
            msg.style.color = "#ffff00"
            break;
        case 4:
            str.innerHTML = "strong";
            pass.parentNode.style.borderColor = "#00ff00";
            msg.style.color = "#00ff00"
            break;
        case 5:
            str.innerHTML = "very strong";
            pass.parentNode.style.borderColor = "#006400";
            msg.style.color = "#006400"
            break;
        default:
            str.innerHTML = "";
            pass.parentNode.style.borderColor = "transparent";
            msg.style.color = "";
            break;
    }
}

pass.addEventListener('focus', () => {
    displayPasswordStrength();
});

pass.addEventListener('input', () => {
    displayPasswordStrength();
});

var otherInputs = document.querySelectorAll('input:not(#password)');
otherInputs.forEach(input => {
    input.addEventListener('focus', () => {
        msg.style.display = "none";
        confirmPass.parentNode.style.marginTop = "10px";
        pass.parentNode.style.borderColor = "transparent";
    });
});

document.getElementById('signup_form').addEventListener('submit', function(event) {
    event.preventDefault();

    var formData = new FormData(this);

    fetch('/signup', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            return response.text();
        } else {
            throw new Error('Network error. Please check your connection and try again');
        }
    })
    .then(data => {
        if (data.includes('All fields are required')) {
            iziToast.error({
                title: 'Error',
                message: 'All fields are required',
                position: 'topRight',
                theme: 'bootstrap',
                messageClass: 'iziToast-message',
                titleClass: 'iziToast-title'
            });
        } else if (data.includes('Password should be at least 6 characters long')) {
            iziToast.error({
                title: 'Error',
                message: 'Password should be at least 6 characters long',
                position: 'topRight',
                theme: 'bootstrap',
                messageClass: 'iziToast-message',
                titleClass: 'iziToast-title'
            });
        } else if (data.includes('Invalid email format')) {
            iziToast.error({
                title: 'Error',
                message: 'Invalid email format',
                position: 'topRight',
                theme: 'bootstrap',
                messageClass: 'iziToast-message',
                titleClass: 'iziToast-title'
            });
        } else if (data.includes('Passwords do not match')) {
            iziToast.error({
                title: 'Error',
                message: 'Passwords do not match',
                position: 'topRight',
                theme: 'bootstrap',
                messageClass: 'iziToast-message',
                titleClass: 'iziToast-title'
            });
        } else if (data.includes('Username is already taken')) {
            iziToast.error({
                title: 'Error',
                message: 'Username is already taken',
                position: 'topRight',
                theme: 'bootstrap',
                messageClass: 'iziToast-message',
                titleClass: 'iziToast-title'
            });
        } else if (data.includes('Email address is already taken')) {
            iziToast.error({
                title: 'Error',
                message: 'Email address is already taken',
                position: 'topRight',
                theme: 'bootstrap',
                messageClass: 'iziToast-message',
                titleClass: 'iziToast-title'
            });
        } else if (data.includes('An error occurred while signing up')) {
            iziToast.error({
                title: 'Error',
                message: 'An error occurred while signing up',
                position: 'topRight',
                theme: 'bootstrap',
                messageClass: 'iziToast-message',
                titleClass: 'iziToast-title'
            });
        } else if (data.includes('Sign up successful')) {
            sessionStorage.setItem('signupSuccessMessage', 'Please check your email to verify your account');
            location.reload();
        } else {
            throw new Error('Unexpected response from server');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

document.getElementById('login_form').addEventListener('submit', function(event) {
    event.preventDefault();

    var formData = new FormData(this);

    fetch('/login', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            return response.text();
        } else {
            throw new Error('Network error. Please check your connection and try again');
        }
    })
    .then(data => {
        if (data.includes('Incorrect username or password')) {
            iziToast.error({
                title: 'Error',
                message: 'Incorrect username or password',
                position: 'topRight',
                theme: 'bootstrap',
                messageClass: 'iziToast-message',
                titleClass: 'iziToast-title'
            });
        } else if (data.includes('Email is not verified')) {
            iziToast.error({
                title: 'Error',
                message: 'Email is not verified',
                position: 'topRight',
                theme: 'bootstrap',
                messageClass: 'iziToast-message',
                titleClass: 'iziToast-title'
            });
        } else if (data.includes('Login successful')) {
            window.location.href = '/dashboard';
            iziToast.success({
                title: 'Success',
                message: 'Login successful',
                position: 'topRight',
                theme: 'bootstrap',
                messageClass: 'iziToast-message',
                titleClass: 'iziToast-title'
            });
        } else {
            throw new Error('Unexpected response from server');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const verifyMessage = sessionStorage.getItem('signupSuccessMessage');
    if (verifyMessage) {
        iziToast.info({
            title: 'Info',
            message: verifyMessage,
            position: 'topRight',
            theme: 'bootstrap',
            messageClass: 'iziToast-message',
            titleClass: 'iziToast-title'
        });
        sessionStorage.removeItem('signupSuccessMessage');
    }
});
