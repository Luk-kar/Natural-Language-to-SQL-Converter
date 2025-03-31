function setQuestion(query) {
    document.getElementById('questionInput').value = query;
}

function toggleSqlExpansion(element) {
    element.classList.toggle('expanded');
}

document.addEventListener('DOMContentLoaded', function () {
    // Expand SQL query on click
    document.querySelectorAll('.show-full-query').forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            const fullSql = this.getAttribute('data-full');
            const pre = this.closest('.sql-container').querySelector('.sql-display');
            if (pre) {
                pre.textContent = fullSql;
                this.style.display = 'none';
            }
        });
    });
});