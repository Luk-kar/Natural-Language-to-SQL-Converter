FROM postgres:15.8

# Install PostGIS and the associated PostgreSQL extension
RUN apt-get update && \
    apt-get install -y --no-install-recommends gettext && \
    rm -rf /var/lib/apt/lists/*

# Copy the SQL template and the entrypoint script into the init directory
COPY init_readonly.sql.template /docker-entrypoint-initdb.d/
COPY init.sh /docker-entrypoint-initdb.d/

# Ensure the init script is executable
RUN chmod +x /docker-entrypoint-initdb.d/init.sh && \
    chown -R postgres:postgres /docker-entrypoint-initdb.d/