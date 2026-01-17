# Contributing to VoxLabs

Thank you for your interest in contributing to VoxLabs! This document provides guidelines and instructions for contributing.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Making Changes](#making-changes)
- [Submitting Changes](#submitting-changes)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

---

## 🤝 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors.

### Our Standards

- ✅ Be respectful and inclusive
- ✅ Accept constructive criticism gracefully
- ✅ Focus on what's best for the community
- ✅ Show empathy towards others

### Unacceptable Behavior

- ❌ Harassment or discriminatory language
- ❌ Trolling or insulting comments
- ❌ Personal or political attacks
- ❌ Publishing others' private information

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** >= 20.0.0
- **Python** >= 3.12
- **uv** (for Python package management)
- **Git**
- **Docker** (optional, for containerized development)

### Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/nishanth-kj/VoxLabs.git
cd VoxLabs

# Add upstream remote
git remote add upstream https://github.com/nishanth-kj/VoxLabs.git
```

---

## 💻 Development Setup

### 1. Install Dependencies

**Frontend (Next.js):**
```bash
cd web
npm install
```

**Backend (FastAPI):**
```bash
# Install uv if you haven't already
pip install uv

cd api
# uv handles virtual environment and dependencies automatically when you run commands
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
```

### 3. Start Development

**Frontend:**
```bash
cd web
npm run dev
# → http://localhost:3000
```

**Backend:**
```bash
cd api
uv run uvicorn main:app --reload --port 8000
# → http://localhost:8000
```

---

## 📁 Project Structure

```
VoxLabs/
├── api/                        # FastAPI Backend
│   ├── engine/                # Voice Cloning & TTS Engine
│   ├── main.py                # App Entry Point
│   └── pyproject.toml         # Python Dependencies
├── web/                        # Next.js Frontend
│   ├── app/                   # App Router Pages
│   └── components/            # React Components
├── desktop/                    # Tauri Desktop App (Upcoming)
├── docs/                       # Documentation
└── docker-compose.yml          # Container Orchestration
```

---

## 🔧 Making Changes

### Create a Branch

```bash
# Update your fork
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/changes
- `chore/` - Maintenance tasks

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples:**
```bash
git commit -m "feat(api): add voice cloning endpoint"
git commit -m "fix(web): resolve audio playback issue"
```

---

## 📤 Submitting Changes

### Before Submitting

1. **Test your changes**
2. **Build successfully**
   ```bash
   # Web
   cd web && npm run build
   ```
3. **Update documentation** if needed

### Create Pull Request

1. Push your branch:
   ```bash
   git push origin feature/your-feature-name
   ```
2. Go to GitHub and create a Pull Request.
3. Our **PR Template** will automatically load. Please fill it out completely:
   - **Description**: Summary of changes
   - **Type of Change**: Bug fix, feature, etc.
   - **Related Issues**: Link to issues (e.g., `Closes #123`)
   - **Testing**: How you verified functionality

---

## 🐛 Reporting Bugs

Please use our **Bug Report Template** when opening a new issue.

1. Check existing issues to avoid duplicates.
2. Provide a clear description and steps to reproduce.
3. Include environment details (OS, Browser, etc.).

## 💡 Feature Requests

Please use our **Feature Request Template** to suggest new ideas.

---

## 📄 License

By contributing to VoxLabs, you agree that your contributions will be licensed under the MIT License.

---

## 📞 Questions?

- **Discussions**: [GitHub Discussions](https://github.com/nishanth-kj/VoxLabs/discussions)
- **Issues**: [GitHub Issues](https://github.com/nishanth-kj/VoxLabs/issues)

**Happy Coding!** 🚀
