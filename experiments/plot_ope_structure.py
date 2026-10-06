#!/usr/bin/env python3
"""Render the executed structural census, with no policy performance quantities."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.result.read_text())['archives']
    names = list(data)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), layout='constrained', sharey=True)
    for ax, field, title, color in zip(axes, ['segments', 'policy_names'],
                                       ['Recording segments', 'Distinct policy-name strings'],
                                       ['#255F85', '#43795A']):
        values = [data[n][field] for n in names]
        bars = ax.barh(range(len(names)), values, color=color)
        ax.bar_label(bars, labels=[f'{v:,}' for v in values], padding=5, fontsize=10)
        ax.set_xlim(0, max(values)*1.2)
        ax.set_xlabel('Count')
        ax.set_title(title, fontsize=12)
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(axis='x', alpha=.15)
        ax.set_axisbelow(True)
    axes[0].set_yticks(range(len(names)), names, fontsize=10)
    axes[0].invert_yaxis()
    fig.suptitle('Pinned F110 archives: unfiltered structural census', fontsize=14)
    fig.supxlabel('Reset segments are not verified independent runs. No returns or rankings computed.', fontsize=10)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=170)
    plt.close(fig)


if __name__ == '__main__':
    main()
