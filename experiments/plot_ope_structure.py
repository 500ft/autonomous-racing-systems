#!/usr/bin/env python3
"""Render structural figures and tables from the committed result, without archives."""
import argparse
import csv
import json
from pathlib import Path

from matplotlib.ticker import MaxNLocator, StrMethodFormatter

import figure_style as fs
from figure_style import COLORS as C

# Pair real/sim versions; the final archive has no corresponding sim-v2 file.
ARCHIVES = {
    'dataset_real_v0.zip': 'Real v0',
    'dataset_sim_v0.zip': 'Sim v0',
    'f110-real-v1.zip': 'Real v1',
    'f110-sim-v1.zip': 'Sim v1',
    'f110-real-stoch-v2.zip': 'Real stochastic v2',
}


SEGMENT_COLOR, NAME_COLOR = '#2980b9', '#7d3c98'


def render_figure(result):
    archives = result['archives']
    names = list(ARCHIVES)
    labels = list(ARCHIVES.values())
    fig = fs.figure(height_in=6.2)
    grid = fig.add_gridspec(2, 2, height_ratios=[1, 1.1])
    axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1]), fig.add_subplot(grid[1, :])]
    segments = [archives[n]['segments'] for n in names]
    policy = [archives[n]['policy_names'] for n in names]
    most = labels[segments.index(max(segments))]
    for ax, values, title, color, marker in zip(
        axes[:2], [segments, policy],
        [f'{most}: most segments ({max(segments):,})',
         f'{min(policy):,} to {max(policy):,} policy-name strings per archive'],
        [SEGMENT_COLOR, NAME_COLOR], ['o', 's'],
    ):
        ax.hlines(range(len(names)), 0, values, color=color, linewidth=1.5)
        ax.plot(values, range(len(names)), marker, color=color, markersize=5)
        for y, value in enumerate(values):
            ax.annotate(f'{value:,}', (value, y), xytext=(6, 0), textcoords='offset points', va='center',
                        fontsize=fs.SMALL)
        ax.set_xlim(0, max(values)*1.3)
        ax.xaxis.set_major_locator(MaxNLocator(4))
        ax.set_xlabel('Recording segments [count]' if values is segments else 'Policy-name strings [count]')
        ax.set_title(title)
    axes[1].tick_params(labelleft=False)
    ax = axes[2]
    early = [archives[n]['flags_before_segment_end'] for n in names]
    at_end = [archives[n]['done_or_truncated_rows']-e for n, e in zip(names, early)]
    ax.barh(range(len(names)), at_end, height=.48, color=SEGMENT_COLOR, label='At segment end')
    ax.barh(range(len(names)), early, left=at_end, height=.48, color=C['alarm'], edgecolor='white',
            hatch='////', label='Before segment end')
    for y, (end, before) in enumerate(zip(at_end, early)):
        ax.annotate(f'{end:,} + {before:,}', (end+before, y), xytext=(6, 0), textcoords='offset points',
                    va='center', fontsize=fs.SMALL)
    ax.set_xlim(0, max(a+b for a, b in zip(at_end, early))*1.27)
    ax.set_xlabel('Rows with done OR truncated [count]')
    flagged = [label for label, e in zip(labels, early) if e]
    ax.set_title(f'{" and ".join(flagged)} alone raises flags before a segment ends ({sum(early):,} rows)'
                 if len(flagged) == 1 else 'Flag alignment with structural boundaries')
    ax.legend(loc='lower right')
    for letter, ax in zip('ABC', axes):
        ax.set_yticks(range(len(names)), labels)
        ax.set_ylim(len(names)-.5, -.5)
        ax.grid(axis='y', visible=False)
        ax.xaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
        fs.panel_letter(ax, letter)
    fs.title(fig, 'F110 archives | STRUCTURAL CENSUS',
             'Unfiltered records; episode meaning and policy execution unresolved')
    fs.footnote(fig, 'Resets do not establish independent episodes. Name matches do not establish executable policies.\n'
                     'Counts only; no return or ranking analysis. Archive filenames and sources: structure.md.')
    return fig


