"""Reduced compute-manager runtime for source-mode algorithm harness execution."""

from __future__ import annotations

import threading
from collections import defaultdict, deque
from queue import Empty, Queue
from time import monotonic


class IntermediateStage:
    """Owns intermediate executors and per-algorithm result buffers."""

    def __init__(self, max_results_per_stream: int = 1000, error_cb=None):
        self.max_results_per_stream = max_results_per_stream
        self.error_cb = error_cb
        self._intermediate_executors = {}
        self._results = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=self.max_results_per_stream))
        )
        self._lock = threading.Lock()

    def register_intermediate_executor(self, algorithm_name, executor) -> None:
        with self._lock:
            self._intermediate_executors[algorithm_name] = executor

    def reset(self) -> None:
        with self._lock:
            self._intermediate_executors.clear()
            self._results.clear()

    def handle_result(self, result):
        algo_name = result.algorithm_name
        with self._lock:
            self._results[algo_name][result.address].append(result)
            executor = self._intermediate_executors.get(algo_name)
            if not executor:
                return None
            if not executor.should_run(self._results[algo_name]):
                return None
            try:
                return executor.run(self._results[algo_name])
            except Exception as exc:
                if self.error_cb:
                    self.error_cb(f"Intermediate executor failed for {algo_name}: {exc}")
                return None

    def get_results(self, algorithm_name, address=None, limit=None):
        with self._lock:
            if address:
                results = list(self._results[algorithm_name][address])
            else:
                results = [
                    result
                    for address_results in self._results[algorithm_name].values()
                    for result in address_results
                ]
        if limit:
            return results[-limit:]
        return results


class ConsolidationStage:
    """Owns consolidation executors and dispatches them per subject/algorithm."""

    def __init__(self, error_cb=None):
        self.error_cb = error_cb
        self._consolidation_executors = {}
        self._lock = threading.Lock()

    def register_consolidation_executor(self, algorithm_name, executor) -> None:
        with self._lock:
            self._consolidation_executors[algorithm_name] = executor

    def reset(self) -> None:
        with self._lock:
            self._consolidation_executors.clear()

    def run_for_subject(self, subject_id: str, algorithm_name: str, intermediate_records: list[dict]):
        with self._lock:
            executor = self._consolidation_executors.get(algorithm_name)
        if not executor:
            return None
        try:
            return executor.consolidate(
                subject_id=subject_id,
                intermediate_records=intermediate_records,
            )
        except Exception as exc:
            if self.error_cb:
                self.error_cb(f"Consolidation executor failed for {algorithm_name}: {exc}")
            return None


class ResultRouter:
    """Route per-sensor algorithm results to listeners and intermediate stage."""

    def __init__(self, intermediate_stage: IntermediateStage):
        self._intermediate_stage = intermediate_stage
        self._lock = threading.Lock()
        self._algorithm_result_listener = None
        self._intermediate_result_listener = None

    def register_result_listener(self, callback) -> None:
        with self._lock:
            self._algorithm_result_listener = callback

    def register_intermediate_result_listener(self, callback) -> None:
        with self._lock:
            self._intermediate_result_listener = callback

    def handle_result(self, result) -> None:
        with self._lock:
            result_listener = self._algorithm_result_listener
            intermediate_listener = self._intermediate_result_listener

        if result_listener:
            result_listener(result)

        intermediate_result = self._intermediate_stage.handle_result(result)
        if intermediate_result and intermediate_listener:
            intermediate_listener(intermediate_result)


class HarnessComputeManager:
    """Execute per-sensor algorithms and optional aggregate executors."""

    def __init__(self, error_cb=None):
        self.error_cb = error_cb
        self._algorithms = {}
        self._queue: Queue = Queue()
        self._shutdown_token = object()
        self._pending_lock = threading.Lock()
        self._pending_count = 0
        self._idle_event = threading.Event()
        self._idle_event.set()
        self._intermediate_stage = IntermediateStage(error_cb=error_cb)
        self._consolidation_stage = ConsolidationStage(error_cb=error_cb)
        self._result_router = ResultRouter(self._intermediate_stage)
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def register_algorithm(self, address, algorithm) -> None:
        self._algorithms[address] = algorithm

    def has_algorithm(self, address) -> bool:
        return address in self._algorithms

    def register_intermediate_executor(self, algorithm_name, executor) -> None:
        self._intermediate_stage.register_intermediate_executor(algorithm_name, executor)

    def register_consolidation_executor(self, algorithm_name, executor) -> None:
        self._consolidation_stage.register_consolidation_executor(algorithm_name, executor)

    def register_result_listener(self, callback) -> None:
        self._result_router.register_result_listener(callback)

    def register_intermediate_result_listener(self, callback) -> None:
        self._result_router.register_intermediate_result_listener(callback)

    def ingest_sample(self, sample) -> None:
        with self._pending_lock:
            self._pending_count += 1
            self._idle_event.clear()
        self._queue.put(sample)

    def wait_until_idle(self, timeout: float = 5.0) -> bool:
        deadline = monotonic() + timeout
        while True:
            remaining = deadline - monotonic()
            if remaining <= 0:
                return self._idle_event.is_set()
            if self._idle_event.wait(timeout=remaining):
                return True

    def get_results(self, algorithm_name, address=None, limit=None):
        return self._intermediate_stage.get_results(
            algorithm_name=algorithm_name,
            address=address,
            limit=limit,
        )

    def run_consolidation_for_subject(self, subject_id: str, algorithm_name: str, intermediate_records: list[dict]):
        return self._consolidation_stage.run_for_subject(
            subject_id=subject_id,
            algorithm_name=algorithm_name,
            intermediate_records=intermediate_records,
        )

    def on_algorithm_result(self, result) -> None:
        self._result_router.handle_result(result)

    def reset(self) -> None:
        self._algorithms.clear()
        self._intermediate_stage.reset()
        self._consolidation_stage.reset()
        try:
            while True:
                self._queue.get_nowait()
        except Empty:
            pass
        with self._pending_lock:
            self._pending_count = 0
            self._idle_event.set()

    def shutdown(self) -> None:
        self._queue.put(self._shutdown_token)
        self._worker.join(timeout=2.0)

    def _run(self) -> None:
        while True:
            sample = self._queue.get()
            try:
                if sample is self._shutdown_token:
                    break
                algorithm = self._algorithms.get(sample.address)
                if algorithm:
                    try:
                        algorithm.on_sample(sample)
                    except Exception as exc:
                        if self.error_cb:
                            self.error_cb(f"Error processing sample from {sample.address}: {exc}")
            finally:
                if sample is not self._shutdown_token:
                    with self._pending_lock:
                        self._pending_count = max(0, self._pending_count - 1)
                        if self._pending_count == 0:
                            self._idle_event.set()
