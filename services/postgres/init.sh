#!/bin/sh
set -e

# Use envsubst to substitute environment variables in the SQL template.
# The resulting file is placed in the same directory so that PostgreSQL will run it.
envsubst < /docker-entrypoint-initdb.d/init_readonly.sql.template > /docker-entrypoint-initdb.d/init_readonly.sql

# Exit so that the original postgres entrypoint picks up the generated SQL file.
exit 0