def write_csv(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def render_tables(result, directory):
    rows = []
    for name, label in ARCHIVES.items():
        a = result['archives'][name]
        rows.append(dict(
            label=label, archive=name, rows=a['rows'], segments=a['segments'],
            policy_names=a['policy_names'], min_rows_per_segment=a['length_range_rows'][0],
            max_rows_per_segment=a['length_range_rows'][1], done_rows=a['done_rows'],
            truncated_rows=a['truncated_rows'], both_flags_rows=a['both_flags_rows'],
            done_or_truncated_rows=a['done_or_truncated_rows'],
            flags_at_segment_end=a['done_or_truncated_rows']-a['flags_before_segment_end'],
            flags_before_segment_end=a['flags_before_segment_end'],
            unflagged_segment_ends=a['unflagged_segment_ends'],
            bundled_config_matches=sum(v is not None for v in a['bundled_config_mapping'].values()),
            benchmark_config_matches=sum(v is not None for v in a['benchmark_config_mapping'].values()),
        ))
    aliases = [dict(registration=name, archive=a['archive'],
                    listed_eval_names=len(a['eval_model_names']),
                    missing_eval_names=len(a['eval_names_missing_from_loaded_archive']),
                    listed_bad_indices=len(a['bad_trajectory_indices']),
                    bad_indices_outside_rows=len(a['bad_indices_outside_loaded_rows']))
               for name, a in result['registrations'].items()]
    write_csv(directory/'structure.csv', rows)
    write_csv(directory/'loader_aliases.csv', aliases)
    lines = [
        '# Unfiltered archive structure', '',
        'Generated by `experiments/plot_ope_structure.py` from [result.json](result.json).',
        'Download [archive counts](structure.csv) and [loader aliases](loader_aliases.csv).',
        'All numbers below are counts or observed row-count ranges, with no filtering.', '',
        '## Archive identity and recordings', '',
        '| Figure label | Explicit archive filename | Rows | Segments | Policy-name strings | Rows/segment, min to max |',
        '| --- | --- | ---: | ---: | ---: | ---: |',
    ]
    for r in rows:
        lines.append(f"| {r['label']} | `{r['archive']}` | {r['rows']:,} | {r['segments']:,} | {r['policy_names']:,} | {r['min_rows_per_segment']:,} to {r['max_rows_per_segment']:,} |")
    lines += ['', 'A segment begins when timestep stops increasing. A reset flag does not',
              'establish an independent episode. Pairing real/sim rows here expresses archive',
              'versions only; no experimental pairing has been established.', '',
              '## Apparent terminal flags', '',
              '| Archive label | done rows | truncated rows | Either flag rows | Before segment end rows | Unflagged ends |',
              '| --- | ---: | ---: | ---: | ---: | ---: |']
    for r in rows:
        lines.append(f"| {r['label']} | {r['done_rows']:,} | {r['truncated_rows']:,} | {r['done_or_truncated_rows']:,} | {r['flags_before_segment_end']:,} | {r['unflagged_segment_ends']:,} |")
    lines += ['', '`Either` is the union, so a row with both flags is counted once. Figure C',
              'splits that union into rows at and before segment ends. Those early flags',
              'cannot be counted as independent recordings; their physical meaning is unresolved.', '',
              '## Loader registrations', '',
              '| Registration | Selected archive | Missing / listed evaluation names | Out-of-range / listed bad indices |',
              '| --- | --- | ---: | ---: |']
    for r in aliases:
        missing = f"{r['missing_eval_names']} / {r['listed_eval_names']}" if r['listed_eval_names'] else 'None listed'
        bad = f"{r['bad_indices_outside_rows']} / {r['listed_bad_indices']}" if r['listed_bad_indices'] else 'None listed'
        lines.append(f"| `{r['registration']}` | `{r['archive']}` | {missing} | {bad} |")
    lines += ['', '“None listed” means the registration supplied no entries for that field.',
              'The explicit real-stochastic archive remains separate from the similarly named',
              'registrations that select simulation-v1. These are source-code mappings;',
              'they do not establish which file a published experiment used.', '',
              '## Exact configuration-filename correspondence', '',
              '| Archive label | Archived names | Bundled config matches | Benchmark config matches |',
              '| --- | ---: | ---: | ---: |']
    for r in rows:
        lines.append(f"| {r['label']} | {r['policy_names']:,} | {r['bundled_config_matches']:,} | {r['benchmark_config_matches']:,} |")
    lines += ['', 'Zero means no exact filename match in that pinned tree. A match does not',
              'qualify policy execution, observation reconstruction or action probabilities.',
              'Rights, episode semantics and independence remain unresolved. See the',
              '[qualification report](../../reports/ope_qualification.md) for the separate gates.', '']
    (directory/'structure.md').write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='PNG path; SVG and tables saved beside it')
    args = parser.parse_args()
    result = json.loads(args.result.read_text())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fs.apply(hashsalt='racing-structure')
    fs.save(render_figure(result), args.output, ('png', 'svg'))
    render_tables(result, args.output.parent)


if __name__ == '__main__':
    main()
