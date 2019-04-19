import time
from threading import Lock, Event
from typing import NamedTuple

time_sleep_before_patch = time.sleep


def passthrough_to_real_implementation(duration):
    time_sleep_before_patch(duration)


class SleepRegistration(NamedTuple):
    sleep_end_time: int
    sleep_is_over: Event


class SleepMock:
    def __init__(self):
        self._current_time = 0
        self._registrations = []
        self._lock = Lock()

    def __call__(self, duration):
        if duration < 1:
            # Small sleep duration are used in some debuggers (ie: pycharm) to allow for their
            # instrumentation to take place.
            #
            # For the code under tests, it is always possible to configure test-specific sleep
            # duration that would be over 1s, allowing this library to take over.
            # So no option to disable the passthrough is provided as of now.
            passthrough_to_real_implementation(duration)
            return

        with self._lock:
            registration = SleepRegistration(sleep_end_time=self._current_time + duration,
                                             sleep_is_over=Event())
            self._registrations.append(registration)

        registration.sleep_is_over.wait()

    def fast_forward(self, duration):
        with self._lock:
            self._current_time += duration

            for registration in self._registrations:
                def should_wake_up():
                    return registration.sleep_end_time <= self._current_time

                def wake_up():
                    registration.sleep_is_over.set()

                if should_wake_up():
                    wake_up()
                    self._registrations.remove(registration)

    def assert_current_time(self, expected):
        """Use for sanity-check / readability in tests"""
        assert expected == self._current_time
