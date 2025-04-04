function processSqlClauses(preElement) {
    const sql = preElement.textContent;
    // parseSqlClauses now returns an array of strings.
    const clauses = parseSqlClauses(sql);

    // Clear existing content and rebuild by mapping each clause string
    preElement.innerHTML = clauses.map(clause => {
        // Wrap each clause string in a span element.
        // A default type "CLAUSE" is used in data-clause-type.
        return `<span class="sql-clause" data-clause-type="CLAUSE" title="placeholder">${clause}</span>`;
    }).join(''); // Join without adding extra spaces

    // Prevent text selection on these spans
    preElement.style.userSelect = 'none';
    preElement.style.webkitUserSelect = 'none';
}

function splitSQL(sql) {
    // List of SQL clauses
    const list_clauses = [
        "OVER", "WITH", "SELECT", "FROM", "WHERE", "INNER\\s+JOIN", "LEFT\\s+JOIN", "RIGHT\\s+JOIN",
        "FULL\\s+JOIN", "CROSS\\s+JOIN", "NATURAL\\s+JOIN", "JOIN", "ORDER\\s+BY", "GROUP\\s+BY",
        "HAVING", "LIMIT", "OFFSET", "UNION\\s+ALL", "UNION", "INTERSECT", "EXCEPT", "FETCH", "EXCLUDE"
    ];

    const uniqueClauses = Array.from(new Set(list_clauses));

    // Adjust clause patterns to include leading whitespace or start of string, ensuring the split includes necessary spaces
    const clausePatterns = uniqueClauses.map(clause => `(?:\\s+|^)${clause}\\b`);

    // Join the individual patterns using the OR operator (|)
    const patternString = clausePatterns.join("|");

    // Build a regular expression that uses a positive lookahead to split the string
    // at each position where one of the clauses starts, including preceding whitespace
    const clauseRegex = new RegExp(`(?=${patternString})`, "gi");

    // Split the SQL query using the generated regex and return the parts.
    return sql.split(clauseRegex);
}

function splitSQLWithWindowFunctions(sql) {
    const parts = [];
    let currentIndex = 0;

    while (currentIndex < sql.length) {
        // Look for the pattern: function(...) OVER (
        const windowStartRegex = /(\w+)\s*\([^)]*\)\s+OVER\s*\(/gi;
        const match = windowStartRegex.exec(sql.slice(currentIndex));
        if (!match) {
            // Add remaining part if no more window functions
            parts.push(sql.slice(currentIndex));
            break;
        }

        const windowStart = currentIndex + match.index;
        const beforeWindow = sql.slice(currentIndex, windowStart);
        if (beforeWindow) {
            parts.push(beforeWindow);
        }

        // Find the end of the OVER clause's parentheses
        let parenDepth = 1;
        let index = windowStart + match[0].length; // Position after 'OVER ('
        while (index < sql.length && parenDepth > 0) {
            if (sql[index] === '(') parenDepth++;
            else if (sql[index] === ')') parenDepth--;
            index++;
        }
        let windowEnd = index;

        // Check for AS alias and include it
        const remainingAfterParen = sql.slice(windowEnd);
        const aliasRegex = /\s+AS\s+([\w_]+|"[^"]*"|'[^']*')\b/gi;
        const aliasMatch = aliasRegex.exec(remainingAfterParen);
        if (aliasMatch) {
            windowEnd += aliasMatch.index + aliasMatch[0].length;
        }

        const windowFunc = sql.slice(windowStart, windowEnd);
        parts.push(windowFunc);

        currentIndex = windowEnd;
    }

    return parts.filter(part => part.trim() !== '');
}

function parseSqlClauses(sql) {
    const windowParts = splitSQLWithWindowFunctions(sql);

    let result = [];
    for (const part of windowParts) {
        // Check if the part is a window function by looking for "OVER (" pattern
        if (/\bOVER\s*\(/i.test(part)) {
            result.push(part);
        } else {
            // Split the non-window part into SQL clauses
            const clauses = splitSQL(part);
            result.push(...clauses);
        }
    }
    // Filter out any empty or whitespace-only strings and return
    return result.filter(p => p.trim() !== '');
}