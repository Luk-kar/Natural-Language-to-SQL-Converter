#!/usr/bin/env bash
set -e

echo "Starting database initialization process..."

echo "Checking/Creating read-only user '${DB_USER_READONLY}'..."
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$ BEGIN
        IF NOT EXISTS (
            SELECT FROM pg_catalog.pg_roles 
            WHERE rolname = '${DB_USER_READONLY}'
        ) THEN
            CREATE ROLE ${DB_USER_READONLY} WITH LOGIN PASSWORD '${DB_PASSWORD_READONLY}';
        END IF;
    END \$\$;
EOSQL

echo "Granting CONNECT privileges on ${DB_NAME}..."
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    GRANT CONNECT ON DATABASE ${DB_NAME} TO ${DB_USER_READONLY};
EOSQL

echo "Granting USAGE on public schema..."
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    GRANT USAGE ON SCHEMA public TO ${DB_USER_READONLY};
EOSQL

echo "Granting SELECT on existing tables..."
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO ${DB_USER_READONLY};
EOSQL

echo "Setting default privileges for future tables..."
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ${DB_USER_READONLY};
EOSQL

echo "Creating customers table..."
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE TABLE customers (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        email VARCHAR(100),
        city VARCHAR(50)
    );
EOSQL

echo "Adding column comments context..."
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    COMMENT ON COLUMN customers.id IS 'A unique identifier for the customer.';
    COMMENT ON COLUMN customers.name IS 'Stores the customer''s full name, can be non-unique. Note that in many cultures the name may be composed differently or may not clearly split into "first" and "last" components.';
    COMMENT ON COLUMN customers.email IS 'A unique identifier for the customer.';
    COMMENT ON COLUMN customers.city IS 'A categorical variable, meaning it belongs to a finite set of possible values (e.g., "New York", "London", "Paris").';
EOSQL

echo "Inserting initial sample data (3 records)..."
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    INSERT INTO customers (name, email, city)
    VALUES
        ('John Doe', 'john@example.com', 'New York'),
        ('Jane Smith', 'jane@example.com', 'London'),
        ('Bob Wilson', 'bob@example.com', 'Paris');
EOSQL

echo "Generating 100 additional sample records..."
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    INSERT INTO customers (name, email, city)
    SELECT
        'Customer ' || gs,
        'customer' || gs || '@example.com',
        CASE
            WHEN gs % 3 = 0 THEN 'New York'
            WHEN gs % 3 = 1 THEN 'London'
            ELSE 'Paris'
        END
    FROM generate_series(1, 100) AS gs;
EOSQL

echo "Database initialization completed successfully!"