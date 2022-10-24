# Thread Sleep Mock
Control time: Mock `time.sleep(...)` in Threads, fast-forward in time, perform your assertions at specific points in the future.

## Usage
2 classes are provided: 
- `SleepMock`: The mock itself, used to mock `time.sleep(...)`
- `BlockingCallbackMock()`: A mock callback used to perform blocking assertions. In other words, the assertion will wait until either: the condition is true, or the timeout has been reached  
  - `assert_called_within(TIMEOUT)`
  - `assert_not_called_within(TIMEOUT)`
  - `assert_already_called()`
  - `assert_not_called_yet()`

## Usage
1. Use `SleepMock` to patch `time.sleep`
   ```python
    @patch('time.sleep', new_callable=SleepMock)
    ```
2. Give the `BlockingCallbackMock` to the function under test
   ```python
   callback_mock = BlockingCallbackMock()
   async_function_that_calls_callback_when_finished(callback_mock)
   ```

3. Move forward in time and assert the callback was called
   ```python
   sleep_mock.fast_forward(20) # Simulate that 20 seconds have passed
   callback_mock.assert_called_within(2) # Check that the callback was called
   ```

### Example
```python
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
    callback = BlockingCallbackMock()
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
```
