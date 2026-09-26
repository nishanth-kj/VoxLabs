# Voice cloning

Cloning lives in `CloneService` (`app/services/clone_service.py`), with `ConsentService` and `VoiceService`.

## Workflow

```text
samples → validate files → validate consent → select model
        → analyze + prepare samples (staging folder) → build profile
        → [one transaction: create voice → record consent → move samples in → store profile]
        → voice ready for TTS → preview
```

1. **Validate files** (`require_audio_file`): the file exists, is not empty, and has a supported extension (wav, mp3, flac, ogg, m4a, aac, opus).
2. **Consent** (`ConsentService.validate`): requires `confirmed is True`, plus `granted_by` and `speaker_name`. It runs *before* any file is processed, and nothing can skip it. The statement defaults to `CONSENT_STATEMENT` with the speaker's name filled in.
3. **Select model:** the `model_key` argument, or `default_clone_model` from Settings. It must be a CLONE or EMBED model and must be installed.
4. **Analyze** (`analyze_sample`): runs `AudioService.analyze`, then blocks on:
   - samples shorter than 1 s or longer than 5 min
   - sample rate under 16 kHz
   - more than 90% silence

   Other findings are warnings: clipping, noise, quiet level.
5. **Prepare** each sample: resample to 24 kHz, trim silence, peak-normalize to −1 dBFS, and write to a staging folder. Together the samples must provide at least 3 s of speech.
6. **Profile** (`build_profile`): the MFCC mean/std and the median pitch (pYIN) across samples.
7. **Transaction:** create the voice, record consent, move the samples into `data/voices/<voices_id>/samples/`, and store the profile.

Heavy work and progress reporting happen before the transaction, so it stays short. On any failure the rows roll back and both the staging and voice folders are deleted.

## How the voice is used for speech

| Cloning model | At generation time |
|---|---|
| XTTS v2, F5-TTS, Chatterbox | The backend receives the stored sample paths as reference audio (zero-shot cloning). `params.cloned = true`. |
| Voice profile (MFCC) | The voice speaks through the default TTS model. Its output pitch is shifted to match the speaker's median pitch (`params.pitch_matched = true`). This is an approximation, not a clone. |

## Lifecycle (VoiceService)

- **Rename or edit:** `update()` and `rename()`.
- **Add or remove samples:** `attach_sample()` (requires active consent) and `remove_sample()` (at least one sample must remain). Both rebuild the profile.
- **Revoke:** `revoke()` does four things:
  - deletes all sample files and the profile;
  - marks consent records Inactive and sets `revoked_at`;
  - sets `voices.status = Inactive` and `consent_status = Revoked`;
  - blocks the voice from generation (`voice_ref()` raises).

  The row itself stays as an audit trail.
- **Delete:** `delete()` removes the voice, its samples, its consent rows and its folder.
- **Export metadata:** `export_metadata()` returns voice fields, sample info without paths, and consent history.

## Preset voices

`VoiceService.create()` makes a *preset* voice: an engine's built-in speaker, such as an Edge voice id in `engine_voice`. Nobody is cloned, so `consent_status = NotRequired`.

## UI

The Clone Voice page walks through: samples (import or record) → analysis table → consent form → voice settings → Clone (background job) → Preview → Save.

The Voices page shows each voice's sample count, consent and status, with actions to preview, rename, edit, add a sample, revoke, delete and export.
