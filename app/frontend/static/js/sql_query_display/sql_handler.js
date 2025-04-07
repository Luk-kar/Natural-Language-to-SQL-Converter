/**
 
 * @param {HTMLElement} preElement - The HTML element (typically a <pre> element) containing the SQL query text.
 */
function wrapSqlClausesInHtml(preElement) {
    const sql = preElement.dataset.fullSql;
    const clauses = extractSqlClausesWithWindows(sql);

    preElement.innerHTML = clauses.map((clause, index) => {
        return `<span class="sql-clause" 
                      data-clause-id="${index}" 
                      data-clause-type="CLAUSE" 
                      title="Loading...">${clause}</span>`;
    }).join('');

    preElement.style.userSelect = 'none';
    preElement.style.webkitUserSelect = 'none';
}

function splitSqlByClauses(sql) {

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

/**
 * Splits an SQL query string into an array of clauses based on a set of SQL keywords.
 *
 * The function defines a list of common SQL clauses and generates a regular expression pattern to split
 * the SQL query string at each occurrence of these clauses. It handles potential whitespace issues by
 * including leading whitespace or the start of the string in the pattern.
 *
 * @param {string} sql - The SQL query string to be split into clauses.
 * @returns {string[]} An array of SQL clause strings.
 */
function splitSqlWithWindowHandling(sql) {

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

/**
 * Splits an SQL query string into parts, specifically handling window functions separately.
 *
 * This function iterates over the SQL query and searches for window function patterns (i.e., functions
 * followed by an OVER clause). It isolates the window function, including any alias (AS ...), and collects
 * all parts of the SQL query accordingly. It returns an array of SQL string parts where each part is either
 * a window function or a regular clause segment.
 *
 * @param {string} sql - The SQL query string that may include window functions.
 * @returns {string[]} An array of SQL string parts, each representing a window function or a clause segment.
 */
function extractSqlClausesWithWindows(sql) {

    const windowParts = splitSqlWithWindowHandling(sql);

    let result = [];
    for (const part of windowParts) {
        // Check if the part is a window function by looking for "OVER (" pattern
        if (/\bOVER\s*\(/i.test(part)) {
            result.push(part);
        } else {
            // Split the non-window part into SQL clauses
            const clauses = splitSqlByClauses(part);
            result.push(...clauses);
        }
    }
    // Filter out any empty or whitespace-only strings and return
    return result.filter(p => p.trim() !== '');
}