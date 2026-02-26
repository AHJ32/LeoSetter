# Contributing to LeoSetter

Thank you for considering contributing to LeoSetter! This document outlines how to report bugs, request features, and submit code changes.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Reporting Bugs](#reporting-bugs)
- [Requesting Features](#requesting-features)
- [Contributing Code](#contributing-code)
- [Development Setup](#development-setup)
- [Pull Request Guidelines](#pull-request-guidelines)

---

## Code of Conduct

Please be respectful and constructive. We aim to keep this a welcoming project for everyone.

---

## 🐛 Reporting Bugs

1. **Search first** — Check [existing issues](https://github.com/AHJ32/LeoSetter/issues) to see if the bug has already been reported.
2. **Open a Bug Report** — Click [New Issue → Bug Report](https://github.com/AHJ32/LeoSetter/issues/new?template=bug_report.md) and fill in the template completely, including:
   - Your OS and Python version
   - Steps to reproduce the bug
   - What you expected vs. what actually happened
   - Any relevant error messages or screenshots

---

## 💡 Requesting Features

Have an idea for a new feature or improvement? Here's how to request it:

1. **Search first** — Check [existing issues](https://github.com/AHJ32/LeoSetter/issues?q=is%3Aissue+label%3Aenhancement) to avoid duplicates.
2. **Open a Feature Request** — Click [New Issue → Feature Request](https://github.com/AHJ32/LeoSetter/issues/new?template=feature_request.md) and describe:
   - **What** the feature does
   - **Why** it would be useful (use case)
   - **How** you imagine it working (optional, but helpful)
3. **Discuss** — Wait for a maintainer to review and label your request. Features marked `accepted` are open for implementation.

> **Tip:** A well-described feature request with a clear use case is much more likely to be accepted quickly.

---

## 🛠️ Contributing Code

### 1. Fork & Branch

Fork the repo and create a descriptive branch:

```bash
git checkout -b 42-add-batch-rename
```

Branch names should follow the pattern `<issue-number>-<short-description>`.

### 2. Development Setup

**Windows:**
```powershell
git clone https://github.com/YOUR_USERNAME/LeoSetter.git
cd LeoSetter
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

**Linux:**
```bash
git clone https://github.com/YOUR_USERNAME/LeoSetter.git
cd LeoSetter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 run.py
```

Also install `exiftool` on your system:
- **Windows:** Download from [exiftool.org](https://exiftool.org/)
- **Linux:** `sudo apt-get install exiftool`

### 3. Make Your Changes

- Keep code changes focused — one feature or bug fix per PR
- Follow the existing code style (CustomTkinter widgets, type hints, helper patterns)
- Update `requirements.txt` if you add new dependencies
- Test your changes by running the application manually

### 4. Sync With Upstream

Before opening a PR, sync your fork with the latest `main`:

```bash
git remote add upstream https://github.com/AHJ32/LeoSetter.git
git fetch upstream
git rebase upstream/main
```

---

## Pull Request Guidelines

- Link the related issue in your PR description (e.g., `Closes #42`)
- Fill in the [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md)
- Keep PRs small and focused — large PRs are harder to review
- Screenshots or screen recordings are appreciated for UI changes
- A maintainer will review your PR, request changes if needed, and merge once it's ready

---

*Thank you for helping make LeoSetter better! 🙏*
