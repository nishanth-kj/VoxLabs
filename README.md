# 🎙️ VoxLabs

**Professional AI Voice Cloning Platform**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![Node.js 20+](https://img.shields.io/badge/Node.js-20+-green.svg)](https://nodejs.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](./docker-compose.yml)

> Ethical voice cloning with consent. Local-first processing. Multi-platform support.

---

## 📚 Documentation

Detailed documentation is available in the [`docs/`](./docs) directory:

- [**Project Overview**](./docs/README.md)
- [**Backend Guide**](./docs/backend.md) (Architecture, Audio Engine)
- [**API Reference**](./docs/api.md) (Endpoints, JSON formats)
- [**Frontend Guide**](./docs/frontend.md) (Studio UI, State Management)
- [**Setup & Deployment**](./docs/setup.md) (Local Dev, Docker)

---

## ✨ Features

- 🎤 **Voice Cloning** - Clone voices with explicit consent
- 🎭 **Emotional TTS** - Control speed, pitch, and energy
- 🔒 **100% Local** - No data uploads, complete privacy
- 🌍 **Multi-Language** - Support for 100+ languages
- 📱 **Multi-Platform** - Web, Desktop, Mobile
- ⚡ **Modern Stack** - FastAPI + Next.js + Tauri

---

## 🚀 Quick Start

For detailed setup instructions, see [Setup Guide](./docs/setup.md).

### Docker (Recommended) ⭐

```bash
docker-compose up -d --build
```

Access:
- 🌐 Frontend: `http://localhost:3000`
- 📚 API Docs: `http://localhost:8000/docs`

### C++ Core (Native & WebAssembly) 🚀

The new high-performance C++ core handles voice decloning and emotion control.

#### Standard Native Build
To build natively, we use a local installation of `vcpkg` for dependency management:

```bash
cd core

# 1. Clone and bootstrap vcpkg locally
git clone https://github.com/microsoft/vcpkg.git
# On Windows:
.\vcpkg\bootstrap-vcpkg.bat
# On Linux/macOS:
# ./vcpkg/bootstrap-vcpkg.sh

# 2. Build the project using the local toolchain
mkdir build && cd build
cmake -DCMAKE_TOOLCHAIN_FILE=../vcpkg/scripts/buildsystems/vcpkg.cmake ..
make
```

#### WebAssembly Build
To compile the C++ core to WebAssembly, you need [Emscripten](https://emscripten.org/) installed:

```bash
cd core
mkdir build && cd build
emcmake cmake ..
make
```

---

## 📁 Project Structure

```
VoxLabs/
├── core/                     # C++ Core (Voice Decloning & Emotion)
├── api/                      # FastAPI Backend
│   ├── main.py               # Entry point
│   ├── engine/               # Audio processing logic
│   └── static/               # Generated audio files
├── web/                      # Next.js Frontend
│   ├── app/                  # App Router pages
│   └── lib/                  # API client & types
├── desktop/                  # Tauri Desktop App config
├── docs/                     # Project Documentation
├── docker-compose.yml        # Orchestration
└── README.md                 # This file
```

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Python web framework
- **Librosa** - DSP & Audio analysis
- **SoundFile** - Audio I/O
- **Pydantic** - Data validation

### Frontend
- **Next.js 16** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Shadcn UI** - Components
- **Framer Motion / GSAP** - Animations

### DevOps & Desktop
- **Docker** - Containerization
- **Tauri** - Desktop application bundle

---

## 🔐 Safety & Ethics

VoxLabs is built with ethical AI practices at its core:

✅ **Consent Required** - Explicit consent for all voice cloning operations  
✅ **Local Storage** - No data uploads to external servers  
✅ **AI Labels** - All generated audio labeled as AI-generated  
✅ **Easy Deletion** - Simple voice data revocation  
✅ **Transparent** - Open source and fully auditable  
✅ **No Impersonation** - Designed to prevent malicious use  

---

## 🎯 Use Cases

- **Accessibility** - Text-to-speech for visually impaired users
- **Content Creation** - Voiceovers for videos and podcasts
- **Language Learning** - Practice pronunciation with native voices
- **Personal Assistants** - Custom voice for smart home devices
- **Game Development** - Character voices for indie games

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for:

- Code of conduct
- Development setup
- Coding standards
- Pull request process
- Testing guidelines

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

**Important Disclaimer:** Users are responsible for obtaining proper consent before cloning any voice and must comply with all applicable laws and regulations.

---

## 🎯 Roadmap

- [x] FastAPI backend with voice cloning
- [x] Next.js frontend with modern UI
- [x] Docker deployment setup
- [x] Emotional TTS controls
- [x] Multi-language support
- [ ] Desktop app (Tauri)
- [ ] Mobile app (Tauri Mobile)
- [ ] npm package (`@voxlabs/client`)
- [ ] PyPI package (`voxlabs`)
- [ ] Cloud deployment guides

---

## 📞 Support & Contact

- **Author**: nishanth-kj
- **GitHub**: [@nishanth-kj](https://github.com/nishanth-kj)
- **Issues**: [GitHub Issues](https://github.com/nishanth-kj/VoxLabs/issues)
- **Discussions**: [GitHub Discussions](https://github.com/nishanth-kj/VoxLabs/discussions)

---

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Next.js team for the React framework
- Open source community for amazing tools
- Contributors and supporters

---

<div align="center">

**Made with ❤️ for ethical AI voice technology**

[Report Bug](https://github.com/nishanth-kj/VoxLabs/issues) • [Request Feature](https://github.com/nishanth-kj/VoxLabs/issues) • [Documentation](./CONTRIBUTING.md)

⭐ **Star this repo if you find it useful!** ⭐

</div>
