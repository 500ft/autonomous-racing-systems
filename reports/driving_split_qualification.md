# Driving split qualification

No final-test set was admitted. The published metadata leaves acquisition-session
and segment membership unresolved. The requested whole-run validation stopped at
this prerequisite, before another bag was acquired or parsed. The census,
per-file roles and execution counts are in
[result.json](../runs/driving_split_qualification/result.json).

## What was inspected

The [Zenodo record](https://zenodo.org/records/12536536) lists bag names, byte sizes
and published MD5 checksums. Its
[README](https://zenodo.org/records/12536536/files/ReadMe.md?download=1) describes
each bag as a continuous run. The linked
[upstream README](https://github.com/zhang-zengjie/dl-vehicle-model/blob/7d0fa15286d2bea830326427e225db550abd9190/README.md)
explains loading and model use. These sources do not supply acquisition-session
identifiers, parent-segment mappings, end times or documented changes in vehicle,
surface and configuration.

The filenames share a collection date and have different start labels. The
published whole-file checksums are distinct. Those observations identify files;
they do not establish that acquisition sessions are separate or that segments do
not overlap. Conversely, a common date does not prove one common session.

The conservative grouping is therefore unresolved. The previously inspected bag
retains its development role. All unopened files remain unassigned together.
Their payload SHA256 values are deliberately unknown; published MD5 checksums
are registered without downloading them. A session-separated final set cannot
be established from the inspected metadata. This is a provenance limitation,
not a measured failure of the longitudinal model.

## Executed procedure

[registration.json](../runs/driving_split_qualification/registration.json) records
the input URLs and hashes, analysis scope, source-review interpretation and code
hash. It was committed before the scripted census. Metadata had already been
read during prerequisite review; the registration does not claim human blinding.

[qualify_driving_split.py](../experiments/qualify_driving_split.py) verifies the
registered metadata snapshot, enumerates every bag, extracts filename fields,
groups exact published checksums and retains the prior exposure role. It records
the source-review decision explicitly. The code does not independently infer
session membership or prove the absence of undocumented sessions.

There was one source review and one registered census, with no model-fitting
iterations. The failed eligibility decision remains in the result. Longitudinal
training, lateral signal qualification, model selection, endpoint freezing and
final scoring were not executed. No lateral coefficients or qualification
failure are inferred from this earlier stop.

Data terms and attribution remain those of
[the original source record](../runs/real_command_response/source.json): CC BY
4.0 for the dataset, credited to Zengjie Zhang with Giannis Badakis and Michalis
Galanis at Eindhoven University of Technology. The repository code licence is
separate. No bag payload or private location trace is included in this result.

## Reproduce the metadata census

From the repository root, use the committed metadata snapshot. The live API can
change access statistics without changing its acquisition documentation.

```bash
python3 experiments/qualify_driving_split.py \
  --metadata runs/driving_split_qualification/zenodo-record.json \
  --output /tmp/racing-split-reproduction.json
```

The input hash must match the registered snapshot. The execution timestamp
changes on reproduction; all other result fields should match. The registration
retains the retrieval URL and source hash. A changed source requires a separately
reviewed snapshot, rather than silently replacing the evidence used here.

## What would change this conclusion

A source-backed mapping from each bag to its acquisition session and any parent
recording would permit grouping, including shared vehicle/surface/configuration
limits and any known overlap. If it establishes separate acquisition units, the
split and analysis choices can be registered before the unopened outcomes are
accessed. The [roadmap](../ROADMAP.md) holds that next step. This task does not
substitute filename families or arbitrary time boundaries for missing provenance.

Owner exercise: reproduce the frame rotation from the earlier development
result's `owner_frame_exercise`, then explain which source evidence would make
one unopened run eligible for a separate final group. The requested whole-run
held-out residual does not exist because this gate failed; it must wait for an
admitted split and frozen endpoints. Public-car transfer and the physical D2
mounting decision remain separate.
