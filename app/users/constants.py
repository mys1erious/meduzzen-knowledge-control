class ExceptionDetails:
    PASSWORDS_DONT_MATCH = 'Passwords do not match.'
    WEAK_PASSWORD = 'Password must be longer than 4 characters.'
    INVALID_TOKEN = "Invalid token."
    EMAIL_TAKEN = "Email is already taken."
    USER_NOT_FOUND = 'This user not found'
    USER_WITH_ID_NOT_FOUND = lambda user_id: f"User with id {user_id} not found."
    USER_WITH_EMAIL_NOT_FOUND = lambda email: f"User with email {email} not found."
    WRONG_USER = 'It\'s not your account'
    INVALID_CREDENTIALS = "Incorrect username or password"
    USER_ALREADY_A_MEMBER = "User is already a member of the company"
