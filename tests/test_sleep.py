import time
from threading import Thread, Event
from unittest.mock import patch, MagicMock

from src.thread_sleep_mock.sleep import SleepMock

TIMEOUT = 0.5


def give_some_time_for_thread_to_execute():
    time.sleep(0.01)


def async_sleep_for_duration_and_set_event(duration, event):
    class Job(Thread):
        def run(self):
            time.sleep(duration)
            event.set()

    job = Job()
    job.daemon = True
    job.start()


@patch('src.thread_sleep_mock.sleep.original_time_sleep')
@patch('time.sleep', new_callable=SleepMock)
def test_duration_below_1s__passthrough(_mock_sleep, original_time_sleep):
    done = Event()
    async_sleep_for_duration_and_set_event(0.12345, done)
    done.wait(TIMEOUT)
    original_time_sleep.assert_called_with(0.12345)


@patch('src.thread_sleep_mock.sleep.original_time_sleep')
@patch('time.sleep', new_callable=SleepMock)
def test_duration_above_or_equal_1s__capture(mock_sleep, original_time_sleep):
    done = Event()
    async_sleep_for_duration_and_set_event(1, done)
    mock_sleep.fast_forward(1)
    assert done.wait(TIMEOUT)

    original_time_sleep.assert_not_called()


@patch('time.sleep', new_callable=SleepMock)
def test_block_until_sleep_is_over__1s(sleep_mock):
    duration = 1
    is_complete = Event()

    async_sleep_for_duration_and_set_event(duration, is_complete)

    assert not is_complete.is_set()
    sleep_mock.fast_forward(1)
    assert is_complete.wait()


@patch('time.sleep', new_callable=SleepMock)
def test_block_until_sleep_is_over__4s(sleep_mock):
    duration = 4
    is_complete = Event()

    async_sleep_for_duration_and_set_event(duration, is_complete)

    assert not is_complete.is_set()

    sleep_mock.fast_forward(3)
    sleep_mock.assert_current_time(3)
    assert not is_complete.is_set()

    sleep_mock.fast_forward(1)
    sleep_mock.assert_current_time(4)
    assert is_complete.wait()


@patch('time.sleep', new_callable=SleepMock)
def test_multiple_sleep_during_fast_forward_duration(sleep_mock):
    two_seconds = 2
    function = MagicMock()

    class CallFunctionEvery2s(Thread):
        def __init__(self):
            super().__init__()
            self._should_stop = Event()

        def run(self):
            while not self._should_stop.is_set():
                function()
                time.sleep(two_seconds)

        def stop(self):
            self._should_stop.set()

    job = CallFunctionEvery2s()
    job.start()

    assert function.call_count == 1
    function.reset_mock()

    sleep_mock.fast_forward(two_seconds)
    give_some_time_for_thread_to_execute()
    assert function.call_count == 1
    function.reset_mock()

    sleep_mock.fast_forward(two_seconds * 4)
    give_some_time_for_thread_to_execute()
    assert function.call_count == 4

    job.stop()
    sleep_mock.fast_forward(two_seconds)  # Unlock the job


@patch('time.sleep', new_callable=SleepMock)
def test_multiple_threads(sleep_mock):
    complete_after_1s = Event()
    complete_after_4s = Event()
    complete_after_10s = Event()
    complete_after_15s = Event()

    async_sleep_for_duration_and_set_event(1, complete_after_1s)
    async_sleep_for_duration_and_set_event(4, complete_after_4s)
    async_sleep_for_duration_and_set_event(10, complete_after_10s)
    async_sleep_for_duration_and_set_event(15, complete_after_15s)

    assert not complete_after_1s.is_set()
    assert not complete_after_4s.is_set()
    assert not complete_after_10s.is_set()
    assert not complete_after_15s.is_set()

    sleep_mock.fast_forward(1)
    sleep_mock.assert_current_time(1)
    assert complete_after_1s.wait(TIMEOUT)
    assert not complete_after_4s.is_set()
    assert not complete_after_10s.is_set()
    assert not complete_after_15s.is_set()

    sleep_mock.fast_forward(3)
    sleep_mock.assert_current_time(4)
    assert complete_after_1s.is_set()
    assert complete_after_4s.wait(TIMEOUT)
    assert not complete_after_10s.is_set()
    assert not complete_after_15s.is_set()

    sleep_mock.fast_forward(8.5)
    sleep_mock.assert_current_time(12.5)
    assert complete_after_1s.is_set()
    assert complete_after_4s.is_set()
    assert complete_after_10s.wait(TIMEOUT)
    assert not complete_after_15s.is_set()

    sleep_mock.fast_forward(2.5)
    sleep_mock.assert_current_time(15)
    assert complete_after_1s.is_set()
    assert complete_after_4s.is_set()
    assert complete_after_10s.is_set()
    assert complete_after_15s.wait(TIMEOUT)
