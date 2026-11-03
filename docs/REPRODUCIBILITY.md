# Reproducing the baseline

1. Use Python 3.11 or 3.12 and install the exact versions in `requirements.txt`, preferably in a virtual environment.
2. Run `python run_pipeline.py`. Each source response is atomically cached with its URL, UTC access time, byte count and SHA256. A cached response is reused only if the URL and hash match.
3. The 26 annual USGS batches are independently reconciled to the saved count receipt after applying the half-open global window and deduplicating IDs. A batch with 20,000 rows or a count mismatch stops the run rather than silently accepting truncation or catalogue drift.
4. The cleaned dataset and computed distances are bound to `config.json`, `data/sources.lock.json`, and the hashes of the cleaning, geometry and preparation modules. A matching processed-data hash is required for reuse.
5. `python run_pipeline.py --offline` validates local source hashes and rebuilds tables, figures, the dashboard and report without networking. It reuses distances only when the processing seal matches.
6. Run `python verify_results.py` and `python -m pytest -q`. The independent verifier does not call the pipeline's cleaning, distance or case-selection implementations.

`outputs/artifact_manifest.json` hashes generated tables, figures and the HTML deliverables. `outputs/verification.json` records independent checks; `outputs/browser_verification.json` records optional rendered/browser checks. The source-lock file is versioned, while generated output, raw data, the input DOCX and environments are excluded from the public repository.

## Exact snapshot versus a new download

The saved source manifest describes this local snapshot. Since USGS is a mutable catalogue, an empty-cache download at a later date can legitimately produce different source bytes or counts. The downloader writes a new local manifest for that new extraction; review the manifest diff and repeat all checks before treating it as a new result. Do not describe a new download as byte-identical to the delivered snapshot without comparing its hashes. Retain the old folder if comparing different snapshots.

Changing the study period or region configuration is possible, but predefined case dates must remain inside the observation interval. The figures/report and browser baseline checks are designed for this supplied 2000–2025 proposal; substantial scope changes require corresponding updates. In particular, the current report's introductory wording and fixed case-study descriptions are not a generic reporting framework for arbitrary intervals.

## Publication boundary

The public repository contains original code, tests, documentation, configuration, source receipts, a summary snapshot and one UI preview. It does not publish the input Word document, personal identifiers from it, credentials, environments or bulk event records. Data can be retrieved from the cited upstream sources without authentication. The preview and summary contain only public-source descriptive information.

The 3 November extension explicitly publishes the user-requested aggregate results in `docs/temporal_regional_v2`: nine new figures, fourteen aggregate tables/JSON, the report and an offline aggregate-only comparison tool. Event-level inputs and the anchor-level window audit stay local. See `docs/TEMPORAL_ANALYSIS.md` for the extension's strict read-only snapshot validation and preservation checks.
