from queue import Queue

# Queues used to safely pass events from any thread to the Socket.IO greenlet emitters
backend_log_queue: Queue = Queue()
progress_queue: Queue = Queue()

def enqueue_backend_log(payload: dict) -> None:
    try:
        backend_log_queue.put_nowait(payload)
    except Exception:
        pass

def enqueue_progress(payload: dict) -> None:
    try:
        progress_queue.put_nowait(payload)
    except Exception:
        pass


