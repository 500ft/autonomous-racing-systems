# Measurement node: QT Py RP2040 + NAU7802 + one load cell. CircuitPython.
# STATUS: NOT DEVICE-TESTED. Written against cedargrove_nau7802 2.1.4 (see library-versions.txt);
# attribute names must be confirmed on the first flash before any record is called measured.
#
# Emits newline-delimited JSON on the USB serial console: one "session" record at boot, then one
# "sample" or "error" record per NAU7802 conversion. Nothing else is printed. Raw counts only:
# conversion to newtons is a host task (E3) and needs a calibration record this device does not have.
import json
import os
import time

import board
import microcontroller

FIRMWARE = {"name": "measurement_node", "version": "0.1.0-untested"}
SCHEMA_VERSION = 1
SENSOR_ID = "LC-5KG-01"        # from docs/hardware/purchased-instruments.json
ADC_ID = "ADC-NAU7802-01"
MCU_ID = "MCU-QTPY-01"
CONFIG = {"gain": 128, "ldo_voltage": "3V0", "poll_rate_sps": 10, "channel": 1, "internal_calibration": True}
CONFIG_ID = "g%d-ldo%s-%dsps-ch%d" % (CONFIG["gain"], CONFIG["ldo_voltage"], CONFIG["poll_rate_sps"], CONFIG["channel"])
FULL_SCALE = (1 << 23) - 1     # 24-bit signed output; |raw| at this value is saturation, not a measurement
REINIT_AFTER_ERRORS = 5

uid = "".join("%02x" % b for b in microcontroller.cpu.uid)[-8:]
session_id = uid + "-" + "".join("%02x" % b for b in os.urandom(4))   # new on every boot/reset
seq = 0


def emit(rec):
    print(json.dumps(rec))


def stamp(rec, status):
    global seq
    rec["type"] = rec.get("type", "sample")
    rec["schema_version"] = SCHEMA_VERSION
    rec["session_id"] = session_id
    rec["seq"] = seq
    rec["t_ns"] = time.monotonic_ns()   # device monotonic at register read; there is no hardware timestamp
    rec["config_id"] = CONFIG_ID
    rec["status"] = status
    seq += 1
    return rec


def init_sensor():
    from cedargrove_nau7802 import NAU7802
    nau = NAU7802(board.STEMMA_I2C(), address=0x2A, active_channels=1)   # STEMMA connector, not the header bus
    nau.gain = CONFIG["gain"]
    nau.ldo_voltage = CONFIG["ldo_voltage"]
    nau.poll_rate = CONFIG["poll_rate_sps"]
    nau.channel = CONFIG["channel"]
    nau.enable(True)
    calibrated = nau.calibrate("INTERNAL") if CONFIG["internal_calibration"] else None
    return nau, calibrated


nau = None
chip_rev = None
cal_ok = None
try:
    nau, cal_ok = init_sensor()
    chip_rev = nau.chip_revision
except Exception as e:  # missing board, wrong bus, library mismatch
    init_error = repr(e)
else:
    init_error = None

emit({
    "type": "session", "schema_version": SCHEMA_VERSION, "session_id": session_id,
    "sensor_id": SENSOR_ID, "adc_id": ADC_ID, "mcu_id": MCU_ID,
    "config_id": CONFIG_ID, "config": CONFIG, "firmware": FIRMWARE,
    "chip_revision": chip_rev, "internal_calibration_ok": cal_ok, "init_error": init_error,
    "raw_units": "adc_counts_24bit_signed", "full_scale_counts": FULL_SCALE,
    "time_basis": "device monotonic_ns at register read after available() polled true; no hardware conversion timestamp",
    "t_ns": time.monotonic_ns(),
})

errors = 0
while True:
    if nau is None:
        emit(stamp({"type": "error", "detail": init_error}, "missing_device"))
        time.sleep(1.0)
        try:
            nau, cal_ok = init_sensor()
            errors = 0
        except Exception as e:
            init_error = repr(e)
        continue
    try:
        if not nau.available():
            time.sleep(0.002)
            continue
        raw = nau.read()   # read each conversion once; no tare, no averaging, no unit conversion
        errors = 0
        emit(stamp({"raw_counts": raw}, "saturated" if abs(raw) >= FULL_SCALE else "ok"))
    except Exception as e:
        errors += 1
        emit(stamp({"type": "error", "detail": repr(e)}, "read_error"))
        if errors >= REINIT_AFTER_ERRORS:
            nau, init_error = None, repr(e)
