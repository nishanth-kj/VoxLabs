# 🚀 VoxLabs - Quick Start Guide

## Prerequisites

- **Python:** 3.12+
- **Node.js:** 20.0.0+
- **npm:** 10.0.0+

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/nishanth-kj/VoxLabs.git
cd VoxLabs
```

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env if needed
```

### 3. Install Dependencies

**Backend:**
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Frontend:**
```bash
npm install
```

## Running the Application

### Option 1: Development Mode

**Terminal 1 - Backend:**
```bash
python main.py
```
→ Backend running at http://localhost:8000  
→ API Docs at http://localhost:8000/docs

**Terminal 2 - Frontend:**
```bash
npm run dev
```
→ Frontend running at http://localhost:3000

### Option 2: Docker

```bash
docker-compose up -d
```

Access:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Usage

1. Open http://localhost:3000
2. Enter text in the textarea
3. Click "Generate Speech"
4. Listen to the generated audio

## Features

- ✅ Text-to-Speech (gTTS)
- ✅ Emotional TTS controls
- ✅ Voice cloning with consent
- ✅ Multi-language support
- ✅ Local-only processing

## Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
# Find and kill process
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9
```

### Frontend Issues

**Port 3000 already in use:**
```bash
# Change port in package.json
"dev": "next dev -p 3001"
```

**Module not found:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Next Steps

- Read [CONTRIBUTING.md](./CONTRIBUTING.md) to contribute
- Check [README.md](./README.md) for full documentation
- Explore API at http://localhost:8000/docs

## Support

- Issues: [GitHub Issues](https://github.com/nishanth-kj/VoxLabs/issues)
- Discussions: [GitHub Discussions](https://github.com/nishanth-kj/VoxLabs/discussions)

---

**Happy Voice Cloning!** 🎙️
