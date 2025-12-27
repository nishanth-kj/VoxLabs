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

- **Node.js** >= 18.0.0
- **Python** >= 3.10
- **Rust** >= 1.70 (for Tauri)
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

### Install Dependencies

```bash
# Install all workspace dependencies
npm install

# Install Python dependencies
cd packages/backend
pip install -r requirements.txt
pip install -e ".[dev]"  # Install with dev dependencies

# Install Rust (if building desktop/mobile)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
```

### Start Development

```bash
# Start all services (Turbo)
npm run dev

# Or start individual packages
cd packages/backend && python -m uvicorn main:app --reload
cd packages/frontend && npm run dev
cd packages/desktop && cargo tauri dev
```

---

## 📁 Project Structure

```
VoxLabs/                        # Monorepo root
├── packages/                   # All packages
│   ├── backend/               # Python/FastAPI
│   ├── frontend/              # TypeScript/Next.js
│   ├── desktop/               # Rust/Tauri
│   ├── mobile/                # Rust/Tauri Mobile
│   ├── shared/                # Shared TypeScript
│   ├── voxlabs-client/        # npm library
│   └── voxlabs-python/        # PyPI library
├── docker/                    # Docker configs
├── docs/                      # Documentation
└── tools/                     # Build scripts
```

See [`.agent/STRUCTURE.md`](./.agent/STRUCTURE.md) for detailed structure.

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

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Tests
- `chore`: Maintenance

**Examples:**

```bash
git commit -m "feat(backend): add voice cloning endpoint"
git commit -m "fix(frontend): resolve audio playback issue"
git commit -m "docs(readme): update installation instructions"
```

---

## 📤 Submitting Changes

### Before Submitting

1. **Test your changes**
   ```bash
   npm run test
   npm run lint
   ```

2. **Build successfully**
   ```bash
   npm run build
   ```

3. **Update documentation** if needed

4. **Add tests** for new features

### Create Pull Request

1. Push your branch
   ```bash
   git push origin feature/your-feature-name
   ```

2. Go to GitHub and create a Pull Request

3. Fill out the PR template:
   - **Description**: What does this PR do?
   - **Related Issues**: Link to issues
   - **Testing**: How was it tested?
   - **Screenshots**: If UI changes

4. Wait for review

### PR Review Process

- Maintainers will review your PR
- Address any feedback
- Once approved, it will be merged

---

## 📏 Coding Standards

### TypeScript

```typescript
// Use TypeScript strict mode
// Use meaningful variable names
// Add JSDoc comments for public APIs

/**
 * Synthesize speech from text
 * @param text - Text to convert
 * @param options - Synthesis options
 * @returns Audio data
 */
export async function synthesize(
  text: string,
  options: SynthesisOptions
): Promise<AudioData> {
  // Implementation
}
```

### Python

```python
# Follow PEP 8
# Use type hints
# Add docstrings

def synthesize(
    text: str,
    speed: float = 1.0,
    pitch: float = 1.0
) -> bytes:
    """
    Synthesize speech from text.

    Args:
        text: Text to convert to speech
        speed: Speaking speed (0.5 - 2.0)
        pitch: Voice pitch (0.5 - 1.5)

    Returns:
        Audio data as bytes
    """
    # Implementation
```

### Rust

```rust
// Follow Rust conventions
// Use rustfmt
// Add documentation comments

/// Synthesize speech from text
///
/// # Arguments
///
/// * `text` - Text to convert
/// * `options` - Synthesis options
///
/// # Returns
///
/// Audio data as bytes
pub fn synthesize(text: &str, options: SynthOptions) -> Vec<u8> {
    // Implementation
}
```

### Formatting

```bash
# TypeScript/JavaScript
npm run format

# Python
black packages/backend
ruff check packages/backend

# Rust
cargo fmt
```

---

## 🧪 Testing

### TypeScript

```bash
cd packages/frontend
npm run test
npm run test:coverage
```

### Python

```bash
cd packages/backend
pytest
pytest --cov=src tests/
```

### Rust

```bash
cd packages/desktop
cargo test
```

### Integration Tests

```bash
# Run all tests
npm run test
```

---

## 📚 Documentation

### Code Documentation

- Add JSDoc/docstrings for all public APIs
- Include examples in documentation
- Keep README files updated

### User Documentation

- Update `docs/` for user-facing changes
- Add screenshots for UI changes
- Update API documentation

### Changelog

- Update `CHANGELOG.md` for notable changes
- Follow [Keep a Changelog](https://keepachangelog.com/) format

---

## 🐛 Reporting Bugs

### Before Reporting

1. Check existing issues
2. Try latest version
3. Gather information:
   - OS and version
   - Node.js/Python/Rust version
   - Steps to reproduce
   - Expected vs actual behavior

### Bug Report Template

```markdown
**Describe the bug**
A clear description of the bug.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment**
- OS: [e.g., Windows 11]
- Node.js: [e.g., 18.0.0]
- Python: [e.g., 3.10]
- Browser: [e.g., Chrome 120]

**Additional context**
Any other relevant information.
```

---

## 💡 Feature Requests

### Before Requesting

1. Check existing feature requests
2. Ensure it aligns with project goals
3. Consider if it could be a plugin/extension

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
What you want to happen.

**Describe alternatives you've considered**
Other solutions you've thought about.

**Additional context**
Any other relevant information.
```

---

## 🔒 Security

### Reporting Security Issues

**DO NOT** open public issues for security vulnerabilities.

Instead:
1. Email: security@voxlabs.com (or GitHub private reporting)
2. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

---

## 📄 License

By contributing to VoxLabs, you agree that your contributions will be licensed under the MIT License.

---

## 🙏 Recognition

Contributors will be recognized in:
- `CONTRIBUTORS.md`
- Release notes
- Project README

---

## 📞 Questions?

- **Discussions**: [GitHub Discussions](https://github.com/nishanth-kj/VoxLabs/discussions)
- **Chat**: [Discord/Slack link]
- **Email**: contact@voxlabs.com

---

## 🎉 Thank You!

Thank you for contributing to VoxLabs! Your efforts help make voice technology more accessible and ethical.

**Happy Coding!** 🚀
