# Simple Account Creation Logic

This folder contains a beginner-friendly Python backend for creating CSUF student accounts. (sprint1)

## What this does

- checks that first name and last name are not empty
- requires a valid CSUF email ending in @csu.fullerton.edu (crucial)
- checks that the password is at least 10 characters long
- hashes the password before saving it (REALLY IMPORTANT)
- prevents duplicate emails

## How to run the tests

```bash
cd account_creation
python -m unittest discover -s tests -v
```

