from __future__ import annotations

import argparse
import asyncio
import json
import mimetypes
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.vision_client import InventoryVisionClient


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Test OpenAI inventory screenshot extraction without writing inventory data."
    )
    parser.add_argument("image", help="Path to a resources or speedups screenshot.")
    parser.add_argument(
        "--type",
        choices=["resources", "speedups", "materials", "unknown"],
        default=None,
        dest="import_type_hint",
        help="Optional expected screenshot type hint.",
    )
    return parser


async def _run(args: argparse.Namespace) -> int:
    image_path = Path(args.image).expanduser().resolve()
    if not image_path.exists() or not image_path.is_file():
        print(f"Image file not found: {image_path}", file=sys.stderr)
        return 2

    image_bytes = image_path.read_bytes()
    content_type = mimetypes.guess_type(str(image_path))[0] or "image/png"
    client = InventoryVisionClient()
    result = await client.analyse_image(
        image_bytes,
        filename=image_path.name,
        content_type=content_type,
        import_type_hint=args.import_type_hint,
    )

    output = {
        "ok": result.ok,
        "detected_image_type": result.detected_image_type,
        "confidence_score": result.confidence_score,
        "warnings": result.warnings,
        "values": result.values,
        "model": result.model,
        "prompt_version": result.prompt_version,
        "fallback_used": result.fallback_used,
        "error": result.error,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if result.ok else 1


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
