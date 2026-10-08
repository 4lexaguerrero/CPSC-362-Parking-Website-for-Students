# Simple Account Creation Logic

This folder contains a beginner-friendly Python backend for creating CSUF student accounts. (sprint1)

## What this does

- checks that first name and last name are not empty
- requires a valid CSUF email ending in @csu.fullerton.edu (crucial)
- checks that the password is at least 10 characters long
- hashes the password before saving it (REALLY IMPORTANT)
- prevents duplicate emails

## Persistent storage

Use `SQLiteUserRepository` to store accounts in `parking_accounts.db` by default.
Each account receives a database-generated `user_id`, and email addresses must be unique.
Pass a different path to `SQLiteUserRepository` to choose another database file.

## How to run the tests

```bash
cd account_creation
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

