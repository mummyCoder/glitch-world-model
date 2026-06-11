from glitch_detection.pairs import (
    group_sources_by_pair,
    infer_tempglitch_pair_id,
    pair_leakage_report,
)


def test_infer_tempglitch_pair_id_matches_buggy_and_normal_suffixes():
    assert infer_tempglitch_pair_id("Godot_Blinking_1") == "pair-index:1"
    assert infer_tempglitch_pair_id("Godot_Blinking_Normal_1.mp4") == "pair-index:1"
    assert infer_tempglitch_pair_id("Godot_Frozen_Animation_Buggy_Sample_103") == "pair-index:103"
    assert (
        infer_tempglitch_pair_id("Godot_Frozen_Animation_Platformer_Normal_103") == "pair-index:103"
    )
    assert (
        infer_tempglitch_pair_id("Godot_Stuck_In_Place_TPS_Buggy_3")
        == "pair-environment:TPS:index:3"
    )
    assert (
        infer_tempglitch_pair_id("Godot_Animation_TPS_Normal_3") == "pair-environment:TPS:index:3"
    )


def test_infer_tempglitch_pair_id_falls_back_to_source_without_numeric_suffix():
    assert infer_tempglitch_pair_id("unmatched_source.mp4") == "source:unmatched_source"


def test_group_sources_by_pair_scopes_heuristic_to_category():
    rows = [
        {"source": "Godot_Blinking_1", "category": "Blinking"},
        {"source": "Godot_Blinking_Normal_1", "category": "Blinking"},
        {"source": "Godot_Shooting_Error_Buggy_1", "category": "Shooting Error"},
    ]

    groups = group_sources_by_pair(rows)

    assert groups == {
        "Blinking/pair-index:1": ["Godot_Blinking_1", "Godot_Blinking_Normal_1"],
        "Shooting Error/pair-index:1": ["Godot_Shooting_Error_Buggy_1"],
    }


def test_pair_leakage_report_identifies_suspected_cross_split_pairs():
    rows = [
        {
            "source": "Godot_Blinking_1",
            "category": "Blinking",
            "label": "Buggy",
            "split": "train",
        },
        {
            "source": "Godot_Blinking_Normal_1",
            "category": "Blinking",
            "label": "Normal",
            "split": "test",
        },
        {
            "source": "Godot_Blinking_2",
            "category": "Blinking",
            "label": "Buggy",
            "split": "validation",
        },
    ]

    report = pair_leakage_report(rows)

    assert report["grouping_mode"] == "pair_id_heuristic"
    assert report["group_count"] == 2
    assert report["suspected_pair_count"] == 1
    assert report["cross_split_pair_count"] == 1
    assert report["cross_split_pairs"][0]["pair_id_heuristic"] == "Blinking/pair-index:1"
    assert report["cross_split_pairs"][0]["splits"] == ["test", "train"]
