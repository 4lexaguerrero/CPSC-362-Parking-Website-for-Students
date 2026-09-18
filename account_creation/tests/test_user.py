from account_creation.account_creation.userdata import User
# some tests for the User class!.

def test_user_stores_basic_info():
    user = User(
        first_name="Alexa",
        last_name="Guerrero",
        email="alexa@csu.fullerton.edu",
        password_hash="abc123",
    )

    assert user.first_name == "Alexa"
    assert user.last_name == "Guerrero"
    assert user.email == "alexa@csu.fullerton.edu"
    assert user.password_hash == "abc123"
    assert user.to_dict()["email"] == "alexa@csu.fullerton.edu"
