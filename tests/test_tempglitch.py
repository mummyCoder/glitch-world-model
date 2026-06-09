from pathlib import Path

from glitch_detection.manifest import ClipRecord, read_labels, read_manifest, write_manifest
from glitch_detection.tempglitch import (
    TempGlitchSample,
    combine_manifests,
    encode_tempglitch_video_url,
    normalize_tempglitch_label,
    parse_tempglitch_video_url,
    select_tempglitch_samples,
    write_tempglitch_full_video_labels,
)


def test_parse_tempglitch_video_url_handles_spaces_and_trailing_label_space():
    ref = parse_tempglitch_video_url(
        "https://huggingface.co/datasets/asgaardlab/TempGlitch/resolve/abc123/"
        "Stuck%20in%20Place/Buggy%20/Godot_Stuck_in_Place_1.mp4"
    )
    assert ref.dataset_revision == "abc123"
    assert ref.category == "Stuck in Place"
    assert ref.public_label_raw == "Buggy "
    assert ref.public_label == "Buggy"
    assert ref.source_name == "Godot_Stuck_in_Place_1"
    assert normalize_tempglitch_label("Normal") == "Normal"


def test_encode_tempglitch_video_url_quotes_category_spaces():
    url = (
        "https://huggingface.co/datasets/asgaardlab/TempGlitch/resolve/abc123/"
        "Frozen Animation/Buggy/video 1.mp4"
    )

    assert encode_tempglitch_video_url(url).endswith("/Frozen%20Animation/Buggy/video%201.mp4")


def _sample(index: int, category: str, label: str) -> TempGlitchSample:
    return TempGlitchSample(
        row_idx=index,
        category=category,
        public_label_raw=label,
        public_label=label,
        is_glitch=label == "Buggy",
        source_name=f"{category}_{label}_{index}",
        file_name=f"{category}_{label}_{index}.mp4",
        video_url=f"https://example.test/{index}.mp4",
        dataset_revision="revision",
        local_video_path=f"videos/{index}.mp4",
    )


def test_random_stratified_sample_is_deterministic_and_balanced():
    candidates = [
        _sample(index, category, label)
        for category in ["Blinking", "Velocity"]
        for label in ["Buggy", "Normal"]
        for index in range(10)
    ]

    first = select_tempglitch_samples(candidates, 3, sample_mode="random-stratified", seed=42)
    second = select_tempglitch_samples(candidates, 3, sample_mode="random-stratified", seed=42)
    different = select_tempglitch_samples(candidates, 3, sample_mode="random-stratified", seed=43)

    assert first == second
    assert first != different
    assert len(first) == 12
    assert {sample.sample_mode for sample in first} == {"random-stratified"}
    assert {sample.seed for sample in first} == {42}
    assert {
        (sample.category, sample.public_label): sum(
            1
            for selected in first
            if selected.category == sample.category and selected.public_label == sample.public_label
        )
        for sample in first
    } == {
        ("Blinking", "Buggy"): 3,
        ("Blinking", "Normal"): 3,
        ("Velocity", "Buggy"): 3,
        ("Velocity", "Normal"): 3,
    }


def test_sequential_sample_keeps_lowest_row_indices_per_group():
    candidates = [_sample(index, "Blinking", "Buggy") for index in [9, 3, 7]]

    selected = select_tempglitch_samples(candidates, 2, sample_mode="sequential", seed=42)

    assert [sample.row_idx for sample in selected] == [3, 7]


def test_combine_manifests_and_write_tempglitch_labels(tmp_path: Path):
    manifest_a = tmp_path / "a" / "manifest.csv"
    manifest_b = tmp_path / "b" / "manifest.csv"
    write_manifest(
        manifest_a,
        [
            ClipRecord(
                clip_id="video_a_000000",
                source="video_a",
                clip_dir="clips/video_a_000000",
                start_frame=0,
                end_frame=3,
                frame_count=4,
                fps=60.0,
            ),
            ClipRecord(
                clip_id="video_a_000001",
                source="video_a",
                clip_dir="clips/video_a_000001",
                start_frame=4,
                end_frame=7,
                frame_count=4,
                fps=60.0,
            ),
        ],
    )
    write_manifest(
        manifest_b,
        [
            ClipRecord(
                clip_id="video_b_000000",
                source="video_b",
                clip_dir="clips/video_b_000000",
                start_frame=0,
                end_frame=3,
                frame_count=4,
                fps=60.0,
            )
        ],
    )

    combined_manifest_path = combine_manifests(
        [manifest_a, manifest_b],
        tmp_path / "combined" / "manifest.csv",
    )
    combined_records = read_manifest(combined_manifest_path)
    assert [record.source for record in combined_records] == ["video_a", "video_a", "video_b"]

    metadata_path = tmp_path / "metadata.csv"
    metadata_path.write_text(
        "\n".join(
            [
                "row_idx,category,public_label_raw,public_label,is_glitch,source,file_name,dataset_revision,video_url,local_video_path",
                "0,Blinking,Buggy,Buggy,1,video_a,video_a.mp4,abc,url,videos/Blinking/Buggy/video_a.mp4",
                "1,Blinking,Normal,Normal,0,video_b,video_b.mp4,abc,url,videos/Blinking/Normal/video_b.mp4",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    labels_path = write_tempglitch_full_video_labels(
        metadata_path=metadata_path,
        manifest_path=combined_manifest_path,
        output_path=tmp_path / "labels.csv",
    )
    labels = read_labels(labels_path)
    assert len(labels) == 1
    assert labels[0].source == "video_a"
    assert labels[0].start_frame == 0
    assert labels[0].end_frame == 7
