import pytest

from glitch_detection.failure_triage import (
    FailureBucket,
    allowed_action,
    classify_failure,
    is_oom,
)


@pytest.mark.parametrize(
    ("message", "bucket"),
    [
        (
            "RuntimeError: An attempt has been made to start a new process before the current "
            "process has finished its bootstrapping phase",
            FailureBucket.DATALOADER_SPAWN,
        ),
        (
            "UnicodeDecodeError: 'charmap' codec can't decode byte 0x8f",
            FailureBucket.ENVIRONMENT_DECODE,
        ),
        (
            "FileExistsError: [Errno 17] File exists: outputs/profile",
            FailureBucket.PACKAGING_IDEMPOTENCY,
        ),
        ("torch.cuda.OutOfMemoryError: CUDA out of memory", FailureBucket.CUDA_OOM),
        ("503 ServiceUnavailable", FailureBucket.INFRA_KAGGLE_TRANSIENT),
        ("unrecognized failure", FailureBucket.UNKNOWN),
    ],
)
def test_classify_known_failure_signatures(message: str, bucket: FailureBucket):
    assert classify_failure(message) is bucket


def test_only_cuda_oom_may_advance_oom_ladder():
    assert allowed_action(FailureBucket.DATALOADER_SPAWN) == "stop_and_fix"
    for bucket in FailureBucket:
        assert is_oom(bucket) is (bucket is FailureBucket.CUDA_OOM)
