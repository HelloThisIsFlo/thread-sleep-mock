import time
from threading import Thread, Event
from unittest.mock import MagicMock

import pytest
from pytest import mark

from src.thread_sleep_mock.callback import ThreadSafeCallbackMock


class CallCallbackWhenFunctionBecomesTrue(Thread):
    def __init__(self, function_to_test, callback, delay_between_each_try) -> None:
        super().__init__(daemon=True)
        self._function_to_test = function_to_test
        self._callback = callback
        self._delay_between_each_try = delay_between_each_try
        self._should_stop = Event()

    def run(self):
        def call_callback_as_soon_as_function_becomes_true():
            func_result = self._function_to_test()
            while func_result is False:
                if self._should_stop.is_set():
                    return

                time.sleep(self._delay_between_each_try)
                func_result = self._function_to_test()

            self._callback()

        call_callback_as_soon_as_function_becomes_true()

    def stop(self):
        self._should_stop.set()


def test_with_delay__showcase_race_condition():
    function = MagicMock(return_value=False)
    callback = ThreadSafeCallbackMock()

    job = CallCallbackWhenFunctionBecomesTrue(function, callback, delay_between_each_try=1)
    job.start()

    callback.assert_not_called_yet()
    function.return_value = True
    with pytest.raises(AssertionError, match="not yet called"):
        callback.assert_already_called()
        # Callback hasn't been called yet because of the slight delay between each check.
        # The Thread is "slow" to figure out something has changed while the test is
        # immediately trying to detect the change
        # ==> Race condition: assertion fails when it "shouldn't"


def test_without_delay__avoid_race_condition():
    function = MagicMock(return_value=False)
    callback = ThreadSafeCallbackMock()

    job = CallCallbackWhenFunctionBecomesTrue(function, callback, delay_between_each_try=0)
    job.start()

    callback.assert_not_called_yet()
    function.return_value = True
    callback.assert_called_within(1)


@mark.integration
def test_with_delay__avoid_race_condition():
    function = MagicMock(return_value=False)
    callback = ThreadSafeCallbackMock()

    job = CallCallbackWhenFunctionBecomesTrue(function, callback, delay_between_each_try=1)
    job.start()

    callback.assert_not_called_yet()
    function.return_value = True
    callback.assert_called_within(5)


@mark.integration
def test_function_never_true__timeout():
    function = MagicMock(return_value=False)
    callback = ThreadSafeCallbackMock()

    job = CallCallbackWhenFunctionBecomesTrue(function, callback, delay_between_each_try=0)
    job.start()

    with pytest.raises(AssertionError, match="never called"):
        callback.assert_called_within(1)

    job.stop()
