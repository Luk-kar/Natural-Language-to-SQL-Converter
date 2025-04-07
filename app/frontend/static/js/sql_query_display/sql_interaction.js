function initializeSqlInfoIcons() {

    document.querySelectorAll('.sql-info-icon').forEach(icon => {
        icon.addEventListener('click', function (e) {
            e.stopPropagation();
            const pre = this.closest('.sql-display-wrapper').querySelector('.sql-display');
            if (pre) wrapSqlClausesInHtml(pre);
        });
    });

}

function initializeQueryExpansion() {

    document.querySelectorAll('.show-full-query').forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            const fullSql = this.getAttribute('data-full');
            const sqlContainer = this.closest('.sql-container');
            const pre = sqlContainer.querySelector('.sql-display');
            if (pre) {
                pre.textContent = fullSql;
                this.style.display = 'none';

                const infoIcon = document.createElement('span');
                infoIcon.textContent = 'ⓘ';
                infoIcon.className = 'sql-info-icon';
                infoIcon.addEventListener('click', function (e) {
                    e.stopPropagation();
                    wrapSqlClausesInHtml(pre);
                });

                const wrapper = sqlContainer.querySelector('.sql-display-wrapper');
                if (wrapper) wrapper.appendChild(infoIcon);
            }
        });
    });

}

document.addEventListener('DOMContentLoaded', () => {

    initializeSqlInfoIcons();
    initializeQueryExpansion();

});