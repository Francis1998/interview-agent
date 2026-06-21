#!/usr/bin/env python3
"""Generate demo GIF assets from simulated agent run frames."""

from __future__ import annotations

from pathlib import Path

try:
    import imageio.v3 as iio
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit("Install dev deps: pip install -e '.[dev]'")

FRAMES_DIR = Path(__file__).resolve().parents[1] / "assets" / "frames"
OUTPUT_GIF = Path(__file__).resolve().parents[1] / "assets" / "demo-agent-run.gif"

STEPS = [
    ("IDLE", "Waiting for question…", "#64748b"),
    ("PLANNING", "Classifying topic: networking", "#6366f1"),
    ("RETRIEVING", "Searching knowledge base…", "#8b5cf6"),
    ("REASONING", "GPT-4o-mini generating answer", "#22d3ee"),
    ("ANSWERING", "Structuring interview response", "#10b981"),
    ("DONE", "TCP handshake explained ✓", "#22c55e"),
]


def render_frame(step: str, detail: str, color: str, index: int) -> Image.Image:
    """Render a single demo frame."""
    img = Image.new("RGB", (800, 450), (10, 14, 23))
    draw = ImageDraw.Draw(img)
    try:
        font_lg = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
        font_sm = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except OSError:
        font_lg = ImageFont.load_default()
        font_sm = ImageFont.load_default()

    draw.rounded_rectangle((30, 30, 770, 420), radius=16, outline=(30, 41, 59), width=2)
    draw.text((50, 50), "Interview Agent", fill=(34, 211, 238), font=font_lg)
    draw.text((50, 100), f"State: {step}", fill=color, font=font_lg)
    draw.text((50, 160), detail, fill=(226, 232, 240), font=font_sm)
    draw.text((50, 200), "Rationale traces · Event log · Multi-LLM", fill=(148, 163, 184), font=font_sm)

    bar_w = 680
    progress = (index + 1) / len(STEPS)
    draw.rectangle((50, 360, 50 + bar_w, 380), fill=(30, 41, 59))
    draw.rectangle((50, 360, 50 + int(bar_w * progress), 380), fill=(99, 102, 241))
    draw.text((50, 390), f"Frame {index + 1}/{len(STEPS)}", fill=(148, 163, 184), font=font_sm)
    return img


def main() -> None:
    """Generate GIF from rendered frames."""
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    frames: list[Image.Image] = []
    for i, (step, detail, color) in enumerate(STEPS):
        frame = render_frame(step, detail, color, i)
        path = FRAMES_DIR / f"frame_{i:02d}.png"
        frame.save(path)
        frames.append(frame)
        frames.append(frame.copy())  # hold frame for readability

    OUTPUT_GIF.parent.mkdir(parents=True, exist_ok=True)
    iio.imwrite(
        OUTPUT_GIF,
        [f for f in frames],
        duration=600,
        loop=0,
    )
    print(f"Generated {OUTPUT_GIF} ({len(frames)} frames)")


if __name__ == "__main__":
    main()
