function initializeSqlInfoIcons() {

    document.querySelectorAll('.sql-info-icon').forEach(icon => {
        icon.addEventListener('click', function (e) {
            e.stopPropagation();
            const pre = this.closest('.sql-display-wrapper').querySelector('.sql-display');
            if (pre) {
                wrapSqlClausesInHtml(pre);
                fetchClauseExplanations(pre);
            };
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

function fetchClauseExplanations(preElement) {
    const clauses = preElement.querySelectorAll('.sql-clause');
    const fullSql = preElement.dataset.fullSql;

    clauses.forEach(clauseElement => {
        const clauseId = clauseElement.dataset.clauseId;
        const clauseText = clauseElement.textContent;

        fetch('/generate_clause_explanation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                clause: clauseText,
                fullSql: fullSql,
                clauseId: clauseId
            }),
        })
            .then(response => response.json())
            .then(data => {
                const targetClause = preElement.querySelector(`[data-clause-id="${data.clauseId}"]`);
                if (targetClause && data.explanation) {
                    targetClause.title = data.explanation;
                }
            })
            .catch(error => console.error('Error:', error));
    });
}

document.addEventListener('DOMContentLoaded', () => {

    initializeSqlInfoIcons();
    initializeQueryExpansion();

});