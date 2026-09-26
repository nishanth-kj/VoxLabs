# Privacy

VoxLabs is a desktop application that processes everything on your computer by default.

## What VoxLabs stores

All of the following is kept locally under `data/` (or `VOXLABS_DATA_DIR`):

- your scripts and generated or imported audio;
- voice samples and voice profiles;
- consent records (who granted consent, for whom, and when);
- job history, settings and logs. Logs never contain audio content or API tokens.

## What leaves your machine

- **Nothing, by default.**
- **Online engines.** If you enable them in Settings and choose Google (gTTS) or Microsoft Edge voices, the text you synthesize is sent to that provider. Voice samples are never uploaded.
- **Model downloads.** Installing a model downloads its weights (for example from Hugging Face). No user data is sent.

## Your control

- Revoke a voice to delete its samples and profile immediately. Delete it to remove every record.
- Delete projects or audio to remove their files.
- Delete the `data/` folder to erase everything.
