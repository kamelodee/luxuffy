-- Create the database
CREATE DATABASE luxuffy;

-- Connect to the database
\c luxuffy

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "hstore";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create the user if not exists
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'luxuffy_user') THEN
      CREATE ROLE luxuffy_user LOGIN PASSWORD 'your_password_here';
   END IF;
END
$do$;

-- Set user privileges
ALTER ROLE luxuffy_user WITH SUPERUSER;
ALTER ROLE luxuffy_user WITH CREATEDB;
ALTER ROLE luxuffy_user WITH CREATEROLE;
ALTER ROLE luxuffy_user SET client_encoding TO 'utf8';
ALTER ROLE luxuffy_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE luxuffy_user SET timezone TO 'UTC';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE luxuffy TO luxuffy_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO luxuffy_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO luxuffy_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO luxuffy_user;
