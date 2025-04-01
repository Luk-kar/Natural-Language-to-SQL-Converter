function processSqlClauses(preElement) {
    const sql = preElement.textContent;
    const clauses = parseSqlClauses(sql);

    // Clear existing content and rebuild with clause spans
    preElement.innerHTML = clauses.map(clause =>
        `<span class="sql-clause" data-clause-type="${clause.type}" title="placeholder">${clause.text}</span>`
    ).join(' ');

    // Add this to prevent text selection
    preElement.style.userSelect = 'none';
    preElement.style.webkitUserSelect = 'none';
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