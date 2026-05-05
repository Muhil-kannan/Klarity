"""
ARQ worker entry point.
Run with: python -m app.jobs.worker
"""

from arq import run_worker
from arq.connections import RedisSettings

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.base import init_db
from app.jobs.tasks import process_pull_request_event


async def startup(ctx):
    setup_logging()
    await init_db()


async def shutdown(ctx):
    pass


class WorkerSettings:
    functions = [process_pull_request_event]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 10
    job_timeout = 120       # seconds
    keep_result = 3600      # keep job results for 1 hour


if __name__ == "__main__":
    run_worker(WorkerSettings)
