from justin.browser.shared import pacing


class TestPause:
    def test_pace_zero_skips_sleep(self, monkeypatch) -> None:
        slept: list[float] = []
        monkeypatch.setattr(pacing.time, "sleep", slept.append)

        monkeypatch.setattr(pacing, "PACE", 0)
        pacing.pause(1.0)

        monkeypatch.setattr(pacing, "PACE", 2.0)
        monkeypatch.setattr(pacing, "SPREAD", 0)
        pacing.pause(1.0)

        assert slept == [2.0]


class TestVaried:
    def test_pauses_are_not_identical(self) -> None:
        drawn = [pacing.varied(1.0) for _ in range(5)]

        assert len(set(drawn)) == len(drawn)

    def test_deviation_scales_with_the_value(self, monkeypatch) -> None:
        monkeypatch.setattr(pacing, "SPREAD", 0.5)

        short = [pacing.varied(0.4) for _ in range(200)]
        long = [pacing.varied(2.0) for _ in range(200)]

        assert all(0.2 <= value <= 0.6 for value in short)
        assert all(1.0 <= value <= 3.0 for value in long)

    def test_zero_spread_keeps_the_value(self, monkeypatch) -> None:
        monkeypatch.setattr(pacing, "SPREAD", 0)

        assert pacing.varied(0.3) == 0.3
