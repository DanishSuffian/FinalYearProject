//---------------------------------------Login Message-------------------------------------

document.addEventListener('DOMContentLoaded', function() {
    const verifyMessage = sessionStorage.getItem('loginSuccessMessage');
    if (verifyMessage) {
        iziToast.success({
            title: 'Success',
            message: verifyMessage,
            position: 'topRight',
            theme: 'bootstrap',
            messageClass: 'iziToast-message',
            titleClass: 'iziToast-title'
        });
        sessionStorage.removeItem('loginSuccessMessage');
    }
});

//-------------------------------------Count Info Display-----------------------------------

document.addEventListener('DOMContentLoaded', function() {
    function formatNumber(number) {
        if (number >= 1000) {
            return (number / 1000).toFixed(0) + 'K' + '<span>+</span>';
        }
        return number;
    }

    fetch('/get_counts')
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            iziToast.error({
                title: 'Error',
                message: data.error,
                position: 'topRight',
                theme: 'bootstrap',
                messageClass: 'iziToast-message',
                titleClass: 'iziToast-title'
            });
        } else {
            document.getElementById('user_count').innerHTML = formatNumber(data.user_count);
            document.getElementById('company_count').innerHTML = formatNumber(data.company_count);
            document.getElementById('review_count').innerHTML = formatNumber(data.review_count);
        }
    })
    .catch(error => {
        console.error('Error fetching counts:', error);
        iziToast.error({
            title: 'Error',
            message: 'An error occurred while fetching counts',
            position: 'topRight',
            theme: 'bootstrap',
            messageClass: 'iziToast-message',
            titleClass: 'iziToast-title'
        });
    });
});

//------------------------------------Autocomplete Search-----------------------------------

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const autocompleteDropdown = document.getElementById('autocompleteDropdown');

    searchInput.addEventListener('input', function() {
        const query = this.value.trim();
        if (query === '') {
            autocompleteDropdown.innerHTML = '';
            return;
        }

        fetch(`/autocomplete-options?query=${query}`)
            .then(response => response.json())
            .then(data => {
                if (data.length > 0) {
                    const dropdownContent = data.map(option => `<div class="autocomplete-option">${option}</div>`).join('');
                    autocompleteDropdown.innerHTML = dropdownContent;
                } else {
                    autocompleteDropdown.innerHTML = '';
                }
            })
            .catch(error => {
                console.error('Error fetching autocomplete options:', error);
            });
    });

    autocompleteDropdown.addEventListener('click', function(event) {
        const clickedOption = event.target.closest('.autocomplete-option');
        if (clickedOption) {
            searchInput.value = clickedOption.textContent.trim();
            autocompleteDropdown.innerHTML = '';
        }
    });
});

//-----------------------------------------ANIMATION----------------------------------------

//Scroll Navigation Bar
function scrollHeader(){
    const header = document.getElementById('header');
    if (window.scrollY >= 50) {
        header.classList.add('scroll-header');
    } else {
        header.classList.remove('scroll-header');
    }
}
window.addEventListener('scroll', scrollHeader);

//Swipe Animation swiper.js
var swiperRecommended = new Swiper(".recommended__container", {
    spaceBetween: 32,
    grabCursor: true,
    centeredSlides: false,
    slidesPerView: 'auto',
    loop: false,
    initialSlide: 0,

    navigation: {
        nextEl: ".swiper-button-next",
        prevEl: ".swiper-button-prev",
    },
 });

// Show Scroll Up
function scrollUp() {
    const scrollUp = document.getElementById('scroll-up');
    if(this.scrollY >= 350) scrollUp.classList.add('show-scroll'); else scrollUp.classList.remove('show-scroll')
}
window.addEventListener('scroll', scrollUp)

// Dark Light Theme
const themeButton = document.getElementById('theme-button')
const darkTheme = 'dark-theme'
const iconTheme = 'ri-sun-line'

const selectedTheme = localStorage.getItem('selected-theme')
const selectedIcon = localStorage.getItem('selected-icon')

const getCurrentTheme = () => document.body.classList.contains(darkTheme) ? 'dark' : 'light'
const getCurrentIcon = () => themeButton.classList.contains(iconTheme) ? 'ri-moon-line' : 'ri-sun-line'

if (selectedTheme) {
    document.body.classList[selectedTheme === 'dark' ? 'add' : 'remove'](darkTheme)
    themeButton.classList[selectedIcon === 'ri-moon-line' ? 'add' : 'remove'](iconTheme)
}

themeButton.addEventListener('click', () => {
    document.body.classList.toggle(darkTheme)
    themeButton.classList.toggle(iconTheme)

    localStorage.setItem('selected-theme', getCurrentTheme())
    localStorage.setItem('selected-icon', getCurrentIcon())
})

