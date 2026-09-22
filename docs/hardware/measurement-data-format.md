# Measurement node data format (E1/E2), schema_version 1

Newline-delimited JSON from `firmware/measurement_node/code.py`, read by `experiments/measurement_logger.py`.
Raw ADC counts only. There is no `force_N` anywhere in this format: newtons need an E3 calibration record
for a named cell, mount and configuration, and the device has none.

## Records

`session` — once per boot or reset (so a reset is visible as a new session ID and a sequence restart):

| field | meaning |
|---|---|
| `session_id` | CPU UID suffix + 4 random bytes, new every boot |
| `sensor_id`, `adc_id`, `mcu_id` | stable IDs from [purchased-instruments.json](purchased-instruments.json) |
| `config_id`, `config` | `g128-ldo3V0-10sps-ch1` and the dict it encodes (gain, LDO, poll rate, channel, internal calibration) |
| `firmware`, `chip_revision`, `internal_calibration_ok`, `init_error` | identity and boot outcome; `init_error` non-null means no sensor |
| `raw_units`, `full_scale_counts` | `adc_counts_24bit_signed`, 8388607 |
| `time_basis` | device `monotonic_ns` at register read after `available()` polled true; no hardware conversion timestamp |

`sample` — one per conversion: `seq` (0-based, per session), `t_ns`, `raw_counts` (int), `config_id`, `status` (`ok` | `saturated`).

`error` — same header, `status` (`read_error` | `missing_device`) and `detail`. Errors are records, not log noise.

## Host outputs (`measurement_logger.py`)

| file | content |
|---|---|
| `stream.jsonl` | input bytes unchanged |
| `samples.csv` | every sample and error record with `flags` (empty = clean) |
| `diagnostics.json` | flag counts and per-line entries |
| `manifest.json` | `source_kind`, source path and SHA-256, source commit, mode, `complete`, `truncated_reason`, sensor/config/firmware identity, `calibration_id: null`, counts, first/last `t_ns`, stream SHA-256 |
| `host_times.csv` | live capture only: line number → host receive ns (USB arrival, not the sampling instant) |

## Flags (retained with the record, never repaired)

`malformed_line`, `unknown_record_type`, `sample_before_session`, `session_id_mismatch`, `config_change`,
`invalid_header`, `duplicate_sequence` (same conversion identity twice = stale), `sequence_reversal`,
`sequence_gap:N`, `time_reversal`, `timing_gap:Xms` (> 3 nominal periods), `invalid_value` (non-integer,
NaN, inf; value blanked, row kept), `clipping` (|raw| ≥ full scale), `session_boundary`.
Identical consecutive counts are not a flag: only conversion identity and timing decide staleness.

## Evidence class

`source_kind` is `synthetic` for fixtures and anything replayed from them, `measured` only for a live
capture or a replay of a measured file whose SHA-256 matches `--measured-sha256`. Replay never upgrades
its input. A truncated capture (timeout, disconnect, interrupt, partial last line) is written with
`complete: false` and exit code 3 so it cannot pass as a full session.
