import math
import time
from threading import Event, RLock
from typing import NamedTuple

original_time_sleep = time.sleep
_original_time_sleep_for_internal_use = time.sleep


def passthrough_to_real_implementation(duration):
    original_time_sleep(duration)


class SleepRegistration(NamedTuple):
    sleep_end_time: int
    sleep_is_over: Event


class SleepMock:
    def __init__(self):
        self._current_time = 0
        self._registrations = []
        self._lock = RLock()
        self._increment = 0.1
        self._unblock_all_called = False

    def __call__(self, duration):
        if duration < 1:
            # Small sleep duration are used in some debuggers (ie: pycharm) to allow for their
            # instrumentation to take place.
            #
            # For the code under tests, it is always possible to configure test-specific sleep
            # duration that would be over 1s, allowing this library to take over.
            # So no option to disable the passthrough is provided as of now.
            passthrough_to_real_implementation(duration)
        else:
            with self._lock:
                if self._unblock_all_called:
                    raise RuntimeError("Can not call 'time.sleep' after calling 'unblock_all'! Only use for teardown")

                registration = SleepRegistration(sleep_end_time=self._current_time + duration,
                                                 sleep_is_over=Event())
                self._registrations.append(registration)

            registration.sleep_is_over.wait()

    def fast_forward(self, duration):
        def allow_other_threads_to_acquire_lock():
            _original_time_sleep_for_internal_use(self._increment / 10_000)

        def move_one_increment():
            with self._lock:
                self._current_time += self._increment
                self._wake_up_threads_whose_sleep_is_over_and_update_registrations()

        end = self._current_time + duration

        while not self._almost_equal(self._current_time, end):
            move_one_increment()
            allow_other_threads_to_acquire_lock()

    def unblock_all(self):
        with self._lock:
            for registration in self._registrations:
                registration.sleep_is_over.set()
            self._unblock_all_called = True

    def _almost_equal(self, float1, float2):
        return math.isclose(float1, float2, abs_tol=self._increment / 100)

    def _wake_up_threads_whose_sleep_is_over_and_update_registrations(self):
        with self._lock:
            for registration in self._registrations:
                def should_wake_up():
                    if self._current_time > registration.sleep_end_time:
                        return True
                    elif self._almost_equal(self._current_time, registration.sleep_end_time):
                        return True
                    else:
                        return False

                def wake_up():
                    registration.sleep_is_over.set()

                if should_wake_up():
                    wake_up()
                    self._registrations.remove(registration)

    def assert_current_time(self, expected):
        """Use for sanity-check / readability in tests"""
        assert self._almost_equal(self._current_time, expected), \
            f"Current time should be '{expected}' but is '{self._current_time}'"
