#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "postgres" <<-EOSQL
    CREATE USER "user" WITH PASSWORD 'password';
    ALTER USER "user" WITH SUPERUSER;
    CREATE DATABASE dating_bot;
    GRANT ALL PRIVILEGES ON DATABASE dating_bot TO "user";
EOSQL 