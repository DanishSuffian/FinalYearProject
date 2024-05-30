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

function scrollHeader(){
    const header = document.getElementById('header');
    if (window.scrollY >= 50) {
        header.classList.add('scroll-header');
    } else {
        header.classList.remove('scroll-header');
    }
}
window.addEventListener('scroll', scrollHeader);

var swiperRecommended = new Swiper(".recommended__container", {
    spaceBetween: 32,
    grabCursor: true,
    centeredSlides: true,
    slidesPerView: 'auto',
    loop: true,

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
