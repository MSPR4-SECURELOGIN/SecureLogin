CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    mfa_secret TEXT NOT NULL,
    gendate TIMESTAMP NOT NULL
);
