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
            const sqlContainer = this.closest('.sql-container');
            const pre = sqlContainer.querySelector('.sql-display');
            if (pre) {
                pre.textContent = fullSql;
                this.style.display = 'none';

                // Create the info icon
                const infoIcon = document.createElement('span');
                infoIcon.textContent = 'ⓘ';
                infoIcon.className = 'sql-info-icon';

                // Create a flex container to hold the pre and icon
                const wrapper = document.createElement('div');
                wrapper.className = 'sql-display-wrapper';

                // Replace the pre with the wrapper and append pre and icon
                pre.parentNode.insertBefore(wrapper, pre);
                wrapper.appendChild(pre);
                wrapper.appendChild(infoIcon);
            }
        });
    });
});