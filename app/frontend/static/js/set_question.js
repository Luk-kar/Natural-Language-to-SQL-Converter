function setQuestion(query) {
    showLoadingOverlay();
    document.getElementById('questionInput').value = query;
    document.querySelector('form').submit();
}

document.addEventListener('DOMContentLoaded', function () {

    // Show loading overlay on form submission
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function () {
            showLoadingOverlay();
        });
    }
});