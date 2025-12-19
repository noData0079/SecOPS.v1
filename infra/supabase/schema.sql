-- infra/supabase/schema.sql
--
-- T79AI – Supabase PostgreSQL schema
--
-- This is the minimal schema required for the MVP:
--   - issues: core issues table used by the console
--
-- You can run this once in the Supabase SQL Editor, or just rely on
-- Alembic migrations pointed at your Supabase DATABASE_URL.
--

-- Ensure we are in the default public schema
set search_path to public;

-- ---------------------------------------------------------------------
-- issues table
-- ---------------------------------------------------------------------
-- This matches the initial Alembic migration we created for the backend.
-- IMPORTANT: If you run Alembic against Supabase, DO NOT run this file
-- separately, or you will get "relation already exists" errors. Use one:
--   - EITHER: Alembic migrations
--   - OR: this SQL schema
-- ---------------------------------------------------------------------

create table if not exists issues (
    id           text primary key,                -- UUID string (36 chars)
    title        varchar(255) not null,
    description  text,
    severity     varchar(32) not null default 'medium',
    status       varchar(32) not null default 'open',
    source       varchar(64),

    detected_at  timestamptz not null default now(),
    resolved_at  timestamptz,

    metadata     jsonb not null default '{}'::jsonb,

    created_at   timestamptz not null default now(),
    updated_at   timestamptz not null default now()
);

-- Indexes to speed up filtering in the console
create index if not exists ix__issues__severity
    on issues (severity);

create index if not exists ix__issues__status
    on issues (status);

create index if not exists ix__issues__source
    on issues (source);

create index if not exists ix__issues__detected_at
    on issues (detected_at);

-- Optionally track who created an issue (mapped to Supabase auth.users.id)
alter table issues
    add column if not exists created_by uuid;

-- If you want to enforce foreign key to Supabase auth.users:
-- alter table issues
--   add constraint fk__issues__created_by__auth_users
--   foreign key (created_by) references auth.users (id) on delete set null;
