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
            throw new Error('Network response was not ok');
        }
    })
    .then(data => {
        if (data.includes('This email is already used')) {
            iziToast.error({
                title: 'Error',
                message: 'This email is already used',
                position: 'topRight',
                theme: 'bootstrap',
                messageClass: 'iziToast-message',
                titleClass: 'iziToast-title'
            });
        } else {
            window.location.href = '/dashboard';
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

document.getElementsByClassName('close')[0].addEventListener('click', function() {
    document.getElementById('errorModal').style.display = 'none';
});
