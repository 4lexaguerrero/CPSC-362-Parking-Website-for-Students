class InMemoryUserRepository:
    def __init__(self):
        self._users = {}

    def add_user(self, account):
        email = account["email"]
        self._users[email] = account
        return account

    def get_user_by_email(self, email):
        return self._users.get(email)
