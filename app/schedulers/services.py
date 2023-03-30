from datetime import datetime
from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.logging import file_logger
from app.notifications.services import notification_service
from app.quizzes.services import quiz_service


class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.add_core_jobs()

    def add_core_jobs(self):
        self.scheduler.add_job(**self.check_outdated_attempts_job())
        # self.scheduler.add_job(**self.log_test_job())

    async def start(self):
        self.scheduler.start()

    async def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    async def check_outdated_attempts(self):
        outdated_attempts = await quiz_service.get_all_outdated_attempts()
        await notification_service.on_attempts_outdate_send_notification_to_all_users(
            outdated_attempts
        )

    def check_outdated_attempts_job(self):
        return {
            'func': self.check_outdated_attempts,
            'trigger': 'interval',
            'days': 1,
            'start_date': datetime.now().replace(hour=0, minute=0, second=0),
        }

    def log_test_job(self):
        return {
            'func': lambda: file_logger.info(datetime.now()),
            'trigger': 'interval',
            'seconds': 1,
            'start_date': datetime.now()
        }


scheduler_service = SchedulerService()
