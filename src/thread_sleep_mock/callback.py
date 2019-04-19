from threading import Event


class ThreadSafeCallbackMock(Event):
    def __call__(self):
        self.set()

    def assert_already_called(self):
        assert self.is_set(), "Callback was not yet called!"

    def assert_called_within(self, timeout):
        assert self.wait(timeout), "Callback was never called!"

    def assert_not_called_yet(self):
        assert not self.is_set(), "Callback shouldn't have been called, but was!"
