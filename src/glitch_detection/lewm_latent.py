from __future__ import annotations

import argparse
import os
from pathlib import Path


class LeWMUnavailableError(RuntimeError):
    """Raised when the LeWM scorer is requested before model dependencies are ready."""


def resolve_checkpoint(checkpoint: Path | None) -> Path:
    candidate = checkpoint or (
        Path(os.environ["LEWM_CHECKPOINT"]) if "LEWM_CHECKPOINT" in os.environ else None
    )
    if candidate is None:
        raise LeWMUnavailableError(
            "LeWM latent scoring requires a checkpoint. Pass --checkpoint PATH or set "
            "LEWM_CHECKPOINT. Next step: download/convert a LeWM checkpoint from the "
            "official Hugging Face collection, then implement latent prediction error."
        )
    if not candidate.exists():
        raise LeWMUnavailableError(f"LeWM checkpoint does not exist: {candidate}")
    return candidate


def score_manifest(
    manifest_path: Path,
    labels_path: Path | None,
    output_path: Path,
    checkpoint: Path | None = None,
) -> Path:
    _ = manifest_path
    _ = labels_path
    _ = output_path
    resolve_checkpoint(checkpoint)
    raise LeWMUnavailableError(
        "LeWM checkpoint loading is not implemented yet. The scorer slot is ready; "
        "next implementation step is to load JEPA, encode clip frames, predict next "
        "latent embeddings, and write scores as latent prediction error."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score clips with LeWM latent prediction error.")
    parser.add_argument("--manifest", required=True, type=Path, help="Path to manifest.csv.")
    parser.add_argument("--labels", type=Path, default=None, help="Optional labels CSV.")
    parser.add_argument("--output", required=True, type=Path, help="Output scores.csv path.")
    parser.add_argument("--checkpoint", type=Path, default=None, help="LeWM checkpoint path.")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        output_path = score_manifest(args.manifest, args.labels, args.output, args.checkpoint)
    except LeWMUnavailableError as exc:
        raise SystemExit(f"LeWM latent scorer is not ready: {exc}") from exc
    print(f"Wrote scores: {output_path}")


if __name__ == "__main__":
    main()
