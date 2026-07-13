-- ============================================================
--  Smart Travel Intelligence Platform — PostgreSQL Setup
--  Run once as postgres superuser:
--  psql -U postgres -f db_setup.sql
-- ============================================================

-- Create user
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'travel_user') THEN
        CREATE USER travel_user WITH PASSWORD 'travel_pass';
        RAISE NOTICE 'Created user travel_user';
    ELSE
        RAISE NOTICE 'User travel_user already exists';
    END IF;
END
$$;

-- Create database
SELECT 'CREATE DATABASE smart_travel OWNER travel_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'smart_travel')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE smart_travel TO travel_user;

\echo '✅ Database smart_travel is ready for user travel_user'
