import io
import json
import builtins
import pytest


class _FakeFile(io.BytesIO):
    def write(self, s):
        if isinstance(s, str):
            s = s.encode("utf-8")
        return super().write(s)

@pytest.fixture
def fake_fs():
    store = {}

    def _open(path, mode="rb"):
        binary = "b" in mode
        create = any(m in mode for m in "wax")
        read = "r" in mode
        append = "a" in mode

        if create:
            f = _FakeFile()
            if append and path in store:
                f.write(store[path])
            f.seek(0)
            def _close_and_persist():
                store[path] = f.getvalue()
            orig_close = f.close
            def patched_close():
                _close_and_persist()
                orig_close()
            f.close = patched_close
            return f

        if read:
            data = store.get(path, b"")
            return _FakeFile(data)

        return _FakeFile()

    class FS:
        def open(self, path, mode="rb"):
            return _open(path, mode)
        def exists(self, path):
            return path in store
        def write_bytes(self, path, data: bytes):
            store[path] = data
        def read_bytes(self, path):
            return store[path]
        @property
        def mapping(self):
            return store

    return FS()



class FakeWFile(_FakeFile):
    pass

class FakeRFile(_FakeFile):
    pass

@pytest.fixture
def http_harness(mocker):
    class Harness:
        def __init__(self, body=b"", headers=None):
            self.rfile = FakeRFile(body)
            self.wfile = FakeWFile()
            self.headers = headers or {}
            self.send_response = mocker.Mock()
            self.send_header = mocker.Mock()
            self.end_headers = mocker.Mock()
    return Harness
