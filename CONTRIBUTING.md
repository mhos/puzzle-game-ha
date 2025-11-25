# Contributing to Puzzle Game for Home Assistant

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Ways to Contribute

- 🐛 Report bugs
- 💡 Suggest new features
- 📝 Improve documentation
- 🔧 Submit bug fixes
- ✨ Add new features

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a new branch for your feature/fix
4. Make your changes
5. Test thoroughly
6. Submit a pull request

## Development Setup

### Backend Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd app
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

### Testing with Home Assistant

1. Set up a Home Assistant development instance
2. Configure the puzzle_game.yaml package
3. Point it to your development server
4. Test voice commands and automations

## Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and small
- Comment complex logic

## Commit Messages

Use clear, descriptive commit messages:

```
Add feature: describe what was added
Fix: describe what was fixed
Docs: describe documentation changes
Refactor: describe what was refactored
```

## Pull Request Process

1. Update documentation if needed
2. Ensure all tests pass
3. Update README.md if adding features
4. Describe your changes clearly in the PR description
5. Link any related issues

## Bug Reports

When reporting bugs, please include:

- Home Assistant version
- Puzzle Game version
- Steps to reproduce
- Expected behavior
- Actual behavior
- Relevant logs
- Screenshots if applicable

## Feature Requests

When suggesting features:

- Describe the feature clearly
- Explain the use case
- Consider backwards compatibility
- Think about Home Assistant integration

## Code of Conduct

- Be respectful and constructive
- Welcome newcomers
- Focus on the code, not the person
- Help others learn and grow

## Questions?

- Open an issue for questions
- Check existing issues first
- Be patient and respectful

Thank you for contributing! 🎉
