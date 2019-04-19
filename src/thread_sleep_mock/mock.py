import time
from threading import Condition, Lock
from typing import NamedTuple

time_sleep_before_patch = time.sleep


class SleepRegistration(NamedTuple):
    sleep_end_time: int
    sleep_is_over: Condition


class MockSleep:
    def __init__(self):
        self._current_time = 0
        self._registrations = []
        self._lock = Lock()

    def __call__(self, duration):
        if duration < 1:
            time_sleep_before_patch(duration)
            return

        with self._lock:
            registration = SleepRegistration(sleep_end_time=self._current_time + duration,
                                             sleep_is_over=Condition())
            self._registrations.append(registration)

        with registration.sleep_is_over:
            registration.sleep_is_over.wait()

    def fast_forward(self, duration):
        with self._lock:
            self._current_time += duration

            for registration in self._registrations:
                if registration.sleep_end_time <= self._current_time:
                    with registration.sleep_is_over:
                        registration.sleep_is_over.notify()
                    self._registrations.remove(registration)

    def assert_current_time(self, expected):
        """Use for sanity-check / readability in tests"""
        assert expected == self._current_time
