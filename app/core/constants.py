class ExceptionDetails:
    NOT_FOUND = 'Not Found'
    SOMETHING_WENT_WRONG = 'Something went wrong'
    NOT_ALLOWED = 'You are not allowed to perform this action'
    ENTITY_WITH_ID_NOT_FOUND = lambda entity, id: f"{entity} with id {id} not found"


class SuccessDetails:
    SUCCESS = 'success'
    SCHEDULER_IS_RUNNING = 'Scheduler is running'
