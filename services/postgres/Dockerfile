FROM postgres:15.8

# Install Python and required dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Add build arguments
ARG DB_USER_READONLY
ARG DB_PASSWORD_READONLY
ARG DB_NAME

# Set environment variables for build time
ENV DB_USER_READONLY=${DB_USER_READONLY}
ENV DB_PASSWORD_READONLY=${DB_PASSWORD_READONLY}
ENV DB_NAME=${DB_NAME}

# Copy the SQL template and the entrypoint script into the init directory
COPY init.sh /docker-entrypoint-initdb.d/init.sh

# Set permissions
RUN chmod +x /docker-entrypoint-initdb.d/init.sh && \
    chown -R postgres:postgres /docker-entrypoint-initdb.d/