import time
from threading import Thread, Event
from unittest.mock import MagicMock

import pytest
from pytest import mark

from src.thread_sleep_mock.callback import BlockingCallbackMock


class CallCallbackWhenFunctionBecomesTrue(Thread):
    def __init__(self, function_to_test, callback, delay_between_each_try, with_fake_args=False) -> None:
        super().__init__(daemon=True)
        self._function_to_test = function_to_test
        self._callback = callback
        self._delay_between_each_try = delay_between_each_try
        self._should_stop = Event()
        self._with_fake_args = with_fake_args

    def run(self):
        def call_callback_as_soon_as_function_becomes_true():
            func_result = self._function_to_test()
            while func_result is False:
                if self._should_stop.is_set():
                    return

                time.sleep(self._delay_between_each_try)
                func_result = self._function_to_test()

            if self._with_fake_args:
                self._callback("some arg", some="other arg")
            else:
                self._callback()

        call_callback_as_soon_as_function_becomes_true()

    def stop(self):
        self._should_stop.set()


class TestAssertCalled:
    def test_showcase_race_condition(self):
        function = MagicMock(return_value=False)
        callback = BlockingCallbackMock()

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

    def test_avoid_race_condition__without_delay(self):
        function = MagicMock(return_value=False)
        callback = BlockingCallbackMock()

        job = CallCallbackWhenFunctionBecomesTrue(function, callback, delay_between_each_try=0)
        job.start()

        callback.assert_not_called_yet()
        function.return_value = True
        callback.assert_called_within(1)

    @mark.integration
    def test_avoid_race_condition__with_delay(self):
        function = MagicMock(return_value=False)
        callback = BlockingCallbackMock()

        job = CallCallbackWhenFunctionBecomesTrue(function, callback, delay_between_each_try=1)
        job.start()

        callback.assert_not_called_yet()
        function.return_value = True
        callback.assert_called_within(5)

    @mark.integration
    def test_function_never_true__timeout(self):
        timeout = 1
        function = MagicMock(return_value=False)
        callback = BlockingCallbackMock()

        job = CallCallbackWhenFunctionBecomesTrue(function, callback, delay_between_each_try=0)
        job.start()

        start_time = time.time()
        with pytest.raises(AssertionError, match="never called"):
            callback.assert_called_within(timeout)
        end_time = time.time()

        duration = end_time - start_time
        assert duration >= timeout

        job.stop()


class TestAssertNotCalled:
    def test_showcase_race_condition(self):
        function = MagicMock(return_value=False)
        callback = BlockingCallbackMock()

        job = CallCallbackWhenFunctionBecomesTrue(function, callback, delay_between_each_try=0)
        job.start()

        callback.assert_not_called_yet()
        function.return_value = True
        callback.assert_not_called_yet()
        # Callback hasn't been called yet because of the slight delay between each check.
        # The Thread is "slow" to figure out something has changed while the test is
        # immediately trying to detect the change
        # ==> Race condition: assertion succeeds when it "shouldn't"

    def test_avoid_race_condition__without_delay(self):
        function = MagicMock(return_value=False)
        callback = BlockingCallbackMock()

        job = CallCallbackWhenFunctionBecomesTrue(function, callback, delay_between_each_try=0)
        job.start()

        callback.assert_not_called_yet()
        function.return_value = True
        with pytest.raises(AssertionError, match="shouldn't have been called"):
            callback.assert_not_called_within(1)

    @mark.integration
    def test_avoid_race_condition__with_delay(self):
        function = MagicMock(return_value=False)
        callback = BlockingCallbackMock()

        job = CallCallbackWhenFunctionBecomesTrue(function, callback, delay_between_each_try=1)
        job.start()

        callback.assert_not_called_yet()
        function.return_value = True
        with pytest.raises(AssertionError, match="shouldn't have been called"):
            callback.assert_not_called_within(5)


def test_with_args():
    function = MagicMock(return_value=False)
    callback = BlockingCallbackMock()

    job = CallCallbackWhenFunctionBecomesTrue(function,
                                              callback,
                                              delay_between_each_try=0,
                                              with_fake_args=True)
    job.start()

    callback.assert_not_called_yet()
    function.return_value = True
    callback.assert_called_within(1)
