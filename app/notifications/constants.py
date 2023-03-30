class Statuses:
    SENT = 'sent'
    SEEN = 'seen'


ON_QUIZ_CREATED_TEXT = lambda quiz_id: \
    'Hello! A new quiz has been created in one of your companies. ' \
    f'Would you like to take it now? quiz: {quiz_id}'
