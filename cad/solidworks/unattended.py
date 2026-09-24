"""Put SOLIDWORKS into an unattended state before authoring, and restore the host afterwards.

The host has no operator: no monitor, nobody to click a dialog. Any modal prompt is a hang, not a
question. `sw.Visible = False` hides the window but does **not** stop SOLIDWORKS asking for values.

The one that matters here is **"Input dimension value"** (Tools > Options > General). When it is on,
creating a dimension pops a modal Modify box waiting for a number. Every dimension this project
authors would raise one, so an unattended run blocks forever at the first dimension with no error and
no output. Disabling it makes SOLIDWORKS accept the value the API supplies, which is what the caller
already passes to `AddDimension2` — the dimension is not guessed, the confirmation click is removed.

STATUS: NOT HOST-VERIFIED. The toggle identifier below is cross-checked against three independent
sources, one of which read it out of `swconst.tlb` directly, but no run on this project's host has
confirmed it yet. That is why every toggle is **read back after writing** and the outcome recorded in
the result JSON: the first real run proves or disproves it instead of assuming. If `applied` comes
back false, the run journal says so and the operator can clear the option by hand once.

Scope limit, stated rather than implied: this disables the prompts named below and nothing else. It is
not a general "suppress every dialog" switch, and no such switch is claimed to exist. A dialog raised
by a licence problem, a missing template or a graphics failure will still block, and the runner's
polling timeout is what catches that.
"""
from __future__ import annotations

# swUserPreferenceToggle_e. Early binding is unavailable on this host (see the shared API findings),
# so enum values are numeric. 10 = swInputDimValOnCreate, verified against three independent sources.
SW_INPUT_DIM_VAL_ON_CREATE = 10

TOGGLES = (("input_dimension_value_on_create", SW_INPUT_DIM_VAL_ON_CREATE, False),)


def begin(sw):
    """Apply the unattended toggles. Returns (saved, journal).

    `saved` restores the host's own settings later; `journal` is evidence of what actually happened
    and belongs in the result file."""
    saved, journal = {}, {}
    for name, ident, target in TOGGLES:
        entry = {"preference_id": ident, "target": target}
        try:
            was = bool(sw.GetUserPreferenceToggle(ident))
            sw.SetUserPreferenceToggle(ident, target)
            now = bool(sw.GetUserPreferenceToggle(ident))
            saved[ident] = was
            entry.update(was=was, now=now, applied=(now == target))
            if now != target:
                entry["note"] = ("read-back does not match the target; an unattended run may block on "
                                 "a modal dimension box")
        except Exception as exc:                      # noqa: BLE001  a failure here must not be fatal
            entry.update(applied=False, error=repr(exc),
                         note="could not set the preference; if the run hangs at the first dimension, "
                              "clear Tools > Options > General > 'Input dimension value' on the host")
        journal[name] = entry
    return saved, journal


def end(sw, saved):
    """Restore the host's original settings. Never raises: teardown must not mask a real result."""
    restored = {}
    for ident, was in (saved or {}).items():
        try:
            sw.SetUserPreferenceToggle(ident, was)
            restored[ident] = bool(sw.GetUserPreferenceToggle(ident)) == was
        except Exception:                             # noqa: BLE001
            restored[ident] = False
    return restored
