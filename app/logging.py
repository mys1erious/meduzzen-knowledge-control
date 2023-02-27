import logging

logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
console_logger = logging.getLogger(__name__)
file_logger = logging.getLogger('file')
