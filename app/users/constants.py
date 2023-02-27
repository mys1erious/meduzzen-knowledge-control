class ExceptionDetails:
    PASSWORDS_DONT_MATCH = 'Passwords do not match.'
    WEAK_PASSWORD = 'Password must be longer than 4 characters.'
    EMAIL_TAKEN = "Email is already taken."
    USER_NOT_FOUND = 'User not found.'
    USER_WITH_ID_NOT_FOUND = lambda user_id: f"User with id {user_id} not found."
