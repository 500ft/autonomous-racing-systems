# measurement_node — QT Py RP2040 + NAU7802 + one load cell (E1)

**Status: NOT DEVICE-TESTED.** `code.py` has been syntax-checked with `python -m py_compile` on the
host only. That checks Python syntax, not CircuitPython drivers, USB behaviour or a sensor.

## What it does

One NAU7802 channel, 10 samples/s, gain 128, LDO 3.0 V, internal calibration at boot, STEMMA QT bus
(`board.STEMMA_I2C()`, not the header bus). Emits newline-delimited JSON on the USB serial console:
one `session` record at boot, then a `sample` or `error` record per conversion. No banners, no tare,
no averaging, no newtons. Format: [docs/hardware/measurement-data-format.md](../../docs/hardware/measurement-data-format.md).

The session ID is new on every boot or reset (CPU UID suffix + 4 random bytes), so a reset shows up in
the host stream as a new `session` record and a sequence restart. Timestamps are device `monotonic_ns`
taken at register read after `available()` polled true; the NAU7802 has no hardware timestamp, so the
conversion instant is bounded by the poll interval, not known.

Saturation: `|raw_counts| >= 8388607` is reported with `status: saturated`. Read errors are emitted as
`error` records; after five in a row the node re-initialises the sensor and reports `missing_device`
once a second until it returns.

## Conditional human steps (owner, not scheduled)

1. Flash CircuitPython 10.3.x to the QT Py RP2040; copy `cedargrove_nau7802` and its bundle deps
   (`adafruit_bus_device`, `adafruit_register`) to `CIRCUITPY/lib`; copy `code.py`.
2. Fill `library-versions.txt` "observed" column from `boot_out.txt` and the bundle used.
3. First check: bus scan shows `0x2A` (a scan hit is not an operation check). Confirm the driver's
   attribute names (`gain`, `ldo_voltage`, `poll_rate`, `channel`, `available`, `read`, `calibrate`)
   match the installed version; fix `code.py` if the pinned API moved.
4. Capture a 60 s unloaded run with the host logger:
   `python experiments/measurement_logger.py --port <serial device> --seconds 60 --output <dir> --source-kind measured`
   Record actual record rate, timing gaps, zero drift, configuration and reset behaviour from
   `diagnostics.json`. That moves `ADC-NAU7802-01` and the cell to `operation_demonstrated`, nothing more.

Nothing here loads the mast, calibrates the cell, or produces a force in newtons.
