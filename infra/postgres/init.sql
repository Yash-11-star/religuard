-- One database per service. Runs once, when the Postgres volume is first created.
-- Each service creates its own tables on startup.
CREATE DATABASE orders;
CREATE DATABASE payments;
CREATE DATABASE inventory;
