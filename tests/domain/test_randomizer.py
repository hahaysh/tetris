import pytest

from tetris_web.domain.randomizer import PIECE_KINDS, SevenBag


def test_each_bag_contains_every_piece_once() -> None:
    randomizer = SevenBag(seed=20260819)

    pieces = [randomizer.next_piece() for _ in range(28)]

    for offset in range(0, len(pieces), len(PIECE_KINDS)):
        assert set(pieces[offset : offset + len(PIECE_KINDS)]) == set(PIECE_KINDS)


def test_equal_seeds_produce_equal_sequences() -> None:
    first = SevenBag(seed="replay")
    second = SevenBag(seed="replay")

    assert [first.next_piece() for _ in range(50)] == [
        second.next_piece() for _ in range(50)
    ]


def test_peek_does_not_consume_pieces() -> None:
    randomizer = SevenBag(seed=42)

    preview = randomizer.peek(10)

    assert tuple(randomizer.next_piece() for _ in range(10)) == preview


def test_negative_preview_size_is_rejected() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        SevenBag(seed=42).peek(-1)
