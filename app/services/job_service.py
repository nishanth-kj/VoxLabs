"""JobService: background execution for long-running work.

Work runs on a small thread pool so neither the Qt event loop nor API requests
block. Each job gets a `JobContext` for progress reporting and cooperative
cancellation. Listeners (the UI's JobBridge) are notified on every change.
"""

import threading
import time
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor

from sqlalchemy import select

from app.constants.jobs import JOB_ACTIVE_STATUSES, JOB_FINISHED_STATUSES, JOB_WORKERS
from app.constants.status import Status
from app.exceptions import AppError, JobError, NotFoundError
from app.models import Job
from app.utils.database import read_session, serialize, transaction
from app.utils.logger import logger
from app.utils.time import utcnow


class JobCancelled(Exception):
    pass


class JobContext:
    def __init__(self, jobs_id: int, service: "JobService"):
        self.jobs_id = jobs_id
        self._service = service
        self._cancel = threading.Event()
        self._last_write = 0.0
        self._last_value = -1.0

    @property
    def cancelled(self) -> bool:
        return self._cancel.is_set()

    def check_cancelled(self) -> None:
        if self._cancel.is_set():
            raise JobCancelled()

    def progress(self, value: float, message: str | None = None) -> None:
        """Report progress 0..1 (writes are throttled). Raises JobCancelled if cancelled."""
        self.check_cancelled()
        value = max(0.0, min(1.0, float(value)))
        now = time.monotonic()
        if value >= 1.0 or value - self._last_value >= 0.01 or now - self._last_write > 0.5:
            self._last_write, self._last_value = now, value
            self._service._update(self.jobs_id, progress=value, message=message)

    def sub(self, start: float, end: float) -> Callable[[float], None]:
        """Progress callback mapping 0..1 onto [start, end] of this job."""
        return lambda value: self.progress(start + (end - start) * value)


JobFn = Callable[[JobContext], dict | None]


class JobService:
    def __init__(self):
        self._executor: ThreadPoolExecutor | None = None
        self._contexts: dict[int, JobContext] = {}
        self._futures: dict[int, Future] = {}
        self._listeners: list[Callable[[dict], None]] = []
        self._lock = threading.Lock()

    # ------------------------------------------------------------ listeners

    def add_listener(self, callback: Callable[[dict], None]) -> None:
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[dict], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify(self, job: dict) -> None:
        for callback in list(self._listeners):
            try:
                callback(job)
            except Exception:
                logger.exception("Job listener failed")

    # ------------------------------------------------------------ persistence

    def to_dict(self, job: Job) -> dict:
        data = serialize(job)
        data["finished"] = job.status in JOB_FINISHED_STATUSES
        return data

    def _update(self, jobs_id: int, message: str | None = None, **fields) -> dict:
        with transaction() as session:
            job = session.get(Job, jobs_id)
            for key, value in fields.items():
                setattr(job, key, value)
            if message:
                job.result = {**(job.result or {}), "message": message}
            data = self.to_dict(job)
        self._notify(data)
        return data

    # ------------------------------------------------------------ public API

    def submit(self, job_type: str, fn: JobFn, *, title: str = "", params: dict | None = None,
               users_id: int | None = None) -> dict:
        with transaction() as session:
            job = Job(job_type=job_type, title=title or job_type, params=params or {}, status=Status.PENDING.code,
                      users_id=users_id)
            session.add(job)
            session.flush()
            data = self.to_dict(job)
        jobs_id = data["jobs_id"]
        context = JobContext(jobs_id, self)
        with self._lock:
            if self._executor is None:
                self._executor = ThreadPoolExecutor(max_workers=JOB_WORKERS, thread_name_prefix="voxlabs-job")
            self._contexts[jobs_id] = context
            self._futures[jobs_id] = self._executor.submit(self._run, context, fn)
        logger.info(f"Job {jobs_id} queued ({job_type})")
        self._notify(data)
        return data

    def _run(self, context: JobContext, fn: JobFn) -> None:
        jobs_id = context.jobs_id
        try:
            if context.cancelled:
                raise JobCancelled()
            self._update(jobs_id, status=Status.IN_PROGRESS.code, started_at=utcnow())
            logger.info(f"Job {jobs_id} started")
            result = fn(context) or {}
            self._update(jobs_id, status=Status.COMPLETED.code, progress=1.0, result=result, finished_at=utcnow())
            logger.info(f"Job {jobs_id} completed")
        except JobCancelled:
            self._update(jobs_id, status=Status.CANCELLED.code, finished_at=utcnow())
            logger.info(f"Job {jobs_id} cancelled")
        except AppError as exc:
            self._update(jobs_id, status=Status.FAILED.code, error=exc.message, finished_at=utcnow())
            logger.warning(f"Job {jobs_id} failed: {exc.message}")
        except Exception as exc:
            logger.exception(f"Job {jobs_id} crashed")
            self._update(jobs_id, status=Status.FAILED.code, error=f"Unexpected error: {exc}", finished_at=utcnow())
        finally:
            with self._lock:
                self._contexts.pop(jobs_id, None)
                self._futures.pop(jobs_id, None)

    def get(self, jobs_id: int) -> dict:
        with read_session() as session:
            job = session.get(Job, jobs_id)
            if job is None:
                raise NotFoundError(f"Job {jobs_id} not found", field="jobs_id")
            return self.to_dict(job)

    def list_jobs(self, active_only: bool = False, limit: int = 50) -> list[dict]:
        with read_session() as session:
            query = select(Job)
            if active_only:
                query = query.where(Job.status.in_(list(JOB_ACTIVE_STATUSES)))
            return [self.to_dict(j) for j in session.scalars(query.order_by(Job.created_at.desc()).limit(limit))]

    def cancel(self, jobs_id: int) -> dict:
        job = self.get(jobs_id)
        if job["finished"]:
            raise JobError(f"Job {jobs_id} already finished", field="jobs_id")
        with self._lock:
            context = self._contexts.get(jobs_id)
            future = self._futures.get(jobs_id)
        if context:
            context._cancel.set()
        if future is not None and future.cancel():
            # Never started: finalize here because _run will not execute.
            return self._update(jobs_id, status=Status.CANCELLED.code, finished_at=utcnow())
        if context is None:
            # Orphaned (e.g. from a previous run); mark it cancelled directly.
            return self._update(jobs_id, status=Status.CANCELLED.code, finished_at=utcnow())
        return self.get(jobs_id)

    def wait(self, jobs_id: int, timeout: float = 60.0) -> dict:
        with self._lock:
            future = self._futures.get(jobs_id)
        if future is not None:
            try:
                future.result(timeout=timeout)
            except Exception:
                pass
        return self.get(jobs_id)

    def recover_interrupted(self) -> int:
        """Mark jobs left Queued/Running by a previous session as failed."""
        with transaction() as session:
            rows = session.scalars(
                select(Job).where(Job.status.in_(list(JOB_ACTIVE_STATUSES)))
            ).all()
            for job in rows:
                if job.jobs_id not in self._contexts:
                    job.status = Status.FAILED.code
                    job.error = "Interrupted: VoxLabs was closed while this job was running"
                    job.finished_at = utcnow()
            return len(rows)

    def shutdown(self, wait: bool = False) -> None:
        with self._lock:
            for context in self._contexts.values():
                context._cancel.set()
            executor, self._executor = self._executor, None
        if executor:
            executor.shutdown(wait=wait, cancel_futures=True)


job_service = JobService()
