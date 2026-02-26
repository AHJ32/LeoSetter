# Contributing to LeoSetter

Thank you for considering contributing to LeoSetter! Every contribution matters — whether it is a bug report, a feature suggestion, a documentation fix, or a full pull request.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Reporting Bugs](#-reporting-bugs)
- [Requesting Features](#-requesting-features)
- [Contributing Code](#-contributing-code)
  - [Fork & Branch](#1-fork--branch)
  - [Development Setup](#2-development-setup)
  - [Making Changes](#3-make-your-changes)
  - [Sync with Upstream](#4-sync-with-upstream)
- [Pull Request Guidelines](#pull-request-guidelines)

---

## Code of Conduct

Please be respectful and constructive in all interactions. We aim to keep LeoSetter a welcoming space for contributors of all skill levels.

---

## 🐛 Reporting Bugs

1. **Search first** — Check [existing issues](https://github.com/AHJ32/LeoSetter/issues) to see if the bug has already been reported.
2. **Open a Bug Report** — Click [New Issue → Bug Report](https://github.com/AHJ32/LeoSetter/issues/new?template=bug_report.md) and fill in the template completely:
   - Your OS and Python version (or installer version if using the EXE)
   - Exact steps to reproduce the bug
   - What you expected vs. what actually happened
   - Any error messages or screenshots

Good bug reports get fixed faster. Be as specific as possible.

---

## 💡 Requesting Features

Have an idea for a new feature or improvement? Follow the step-by-step process described in:

> **[docs/FEATURE_REQUEST.md](docs/FEATURE_REQUEST.md)**

That page covers how to write a great feature request, what information to include, and what happens after you submit one.

---

## 🛠️ Contributing Code

### 1. Fork & Branch

Fork the repository on GitHub, then create a descriptive branch from `main`:

```bash
git checkout -b 42-add-batch-rename
```

Branch names should follow the pattern `<issue-number>-<short-description>`.

---

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

Also install ExifTool on your system:

- **Windows:** Download from [exiftool.org](https://exiftool.org/), rename to `exiftool.exe`, and place it on your `PATH`
- **Linux:** `sudo apt-get install libimage-exiftool-perl`

---

### 3. Make Your Changes

- Keep changes focused — one bug fix or feature per PR
- Follow the existing code style (CustomTkinter widgets, type hints, helper patterns)
- Update `requirements.txt` if you add new Python dependencies
- Test your changes by running the application and exercising the relevant feature

---

### 4. Sync With Upstream

Before opening a PR, sync your fork with the latest `main`:

```bash
git remote add upstream https://github.com/AHJ32/LeoSetter.git
git fetch upstream
git rebase upstream/main
```

---

## Pull Request Guidelines

- **Link the issue** in your PR description (e.g. `Closes #42`)
- **Fill in the template** — see [PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md)
- **Keep PRs small and focused** — large PRs are harder to review and merge
- **Include screenshots or recordings** for any UI-facing changes
- A maintainer will review your PR, may request changes, and will merge once everything looks good

---

*Thank you for helping make LeoSetter better! 🙏*
