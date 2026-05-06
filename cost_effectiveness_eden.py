#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 00:20:06 2026

@author: Louise
"""

import math
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
#core
def compute_positions(components, Lside):
    cum_low = 0.0
    cum_high = 0.0
    for c in components:
        c["x0_low"] = cum_low / 100 * Lside
        c["x1_low"] = (cum_low + c["low"]) / 100 * Lside
        c["x0_high"] = cum_high / 100 * Lside
        c["x1_high"] = (cum_high + c["high"]) / 100 * Lside

        if c.get("cost") is not None:
            lo = min(c["low"], c["high"])
            hi = max(c["low"], c["high"])
            if lo == hi:
                c["cost_text"] = f"£{c['cost']:.1f}M\n£{c['cost']/hi:.2f}M/%"
            else:
                c["cost_text"] = f"£{c['cost']:.1f}M\n£{c['cost']/hi:.2f}–£{c['cost']/lo:.2f}M/%"
        else:
            c["cost_text"] = None

        cum_low += c["low"]
        cum_high += c["high"]


def trapezoid_edges_at_y(c, y, Lside):
    t = y / Lside
    xl = c["x0_low"] + t * (c["x0_high"] - c["x0_low"])
    xr = c["x1_low"] + t * (c["x1_high"] - c["x1_low"])
    return xl, xr


def x_center_at_y(c, y, Lside):
    xl, xr = trapezoid_edges_at_y(c, y, Lside)
    return 0.5 * (xl + xr)


def width_at_y(c, y, Lside):
    xl, xr = trapezoid_edges_at_y(c, y, Lside)
    return xr - xl


def draw_width_arrow(ax, c, y_frac, Lside, lw=1.2):
    y = y_frac * Lside
    xl, xr = trapezoid_edges_at_y(c, y, Lside)
    ax.annotate(
        "",
        xy=(xl, y), xytext=(xr, y),
        arrowprops=dict(
            arrowstyle="<->",
            lw=lw,
            color="black",
            shrinkA=0,
            shrinkB=0,
            mutation_scale=10
        )
    )
    return y, 0.5 * (xl + xr)


def add_inside_text(ax, c, y_frac, Lside, fontsize=11, x_shift_frac=0.0):
    y = y_frac * Lside
    xc = x_center_at_y(c, y, Lside) + x_shift_frac * Lside

    ax.text(
        xc, y + 0.040 * Lside,
        c["label"],
        ha="center", va="center",
        fontsize=fontsize
    )

    if c.get("cost_text") is not None:
        ax.text(
            xc, y - 0.060 * Lside,
            c["cost_text"],
            ha="center", va="top",
            fontsize=fontsize - 1
        )

    return width_at_y(c, y, Lside)


def add_outside_label(ax, c, arrow_y_frac, text_xy_frac, Lside, fontsize=10.5):
    y, xc = draw_width_arrow(ax, c, arrow_y_frac, Lside)

    x_text = text_xy_frac[0] * Lside
    y_text = text_xy_frac[1] * Lside

    ax.annotate(
        c["label"],
        xy=(xc, y),
        xytext=(x_text, y_text + 0.035 * Lside),
        fontsize=fontsize,
        ha="left", va="bottom",
        arrowprops=dict(
            arrowstyle="-|>",
            lw=1.1,
            color="black",
            mutation_scale=10
        )
    )

    if c.get("cost_text") is not None:
        ax.text(
            x_text, y_text - 0.010 * Lside,
            c["cost_text"],
            fontsize=fontsize - 1,
            ha="left", va="top"
        )



# Panel drawing

def draw_panel(
    ax, title, FEV, depth, total_cost, components,
    total_mitig_text,
    total_cost_y=0.22,
    inside_cfg=None,
    outside_cfg=None,
    residual_cfg=None,
    show_fev_header=True
):
    Lside = math.sqrt(FEV * 1_000_000 / depth)
    compute_positions(components, Lside)

    ax.set_aspect("equal")

    # Outer square
    ax.add_patch(
        Rectangle(
            (0, 0), Lside, Lside,
            fill=False, edgecolor="#3344cc", linewidth=2.3
        )
    )

    # Component polygons
    for c in components:
        poly = Polygon(
            [
                (c["x0_low"], 0), (c["x1_low"], 0),
                (c["x1_high"], Lside), (c["x0_high"], Lside)
            ],
            closed=True,
            facecolor=c["color"],
            edgecolor="black",
            linewidth=1.6
        )
        ax.add_patch(poly)

    # Title
    if show_fev_header:
        ax.set_title(
            f"{title}: FEV ≈ {round(Lside):d}² m² × {depth:.0f} m ≈ {FEV:.2f} Mm³",
            fontsize=14
        )
    else:
        ax.set_title(title, fontsize=14)

    # Total arrow
    y_total = total_cost_y * Lside
    ax.annotate(
        "",
        xy=(0, y_total), xytext=(Lside, y_total),
        arrowprops=dict(
            arrowstyle="<->",
            lw=1.6,
            color="black",
            shrinkA=0,
            shrinkB=0,
            mutation_scale=10
        )
    )
    ax.text(
        0.06 * Lside, y_total + 0.055 * Lside,
        total_mitig_text,
        fontsize=11.5, ha="left", va="bottom"
    )
    ax.text(
        0.06 * Lside, y_total - 0.055 * Lside,
        f"£{total_cost:.1f}M",
        fontsize=11.5, ha="left", va="center"
    )

    # Inside labels
    if inside_cfg is None:
        inside_cfg = {}
    for short, cfg in inside_cfg.items():
        c = next(comp for comp in components if comp["short"] == short)
        y_frac = cfg.get("y", 0.70)

        draw_width_arrow(ax, c, y_frac, Lside, lw=1.25)
        add_inside_text(
            ax, c, y_frac, Lside,
            fontsize=cfg.get("fontsize", 11),
            x_shift_frac=cfg.get("x_shift_frac", 0.0)
        )

    # Outside labels
    if outside_cfg is None:
        outside_cfg = {}
    for short, cfg in outside_cfg.items():
        c = next(comp for comp in components if comp["short"] == short)
        add_outside_label(
            ax, c,
            arrow_y_frac=cfg["arrow_y"],
            text_xy_frac=cfg["text_xy"],
            Lside=Lside,
            fontsize=cfg.get("fontsize", 10.5)
        )

    # Residual label
    if residual_cfg is not None:
        c = next(comp for comp in components if comp["short"] == "Residual")
        y = residual_cfg.get("arrow_y", 0.55) * Lside
        xc = x_center_at_y(c, y, Lside)
        ax.annotate(
            c["label"],
            xy=(xc, y),
            xytext=(
                residual_cfg["text_xy"][0] * Lside,
                residual_cfg["text_xy"][1] * Lside
            ),
            fontsize=residual_cfg.get("fontsize", 11),
            ha="left", va="center",
            arrowprops=dict(
                arrowstyle="-|>",
                lw=1.1,
                color="black",
                mutation_scale=10
            )
        )

    ax.set_xlabel("Sidelength (m)", fontsize=11)
    ax.set_ylabel("Sidelength (m)", fontsize=11)
    ax.set_xlim(0, 1.30 * Lside)
    ax.set_ylim(0, Lside)


depth = 2.0

# Use the benchmark/event FEVs from your section 5 analysis
FEV_2005 = 2   
FEV_2015 = 11.42

# Scheme costs from section 5
cost_post2005 = 38.095   # £M, combined phase 1 + phase 2
cost_post2015 = 25.000   # £M

# -------------------------------------------------
# COMPONENTS
# Only one defence category kept: combined walls/embankments
# Anything not mitigated in 2015 is residual
# -------------------------------------------------
components_2005 = [
    {
        "short": "HW",
        "label": "Walls/embankments 100%",
        "low": 100, "high": 100,
        "cost": cost_post2005,
        "color": "#8f8fe9"
    }
]

components_2015 = [
    {
        "short": "HW",
        "label": "Walls/embankments 61%",
        "low": 61, "high": 61,
        "cost": cost_post2015,
        "color": "#8edc8a"
    },
    {
        "short": "Residual",
        "label": "Residual 39%",
        "low": 39, "high": 39,
        "cost": None,
        "color": "white"
    }
]

# -------------------------------------------------
# PLOT
# -------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(14, 7))

# 2005 scenario
draw_panel(
    axes[0],
    "2005 benchmark flood",
    FEV_2005,
    depth,
    cost_post2005,
    components_2005,
    total_mitig_text="Total mitigated 100%",
    inside_cfg={
        "HW": {"y": 0.72, "fontsize": 12}
    },
    outside_cfg={},
    residual_cfg=None
)

# 2015 scenario
draw_panel(
    axes[1],
    "2015 flood",
    FEV_2015,
    depth,
    cost_post2015,
    components_2015,
    total_mitig_text="Total mitigated 61%",
    inside_cfg={
        "HW": {"y": 0.72, "fontsize": 12}
    },
    outside_cfg={},
    residual_cfg={
        "arrow_y": 0.55,
        "text_xy": (1.03, 0.58),
        "fontsize": 11
    }
)

plt.tight_layout()
plt.show()