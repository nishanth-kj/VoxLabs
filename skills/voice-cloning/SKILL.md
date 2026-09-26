---
name: voice-cloning
description: Workflow and rules for VoxLabs voice cloning, consent, voice samples, revoke and delete.
---

# Voice cloning

## Purpose

Turn consented reference recordings into a reusable voice (a `voices` row, its `voice_samples`, and a `voice_consents` audit record).

## Workflow

1. `clone_service.analyze_sample(path)`: quality report. `errors` block cloning; `issues` are warnings.
2. `clone_service.clone(paths, name, consent, model_key=…)`:
   - validates the files;
   - calls `consent_service.validate(consent)` *before* any work;
   - `select_model()` must pick a CLONE or EMBED model that is installed;
   - `prepare_sample()` per file (24 kHz, trim, normalize) into a staging folder, then `build_profile()`. Both happen outside the transaction, because job progress writes the jobs table and must not happen while the transaction is open;
   - in one short transaction: `voice_service.create_in()`, then `consent_service.record()`, then move the samples in and store the profile.
3. `clone_service.preview(voices_id)` generates a sample through `tts_service` and stores `preview_audios_id`.
4. Lifecycle is in `voice_service`: `update`, `rename`, `attach_sample`, `remove_sample`, `revoke`, `delete`, `export_metadata`.

## Important rules

- Never add a parameter, flag or code path that clones without `ConsentService.validate` succeeding.
- Consent must be attributed (`granted_by`, `speaker_name`) and stored with a timestamp.
- `revoke()` must delete the sample files and profile immediately, set `status = Status.INACTIVE.code` and `consent_status = ConsentStatus.REVOKED.code`, and mark consents Inactive with `revoked_at`.
- `delete()` removes rows and folders completely.
- `voice_service.voice_ref()` must refuse voices without active consent.
- Store paths only, under `data/voices/<voices_id>/`. Do not log audio content.

## References

- `app/services/clone_service.py`, `consent_service.py`, `voice_service.py`
- `app/models/voice.py`, `voice_sample.py`, `voice_consent.py`
- `app/ui/pages/clone_page.py`, `voices_page.py`
- `docs/voice-cloning.md`

## Testing

`tests/test_voice_and_clone.py` covers:
- consent refusal
- rollback on short samples (no rows, no files)
- multiple samples
- revoke deleting files
- full delete

Use `make_voice_wav()` from `tests/conftest.py` for synthetic samples. For cloning backends, use the `fake-clone` model.
