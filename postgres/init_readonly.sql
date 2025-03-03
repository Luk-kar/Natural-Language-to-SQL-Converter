-- Create a read-only user
DO $$ BEGIN IF NOT EXISTS (
    SELECT
    FROM
        pg_catalog.pg_roles
    WHERE
        rolname = 'readonly_user'
) THEN CREATE ROLE readonly_user WITH LOGIN PASSWORD 'readonly_password';

END IF;

END $$;

-- Grant SELECT privileges on all existing tables in 'business' database
GRANT CONNECT ON DATABASE business TO readonly_user;

GRANT USAGE ON SCHEMA public TO readonly_user;

GRANT
SELECT
    ON ALL TABLES IN SCHEMA public TO readonly_user;

-- Ensure future tables are also accessible
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT
SELECT
    ON TABLES TO readonly_user;

-- Init sample db
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    city VARCHAR(50)
);

INSERT INTO
    customers (name, email, city)
VALUES
    ('John Doe', 'john@example.com', 'New York'),
    ('Jane Smith', 'jane@example.com', 'London'),
    ('Bob Wilson', 'bob@example.com', 'Paris');

INSERT INTO
    customers (name, email, city)
SELECT
    'Customer ' || gs,
    'customer' || gs || '@example.com',
    CASE
        WHEN gs % 3 = 0 THEN 'New York'
        WHEN gs % 3 = 1 THEN 'London'
        ELSE 'Paris'
    END
FROM
    generate_series(1, 100) AS gs;
