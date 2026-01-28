"""
Job Queue System for Scalable Processing
Handles background tasks and concurrent conversions
"""

import os
import uuid
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from queue import PriorityQueue
import json

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status states"""
    PENDING = 'pending'
    QUEUED = 'queued'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class JobPriority(Enum):
    """Job priority levels"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    URGENT = 0


@dataclass(order=True)
class Job:
    """Represents a conversion job"""
    priority: int
    job_id: str = field(compare=False)
    created_at: datetime = field(compare=False)
    status: JobStatus = field(compare=False, default=JobStatus.PENDING)
    progress: int = field(compare=False, default=0)
    current_step: str = field(compare=False, default='')
    input_file: str = field(compare=False, default='')
    output_file: str = field(compare=False, default='')
    options: Dict = field(compare=False, default_factory=dict)
    error: Optional[str] = field(compare=False, default=None)
    result: Optional[Dict] = field(compare=False, default=None)
    started_at: Optional[datetime] = field(compare=False, default=None)
    completed_at: Optional[datetime] = field(compare=False, default=None)
    
    def to_dict(self) -> Dict:
        """Convert job to dictionary"""
        return {
            'job_id': self.job_id,
            'status': self.status.value,
            'progress': self.progress,
            'current_step': self.current_step,
            'input_file': os.path.basename(self.input_file) if self.input_file else None,
            'output_file': os.path.basename(self.output_file) if self.output_file else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error': self.error,
            'duration_seconds': self._get_duration(),
            'options': {k: v for k, v in self.options.items() if k not in ['password']},
        }
    
    def _get_duration(self) -> Optional[float]:
        """Get job duration in seconds"""
        if self.started_at:
            end_time = self.completed_at or datetime.now()
            return (end_time - self.started_at).total_seconds()
        return None


class JobQueue:
    """Thread-safe job queue with priority support"""
    
    def __init__(self, max_workers: int = 2, max_queue_size: int = 100):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.queue = PriorityQueue(maxsize=max_queue_size)
        self.jobs: Dict[str, Job] = {}
        self.workers: List[threading.Thread] = []
        self.running = False
        self.lock = threading.Lock()
        self.job_handlers: Dict[str, Callable] = {}
        
        # Statistics
        self.stats = {
            'total_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0,
            'total_processing_time': 0,
        }
    
    def register_handler(self, job_type: str, handler: Callable):
        """Register a handler function for a job type"""
        self.job_handlers[job_type] = handler
    
    def start(self):
        """Start the worker threads"""
        if self.running:
            return
        
        self.running = True
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker, name=f"JobWorker-{i}")
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"Job queue started with {self.max_workers} workers")
    
    def stop(self):
        """Stop all worker threads"""
        self.running = False
        for worker in self.workers:
            worker.join(timeout=5)
        self.workers.clear()
        logger.info("Job queue stopped")
    
    def submit(
        self,
        job_type: str,
        input_file: str,
        output_file: str,
        options: Optional[Dict] = None,
        priority: JobPriority = JobPriority.NORMAL
    ) -> str:
        """Submit a new job to the queue"""
        job_id = str(uuid.uuid4())
        
        job = Job(
            priority=priority.value,
            job_id=job_id,
            created_at=datetime.now(),
            status=JobStatus.QUEUED,
            input_file=input_file,
            output_file=output_file,
            options={**(options or {}), 'job_type': job_type},
        )
        
        with self.lock:
            if self.queue.full():
                raise RuntimeError("Job queue is full")
            
            self.jobs[job_id] = job
            self.queue.put(job)
            self.stats['total_jobs'] += 1
        
        logger.info(f"Job {job_id} submitted with priority {priority.name}")
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get job status as dictionary"""
        job = self.jobs.get(job_id)
        return job.to_dict() if job else None
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job"""
        with self.lock:
            job = self.jobs.get(job_id)
            if job and job.status in [JobStatus.PENDING, JobStatus.QUEUED]:
                job.status = JobStatus.CANCELLED
                return True
        return False
    
    def get_queue_stats(self) -> Dict:
        """Get queue statistics"""
        with self.lock:
            pending = sum(1 for j in self.jobs.values() if j.status == JobStatus.QUEUED)
            processing = sum(1 for j in self.jobs.values() if j.status == JobStatus.PROCESSING)
            
            return {
                'pending_jobs': pending,
                'processing_jobs': processing,
                'total_jobs': self.stats['total_jobs'],
                'completed_jobs': self.stats['completed_jobs'],
                'failed_jobs': self.stats['failed_jobs'],
                'average_processing_time': (
                    self.stats['total_processing_time'] / self.stats['completed_jobs']
                    if self.stats['completed_jobs'] > 0 else 0
                ),
                'workers': self.max_workers,
                'queue_size': self.queue.qsize(),
                'max_queue_size': self.max_queue_size,
            }
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Remove jobs older than specified age"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        with self.lock:
            old_jobs = [
                job_id for job_id, job in self.jobs.items()
                if job.created_at < cutoff and job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
            ]
            
            for job_id in old_jobs:
                del self.jobs[job_id]
            
            logger.info(f"Cleaned up {len(old_jobs)} old jobs")
            return len(old_jobs)
    
    def _worker(self):
        """Worker thread main loop"""
        while self.running:
            try:
                # Get job with timeout
                try:
                    job = self.queue.get(timeout=1)
                except:
                    continue
                
                if job.status == JobStatus.CANCELLED:
                    continue
                
                # Process job
                self._process_job(job)
                
            except Exception as e:
                logger.error(f"Worker error: {e}")
    
    def _process_job(self, job: Job):
        """Process a single job"""
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now()
        job.current_step = "Starting..."
        
        try:
            job_type = job.options.get('job_type', 'default')
            handler = self.job_handlers.get(job_type)
            
            if not handler:
                raise ValueError(f"No handler registered for job type: {job_type}")
            
            # Execute handler with progress callback
            def progress_callback(progress: int, step: str):
                job.progress = progress
                job.current_step = step
            
            result = handler(job, progress_callback)
            
            # Mark complete
            job.status = JobStatus.COMPLETED
            job.progress = 100
            job.current_step = "Completed"
            job.result = result
            job.completed_at = datetime.now()
            
            with self.lock:
                self.stats['completed_jobs'] += 1
                self.stats['total_processing_time'] += job._get_duration() or 0
            
            logger.info(f"Job {job.job_id} completed successfully")
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now()
            
            with self.lock:
                self.stats['failed_jobs'] += 1
            
            logger.error(f"Job {job.job_id} failed: {e}")