// Scroll Section Active Link
document.addEventListener('DOMContentLoaded', function() {
    var currentPath = window.location.pathname;
    var navLinks = document.querySelectorAll('.nav__link');

    navLinks.forEach(function(link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});

//--------------------------------------Preferences Form-------------------------------------

document.addEventListener('DOMContentLoaded', function() {
    const submitButton = document.getElementById('submitReview');

    submitButton.addEventListener('click', function(event) {
        event.preventDefault();

        const form = document.getElementById('preferencesForm');
        const formData = new FormData(form);

        const data = {};
        formData.forEach((value, key) => {
            data[key] = value;
        });

        const selectedCompany = document.querySelector('.company-review input[type="radio"]:checked');
        if (!selectedCompany) {
            iziToast.error({
                title: 'Error',
                message: 'Please select a company before proceeding',
                position: 'topRight',
                theme: 'bootstrap',
                messageClass: 'iziToast-message',
                titleClass: 'iziToast-title'
            });
            return;
        }
        data.company = selectedCompany.value;

        console.log("Selected company:", selectedCompany.value);

        bullet[current - 1].classList.add("active");
        progressText[current - 1].classList.add("active");
        progressCheck[current - 1].classList.add("active");
        current += 1;

        fetch('/submit_interaction', {
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
            if (data.includes('Preferences Saved')) {
                iziToast.success({
                    title: 'Success',
                    message: 'Preferences Saved',
                    position: 'topRight',
                    theme: 'bootstrap',
                    messageClass: 'iziToast-message',
                    titleClass: 'iziToast-title'
                });

                setTimeout(() => {
                    location.reload();
                }, 2000);
            } else {
                throw new Error('Submission failed');
            }
        })
        .catch(error => {
            iziToast.error({
                title: 'Error',
                message: error.message,
                position: 'topRight',
                theme: 'bootstrap',
                messageClass: 'iziToast-message',
                titleClass: 'iziToast-title'
            });
        });
    });

    const slidePage = document.querySelector(".slidePage");
    const firstNextBtn = document.querySelector(".nextBtn button");
    const secondPrevBtn = document.querySelector(".prev-1");
    const secondNextBtn = document.querySelector(".next-1");
    const thirdPrevBtn = document.querySelector(".prev-2");
    const progressText = document.querySelectorAll(".step p");
    const progressCheck = document.querySelectorAll(".step .check");
    const bullet = document.querySelectorAll(".step .bullet");
    let current = 1;

    firstNextBtn.addEventListener("click", function(event){
        event.preventDefault();
        const location = document.getElementById("location").value;
        const type = document.getElementById("type").value;
        const scope = document.getElementById("scope").value;

        if (!location || !type || !scope) {
            iziToast.error({
                title: 'Error',
                message: 'Complete all required preferences to proceed',
                position: 'topRight',
                theme: 'bootstrap',
                messageClass: 'iziToast-message',
                titleClass: 'iziToast-title'
            });
            return;
        }

        slidePage.style.marginLeft = "-25%";
        bullet[current - 1].classList.add("active");
        progressText[current - 1].classList.add("active");
        progressCheck[current - 1].classList.add("active");
        current += 1;
    });

    secondPrevBtn.addEventListener("click", function(event){
        event.preventDefault();
        slidePage.style.marginLeft = "0%";
        bullet[current - 2].classList.remove("active");
        progressText[current - 2].classList.remove("active");
        progressCheck[current - 2].classList.remove("active");
        current -= 1;
    });

    secondNextBtn.addEventListener("click", function(event) {
        event.preventDefault();
        slidePage.style.marginLeft = "-50%";
        bullet[current - 1].classList.add("active");
        progressText[current - 1].classList.add("active");
        progressCheck[current - 1].classList.add("active");
        current += 1;

        const location = document.getElementById("location").value;
        const type = document.getElementById("type").value;
        const scope = document.getElementById("scope").value;
        const company_description = document.getElementById("company_description").value;

        const data = { location, type, scope, company_description };

        fetch('/generate_recommendations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            const recommendationsContainer = document.getElementById("recommendationsContainer");
            recommendationsContainer.innerHTML = "";
            data.recommendations.forEach(company => {
                const radio = document.createElement("input");
                radio.type = "radio";
                radio.name = "company";
                radio.id = "company_" + company.company_id;
                radio.value = company.company_id;

                const label = document.createElement("label");
                label.htmlFor = "company_" + company.company_id;
                label.textContent = `Company Name: ${company.company_name}, Location: ${company.company_location}, Type: ${company.company_type}, Similarity Score: ${company.similarity_score.toFixed(2)}`;

                const div = document.createElement("div");
                div.classList.add("company-review");
                div.appendChild(radio);
                div.appendChild(label);

                recommendationsContainer.appendChild(div);
            });
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });

    thirdPrevBtn.addEventListener("click", function(event){
        event.preventDefault();
        slidePage.style.marginLeft = "-25%";
        bullet[current - 2].classList.remove("active");
        progressText[current - 2].classList.remove("active");
        progressCheck[current - 2].classList.remove("active");
        current -= 1;
    });
});
