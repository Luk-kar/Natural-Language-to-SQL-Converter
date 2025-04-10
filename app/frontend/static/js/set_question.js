function setQuestion(query) {
    document.getElementById('questionInput').value = query;
}

document.addEventListener('DOMContentLoaded', function () {

    // Show loading overlay on form submission
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function () {
            const overlay = document.getElementById('loading-overlay');
            if (overlay) {
                overlay.style.display = 'flex';
            }
        });
    }
});