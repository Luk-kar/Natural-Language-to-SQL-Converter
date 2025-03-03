FROM postgres:15.8

# Install PostGIS and the associated PostgreSQL extension
RUN apt-get update && \
    apt-get install -y --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

COPY init_readonly.sql /docker-entrypoint-initdb.d/

# Ensure the init script is executable
RUN chmod +x /docker-entrypoint-initdb.d/init_readonly.sql
