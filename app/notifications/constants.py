class Statuses:
    SENT = 'sent'
    SEEN = 'seen'


ON_QUIZ_CREATED_TEXT = lambda quiz_id: \
    'Hello! A new quiz has been created in one of your companies. ' \
    f'Would you like to take it now? quiz: {quiz_id}'


ON_ATTEMPT_OUTDATED_TEXT = lambda quiz_id: \
    f"Your attempt for quiz {quiz_id} is outdated. " \
    f"It's time to take the quiz again!"
