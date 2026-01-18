# Contributing to Even-Odd League

Thank you for your interest in contributing to the Even-Odd League Multi-Agent Competition System! This document provides guidelines and instructions for contributing.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Code Standards](#code-standards)
5. [Testing Requirements](#testing-requirements)
6. [Documentation](#documentation)
7. [Pull Request Process](#pull-request-process)

---

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- pip (Python package manager)

### Setup Development Environment

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd agents-task7
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Verify setup**
   ```bash
   pytest tests/ -v
   ```

---

## Development Workflow

### Branch Naming

Use descriptive branch names:
- `feature/add-new-strategy` - New features
- `fix/registration-timeout` - Bug fixes
- `docs/update-api-reference` - Documentation
- `refactor/cleanup-state-management` - Code refactoring

### Commit Messages

Follow conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(player): add momentum strategy plugin
fix(referee): handle timeout on player disconnect
docs(api): update registration endpoint examples
test(jsonrpc): add edge case tests for malformed requests
```

---

## Code Standards

### Formatting

All code must pass formatting checks:

```bash
# Format code
black src/ tests/
isort src/ tests/

# Check formatting (what CI runs)
black --check src/ tests/
isort --check-only src/ tests/
```

### Linting

Code must pass linting:

```bash
# Run linters
flake8 src/
pylint src/
```

### Type Checking

Add type hints to all public functions:

```python
def choose_parity(game_id: str, history: List[Dict[str, Any]]) -> str:
    """Choose parity for a game.

    Args:
        game_id: Unique game identifier
        history: Previous game results

    Returns:
        Either "even" or "odd"
    """
    ...
```

Run type checker:
```bash
mypy src/
```

### Code Style Guidelines

1. **Line length**: Maximum 100 characters
2. **Imports**: Use absolute imports, sorted by isort
3. **Docstrings**: Google style for all public functions/classes
4. **Naming**:
   - Classes: `PascalCase`
   - Functions/variables: `snake_case`
   - Constants: `UPPER_SNAKE_CASE`

---

## Testing Requirements

### Test Coverage

- All new features must include tests
- Maintain minimum 80% code coverage
- Test both success and error cases

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test categories
pytest tests/ -m unit
pytest tests/ -m integration
```

### Writing Tests

```python
import pytest

class TestMyFeature:
    """Tests for my feature."""

    def test_success_case(self):
        """Test the happy path."""
        result = my_function(valid_input)
        assert result == expected_output

    def test_error_handling(self):
        """Test error cases."""
        with pytest.raises(ValueError):
            my_function(invalid_input)

    @pytest.mark.integration
    def test_integration(self):
        """Test integration with other components."""
        ...
```

---

## Documentation

### When to Document

- All public APIs
- Complex algorithms
- Configuration options
- Breaking changes

### Documentation Style

- Use Markdown for all documentation
- Include code examples
- Keep documentation up-to-date with code

### Updating Documentation

1. Update relevant docs in `docs/` directory
2. Update README.md if adding new features
3. Add docstrings to new code
4. Update API_REFERENCE.md for endpoint changes

---

## Pull Request Process

### Before Submitting

1. **Run all checks locally**
   ```bash
   pre-commit run --all-files
   pytest tests/ -v
   ```

2. **Update documentation** if needed

3. **Write meaningful commit messages**

### PR Requirements

- [ ] All CI checks pass
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No merge conflicts

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### Review Process

1. Submit PR with description
2. Address reviewer feedback
3. Ensure CI passes
4. Get approval from maintainer
5. Squash and merge

---

## Creating Strategy Plugins

See [docs/PLUGIN_DEVELOPMENT.md](docs/PLUGIN_DEVELOPMENT.md) for detailed instructions on creating custom strategy plugins.

Quick start:

1. Create directory: `src/agents/player/plugins/my_strategy/`
2. Create `strategy.py` with `ParityStrategy` subclass
3. Export via `STRATEGY_CLASS = MyStrategy`

---

## Getting Help

- Check [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- Review existing issues
- Open a new issue with details

---

## Recognition

Contributors will be recognized in:
- Git commit history
- Release notes
- CONTRIBUTORS.md (for significant contributions)

Thank you for contributing!