class RateLimiter:
    """Rate limiter for API endpoints"""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[datetime]] = {}
        self.lock = threading.Lock()
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed"""
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        with self.lock:
            if client_id not in self.requests:
                self.requests[client_id] = []
            
            # Remove old requests
            self.requests[client_id] = [
                t for t in self.requests[client_id] if t > window_start
            ]
            
            # Check limit
            if len(self.requests[client_id]) >= self.max_requests:
                return False
            
            # Add current request
            self.requests[client_id].append(now)
            return True
    
    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests in current window"""
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        with self.lock:
            if client_id not in self.requests:
                return self.max_requests
            
            recent = [t for t in self.requests[client_id] if t > window_start]
            return max(0, self.max_requests - len(recent))
    
    def get_reset_time(self, client_id: str) -> Optional[int]:
        """Get seconds until rate limit resets"""
        with self.lock:
            if client_id not in self.requests or not self.requests[client_id]:
                return None
            
            oldest = min(self.requests[client_id])
            reset_time = oldest + timedelta(seconds=self.window_seconds)
            remaining = (reset_time - datetime.now()).total_seconds()
            return max(0, int(remaining))


class CacheManager:
    """Simple in-memory cache for processed results"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Tuple[Any, datetime]] = {}
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        with self.lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                if datetime.now() - timestamp < timedelta(seconds=self.ttl_seconds):
                    return value
                else:
                    del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Set cached value"""
        with self.lock:
            # Evict oldest if at capacity
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
                del self.cache[oldest_key]
            
            self.cache[key] = (value, datetime.now())
    
    def delete(self, key: str):
        """Delete cached value"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
    
    def clear(self):
        """Clear all cached values"""
        with self.lock:
            self.cache.clear()
    
    def cleanup(self):
        """Remove expired entries"""
        now = datetime.now()
        with self.lock:
            expired = [
                k for k, (_, t) in self.cache.items()
                if now - t > timedelta(seconds=self.ttl_seconds)
            ]
            for k in expired:
                del self.cache[k]
        return len(expired)


# Global instances
job_queue = JobQueue(max_workers=2)
rate_limiter = RateLimiter(max_requests=20, window_seconds=60)
cache_manager = CacheManager(max_size=100, ttl_seconds=3600)
