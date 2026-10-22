# generate_progress_image.py
import matplotlib

matplotlib.use("Agg")  # ✅ Force non-GUI backend

from io import BytesIO

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np


def generate_progress_image(percent: float) -> BytesIO:
    # Clamp to 0–100
    percent = max(0, min(100, percent))

    # Color by threshold
    if percent >= 100:
        color = "#3498db"  # blue
    elif percent >= 85:
        color = "#2ecc71"  # green
    elif percent >= 50:
        color = "#f39c12"  # orange
    else:
        color = "#e74c3c"  # red

    bg_color = "#1e1e1e"
    text_color = "#ffffff"

    fig, ax = plt.subplots(figsize=(4, 4), dpi=150)
    ax.set_facecolor(bg_color)
    fig.patch.set_facecolor(bg_color)

    # Background ring
    ax.add_patch(
        patches.Wedge(center=(0, 0), r=1, theta1=0, theta2=360, width=0.15, color="#444444")
    )

    # Foreground progress arc
    ax.add_patch(
        patches.Wedge(
            center=(0, 0), r=1, theta1=0, theta2=percent / 100 * 360, width=0.15, color=color
        )
    )

    # Progress text
    ax.text(
        0, 0.1, "Progress", ha="center", va="center", fontsize=10, color=text_color, weight="light"
    )
    ax.text(
        0,
        -0.2,
        f"{int(percent)}%",
        ha="center",
        va="center",
        fontsize=24,
        color=text_color,
        weight="bold",
    )

    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.axis("off")

    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", transparent=False)
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_progress_dial(percent: float, display_percent: float = None) -> BytesIO:

    # Clamp and resolve display vs real %
    display_percent = display_percent if display_percent is not None else percent
    percent = max(0, min(200, percent))

    # Color mapping
    if percent >= 100:
        arc_color = "#FFD700"  # Gold
        label_msg = "Smashed it! Don't stop!!"
    elif percent >= 85:
        arc_color = "#006400"  # DarkGreen
        label_msg = "So close, push now!"
    elif percent >= 70:
        arc_color = "#2ecc71"  # Green
        label_msg = "Fight more, still time!"
    elif percent >= 55:
        arc_color = "#FF8500"  # Orange
        label_msg = "Must work harder!"
    elif percent >= 40:
        arc_color = "#ff8c00"  # DarkOrange
        label_msg = "Not enough yet!"
    elif percent >= 20:
        arc_color = "#e74c3c"  # Red
        label_msg = "No excuses, more fighting!"
    else:
        arc_color = "#8B0000"  # DarkRed
        label_msg = "FIGHT NOW!!"

    text_color = arc_color
    bg_color = "#1e1e1e"

    fig, ax = plt.subplots(figsize=(4.5, 2.6), dpi=150)
    ax.set_aspect("equal")
    ax.set_facecolor(bg_color)
    fig.patch.set_facecolor(bg_color)

    # Inner & outer white ring
    ax.add_patch(patches.Wedge((0, 0), 1.075, 0, 180, width=0.005, color="white"))
    ax.add_patch(patches.Wedge((0, 0), 0.925, 0, 180, width=0.005, color="white"))

    # Background arc (semi-circle)
    ax.add_patch(patches.Wedge((0, 0), 1.0, 0, 180, width=0.15, color="#444444"))

    # Foreground arc (rotated so left-to-right)
    # arc_start_angle = 180
    arc_extent = min(percent, 100) / 100 * 180
    fg_arc = patches.Wedge((0, 0), 1.0, 180 - arc_extent, 180, width=0.15, color=arc_color)

    ax.add_patch(fg_arc)

    # Tick marks + % labels
    tick_percentages = [0, 20, 40, 60, 80, 100]
    for p in tick_percentages:
        angle_deg = 180 - (p / 100 * 180)  # Rotate left-to-right
        angle_rad = np.deg2rad(angle_deg)

        # Tick label
        label_radius = 1.22
        x_label = label_radius * np.cos(angle_rad)
        y_label = label_radius * np.sin(angle_rad)
        ax.text(
            x_label, y_label - 0.04, f"{p}%", ha="center", va="center", color="white", fontsize=8
        )

        # Tick lines
        outer_radius = 1.075
        inner_radius = 0.925
        x_outer = outer_radius * np.cos(angle_rad)
        y_outer = outer_radius * np.sin(angle_rad)
        x_inner = inner_radius * np.cos(angle_rad)
        y_inner = inner_radius * np.sin(angle_rad)
        ax.plot([x_inner, x_outer], [y_inner, y_outer], color="white", lw=1)

    # Main title
    ax.text(
        0,
        -0.18,
        f"Total Kills: {display_percent:.0f}%",
        ha="center",
        va="center",
        fontsize=14,
        color=text_color,
        weight="bold",
    )

    # Large % value
    # ax.text(0, -0.27, f"{display_percent:.0f}%", ha="center", va="center",
    # fontsize=18, color=text_color, weight="bold")

    # Motivational message
    ax.text(
        0,
        -0.38,
        label_msg,
        ha="center",
        va="center",
        fontsize=12,
        color=text_color,
        weight="semibold",
        wrap=True,
    )

    # Axes cleanup
    ax.axis("off")
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-0.6, 1.3)

    # Export
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", transparent=False)
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_exempt_dial() -> BytesIO:

    bg_color = "#1e1e1e"
    arc_color = "#666666"  # Neutral grey
    text_color = "#CCCCCC"

    fig, ax = plt.subplots(figsize=(4.5, 2.6), dpi=150)
    ax.set_aspect("equal")
    ax.set_facecolor(bg_color)
    fig.patch.set_facecolor(bg_color)

    # Background semi-circle arc
    ax.add_patch(patches.Wedge((0, 0), 1.0, 0, 180, width=0.15, color=arc_color))

    # Inner & outer rings (greyed out)
    ax.add_patch(patches.Wedge((0, 0), 1.075, 0, 180, width=0.005, color="#AAAAAA"))
    ax.add_patch(patches.Wedge((0, 0), 0.925, 0, 180, width=0.005, color="#AAAAAA"))

    # Central "EXEMPT" text
    ax.text(
        0, -0.1, "EXEMPT", ha="center", va="center", fontsize=18, color=text_color, weight="bold"
    )

    # Optional subtext
    ax.text(
        0,
        -0.35,
        "No targets assigned this KVK",
        ha="center",
        va="center",
        fontsize=10,
        color=text_color,
        style="italic",
    )

    # Axes cleanup
    ax.axis("off")
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-0.6, 1.3)

    # Export
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", transparent=False)
    plt.close(fig)
    buf.seek(0)
    return buf
