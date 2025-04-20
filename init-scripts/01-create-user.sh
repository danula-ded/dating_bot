#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --appusername "postgres" <<-EOSQL
    CREATE USER "appuser" WITH PASSWORD 'password';
    ALTER USER "appuser" WITH SUPERUSER;
    CREATE DATABASE dating_bot;
    GRANT ALL PRIVILEGES ON DATABASE dating_bot TO "appuser";
EOSQL 