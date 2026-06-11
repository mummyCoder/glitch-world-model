from scripts.build_tempglitch_validation_manifest import evenly_spaced_starts


def test_evenly_spaced_starts_are_deterministic_and_bounded():
    assert evenly_spaced_starts(100, 16, 4) == [0, 28, 56, 84]
    assert evenly_spaced_starts(10, 16, 4) == []
    assert evenly_spaced_starts(100, 16, 1) == [42]
