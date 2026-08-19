import pytest

from tetris_web.domain.scoring import gravity_interval, level_for_lines, line_clear_points


@pytest.mark.parametrize(
    ("lines", "expected"),
    [(0, 0), (1, 100), (2, 300), (3, 500), (4, 800)],
)
def test_line_clear_points_follow_the_mvp_table(lines: int, expected: int) -> None:
    assert line_clear_points(lines, level=1) == expected
    assert line_clear_points(lines, level=3) == expected * 3


def test_level_increases_every_ten_lines() -> None:
    assert level_for_lines(0) == 1
    assert level_for_lines(9) == 1
    assert level_for_lines(10) == 2
    assert level_for_lines(24) == 3


def test_gravity_never_drops_below_one_tick() -> None:
    assert gravity_interval(1) == 48
    assert gravity_interval(999) == 5
