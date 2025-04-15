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

echo "Creating pokemon table..."
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE TABLE pokemon (
        id_universal SERIAL PRIMARY KEY,
        id_pokemon INTEGER NOT NULL,
        Name VARCHAR(255),
        Form VARCHAR(255),
        Type1 VARCHAR(255),
        Type2 VARCHAR(255),
        Total INTEGER,
        HP INTEGER,
        Attack INTEGER,
        Defense INTEGER,
        "Sp. Atk" INTEGER,
        "Sp. Def" INTEGER,
        Speed INTEGER,
        Generation INTEGER
    );
EOSQL

echo "Adding column comments context..."
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    COMMENT ON COLUMN pokemon.id_universal IS 'Unique auto-incrementing identifier for each Pokémon entry';
    COMMENT ON COLUMN pokemon.id_pokemon IS 'Original Pokémon ID from game data (may have duplicates for different forms)';
    COMMENT ON COLUMN pokemon.Name IS 'The name of the Pokémon species. Names are unique per species but may vary by form.';
    COMMENT ON COLUMN pokemon.Form IS 'Specific form or variant (e.g., Mega Evolution, Regional Form). Empty indicates base form.';
    COMMENT ON COLUMN pokemon.Type1 IS 'Primary elemental type (e.g., Grass, Fire, Water) determining combat strengths/weaknesses.';
    COMMENT ON COLUMN pokemon.Type2 IS 'Secondary elemental type. Empty indicates single-type Pokémon.';
    COMMENT ON COLUMN pokemon.Total IS 'Sum of all base stats (HP, Attack, Defense, Sp. Atk, Sp. Def, Speed).';
    COMMENT ON COLUMN pokemon.HP IS 'Base health points indicating damage tolerance before fainting.';
    COMMENT ON COLUMN pokemon.Attack IS 'Base physical attack strength for damage calculation.';
    COMMENT ON COLUMN pokemon.Defense IS 'Base physical damage resistance against opponent attacks.';
    COMMENT ON COLUMN pokemon."Sp. Atk" IS 'Base special attack power for non-physical moves.';
    COMMENT ON COLUMN pokemon."Sp. Def" IS 'Base resistance against special move damage.';
    COMMENT ON COLUMN pokemon.Speed IS 'Determines turn order in battles. Higher values act first.';
    COMMENT ON COLUMN pokemon.Generation IS 'Game generation (1-7+) when the Pokémon was introduced.';
EOSQL

echo "Loading data from CSV..."
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    COPY pokemon (
        id_pokemon, 
        Name, 
        Form, 
        Type1, 
        Type2, 
        Total, 
        HP, 
        Attack, 
        Defense, 
        "Sp. Atk", 
        "Sp. Def", 
        Speed, 
        Generation
    )
    FROM '/data/pokemon.csv'
    WITH (FORMAT CSV, HEADER, FORCE_NOT_NULL (id_pokemon));
    
    DO \$\$
    BEGIN
        IF (SELECT COUNT(*) FROM pokemon) = 0 THEN
            RAISE EXCEPTION 'No data loaded from CSV file';
        END IF;
        
        -- Verify the ID column was properly mapped
        IF NOT EXISTS (SELECT 1 FROM pokemon WHERE id_pokemon IS NOT NULL) THEN
            RAISE EXCEPTION 'id_pokemon column contains only NULL values - CSV mapping may be incorrect';
        END IF;
    END \$\$;
EOSQL

echo "Database initialization completed successfully!"