# 🎙️ VoxLabs

**Professional AI Voice Cloning Platform**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![Node.js 20+](https://img.shields.io/badge/Node.js-20+-green.svg)](https://nodejs.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](./docker-compose.yml)

> Ethical voice cloning with consent. Local-first processing. Multi-platform support.

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

### Option 1: Docker (Recommended) ⭐

**Windows:**
```bash
# Double-click start-docker.bat
# OR run in terminal:
docker-compose up -d --build
```

**Linux/Mac:**
```bash
docker-compose up -d --build
```

**Access:**
- 🌐 Frontend: http://localhost (port 80)
- 📚 API Docs: http://localhost/docs
- 🔧 API Status: http://localhost/api/status

**Stop:**
```bash
docker-compose down
```

📖 **Full Docker Guide:** See [DOCKER_GUIDE.md](./DOCKER_GUIDE.md)

### Option 2: Local Development

**Backend (FastAPI)**
```bash
# Install dependencies
pip install -r requirements.txt

# Start server
python main.py

# → http://localhost:8000
```

**Frontend (Next.js)**
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# → http://localhost:3000
```

---

## 📋 Requirements

- **Python:** 3.12 or higher
- **Node.js:** 20.0.0 or higher
- **Docker:** Latest (optional, for containerized deployment)

---

## 📁 Project Structure

```
VoxLabs/
├── main.py                   # FastAPI backend entry point
├── voice_engine.py           # Voice cloning engine
├── requirements.txt          # Python dependencies
├── pyproject.toml            # Python project configuration
│
├── app/                      # Next.js pages (App Router)
├── components/               # React components
├── next.config.js            # Next.js configuration
├── package.json              # Node.js dependencies
│
├── Dockerfile.backend        # Backend Docker image
├── Dockerfile.frontend       # Frontend Docker image
├── docker-compose.yml        # Multi-container orchestration
├── nginx.conf                # Nginx reverse proxy config
│
├── .env.example              # Environment variables template
├── README.md                 # This file
├── CONTRIBUTING.md           # Contribution guidelines
└── LICENSE                   # MIT License
```

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **librosa** - Audio feature extraction
- **pydub** - Audio manipulation
- **gTTS** - Google Text-to-Speech
- **NumPy/SciPy** - Scientific computing

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **React 18** - UI library
- **Sass** - CSS preprocessor

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Reverse proxy and load balancer

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
