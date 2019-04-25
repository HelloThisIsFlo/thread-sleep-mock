class CallCallbackAfterSleep(Thread):
    def __init__(self, callback, sleep_duration):
        super().__init__(daemon=True)
        self._sleep_duration = sleep_duration
        self._callback = callback

    def run(self):
        time.sleep(self._sleep_duration)
        self._callback()


@patch('time.sleep', new_callable=SleepMock)
def test_call_callback_after_sleep(sleep_mock):
    # Given: An asynchronous job in a Thread
    callback = ThreadSafeCallbackMock()
    sleep_duration = 10
    call_callback_after_sleep = CallCallbackAfterSleep(callback, sleep_duration)


    # When: Starting the Thread
    call_callback_after_sleep.start()


    # Then: Callback is called after sleep duration
    callback.assert_not_called_within(0.01)

    sleep_mock.fast_forward(sleep_duration - 1)
    sleep_mock.assert_current_time(sleep_duration - 1)
    callback.assert_not_called_within(0.01)

    sleep_mock.fast_forward(1)
    sleep_mock.assert_current_time(sleep_duration)
    callback.assert_called_within(0.01)
