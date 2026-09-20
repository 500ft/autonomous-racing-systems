# Measurement electronics — purchased inventory and first hookup (E0)

Status: **PURCHASE IDENTIFIED** only. The machine-readable inventory is
[purchased-instruments.json](purchased-instruments.json); every board and cell has a stable local ID
used by the E1–E3 tooling. No device has been connected, no revision observed, no calibration performed.
The owner register `cad/roboracer/parameters.csv` and its six pending rows are not touched by anything here.

## Evidence ladder for each instrument

| state | what it needs | what it does not claim |
|---|---|---|
| purchase_identified | product, quantity, purchase source | that it works |
| operation_demonstrated | unit/revision, wiring, firmware identity, a raw check session | calibration |
| calibrated_for_intended_use | references with uncertainty, range, mounting, configuration, review | campaign readiness |
| campaign_ready | the full [campaign-readiness](../specs/mast-physical-validation/campaign-readiness.md) checklist | — |

A manufacturer conformity sheet is paperwork about the product line, not a force calibration of this cell in this mount.

## What the purchase does and does not change

- A prospective **force** chain now has named parts: MCU-QTPY-01 → ADC-NAU7802-01 → LC-5KG-01.
- **5 kg cell for the 4–20 N profile.** 49.05 N nominal capacity, ratio 2.45 at 20 N before tare. The 1 kg cell (9.81 N) cannot reach 12/16/20 N and is never substituted into the campaign profile.
- **One ADC, one cable:** one cell at a time, one board at a time. Two simultaneous force channels are not established.
- **Not purchased:** calibrated tip and root displacement indicators (≤ 0.001 mm), a root-rotation observation, a fixture, and reference masses. The nominal FEA predicts about 0.0273 mm at 20 N; the accelerometer cannot recover that by double integration. These remain the largest physical gaps.
- **Not a modal channel:** NAU7802 tops out at 320 samples/s (160 Hz Nyquist) against a 285.5 Hz nominal first mode. The LIS3DH's bandwidth is mode dependent (672 Hz normal, ~149 Hz high-resolution at 1.344 kHz ODR); any vibration result stays exploratory.
- **Design loads are not test instructions:** 128.76 N crash load exceeds both cells; 50 g exceeds the LIS3DH ±16 g range.

## First hookup (draft, one board at a time, 3.3 V logic)

Hookup 1, the only one needed for E1–E3: QT Py RP2040 + NAU7802 + 5 kg cell.

```
QT Py STEMMA QT  ──(CBL-STEMMA-01)──  NAU7802 STEMMA QT      I2C on board.STEMMA_I2C()
NAU7802 E+ / E- / A+ / A-             ← LC-5KG-01 four wires (excitation pair, signal pair)
QT Py USB-C                           ← host (data cable, not charge-only)
```

Before wiring, record in the inventory JSON: observed I2C address from a bus scan (expected 0x2A per
the Adafruit guide; a scan hit is not an operation check), the NAU7802 revision (Rev C exposes B+/B-),
the cell's actual wire colours against the vendor page, and the intended load direction of the
bending-beam cell. Adafruit publishes a typical colour map for these cells; verify it on the unit,
do not copy it.

Sequential checks for the other boards (E4–E6, stretch) reuse the same cable one board at a time.

## Unconfirmed prerequisites

USB-C data cable; headers or terminal blocks on the NAU7802 for the cell leads; a two-plate mount for the
bending-beam cell; reference masses with stated uncertainty; an operator and bench. Jumper packs alone do
not make an assembled circuit.

## Conditional owner check (not scheduled, not required for the software deliverable)

If the boards are connected: a 60 s unloaded run recording actual record rate, timing gaps, zero drift,
configuration and reset behaviour, saved as an E2 session with `source_kind=measured`. This moves
ADC-NAU7802-01 and LC-5KG-01 to `operation_demonstrated`, nothing further.

## Sources

QT Py pinouts and STEMMA bus: <https://learn.adafruit.com/adafruit-qt-py-2040/pinouts> ·
NAU7802 revisions and wiring: <https://learn.adafruit.com/adafruit-nau7802-24-bit-adc-stemma-qt-qwiic/pinouts> ·
5 kg cell: <https://www.adafruit.com/product/4541> · 1 kg cell: <https://www.adafruit.com/product/4540> ·
LIS3DH datasheet (Tables 10, 31): <https://www.st.com/resource/en/datasheet/lis3dh.pdf>
