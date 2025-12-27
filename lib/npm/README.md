# @voxlabs/client

Client-side voice synthesis and cloning library for npm.

## Installation

```bash
npm install @voxlabs/client
```

## Usage

```typescript
import { VoiceSynthesizer } from '@voxlabs/client';

const synth = new VoiceSynthesizer();
await synth.synthesize({ text: 'Hello world' });
```

## Features

- Client-side TTS
- Voice cloning
- Audio processing
- Local storage

## License

MIT
