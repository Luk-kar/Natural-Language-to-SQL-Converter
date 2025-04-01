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

                // Add click handler to info icon HERE
                infoIcon.addEventListener('click', function (e) {
                    e.stopPropagation();
                    processSqlClauses(pre);
                });

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
function processSqlClauses(preElement) {
    const sql = preElement.textContent;
    const clauses = parseSqlClauses(sql);

    // Clear existing content and rebuild with clause spans
    preElement.innerHTML = clauses.map(clause =>
        `<span class="sql-clause" data-clause-type="${clause.type}" title="placeholder">${clause.text}</span>`
    ).join(' ');
}

function parseSqlClauses(sql) {
    // Case-insensitive regex pattern for PostgreSQL clauses
    const clauseOrder = [
        { type: 'SELECT', regex: /SELECT.*?(?=\sFROM\b|\sWHERE\b|\sGROUP BY\b|\sORDER BY\b|\sLIMIT\b|$)/i },
        { type: 'FROM', regex: /FROM.*?(?=\sWHERE\b|\sGROUP BY\b|\sORDER BY\b|\sLIMIT\b|$)/i },
        { type: 'WHERE', regex: /WHERE.*?(?=\sGROUP BY\b|\sORDER BY\b|\sLIMIT\b|$)/i },
        { type: 'GROUP BY', regex: /GROUP BY.*?(?=\sORDER BY\b|\sLIMIT\b|$)/i },
        { type: 'ORDER BY', regex: /ORDER BY.*?(?=\sLIMIT\b|$)/i },
        { type: 'LIMIT', regex: /LIMIT.*/i }
    ];

    let remaining = sql;
    const clauses = [];

    for (const { type, regex } of clauseOrder) {
        const match = regex.exec(remaining);
        if (match) {
            clauses.push({ type, text: match[0].trim() });
            remaining = remaining.slice(match.index + match[0].length);
        }
    }

    return clauses;
}