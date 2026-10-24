import sys

from justin.shared.run_mode import is_debug


class TestIsDebug:
    def test_detected_by_tracer(self, monkeypatch) -> None:
        monkeypatch.setattr(sys, "gettrace", lambda: object())

        assert is_debug()

    def test_detected_by_pydevd(self, monkeypatch) -> None:
        """PyCharm loads pydevd even with no tracer set."""
        monkeypatch.setattr(sys, "gettrace", lambda: None)
        monkeypatch.setitem(sys.modules, "pydevd", object())

        assert is_debug()

    def test_plain_run_is_not_debug(self, monkeypatch) -> None:
        monkeypatch.setattr(sys, "gettrace", lambda: None)
        monkeypatch.delitem(sys.modules, "pydevd", raising=False)

        assert not is_debug()
