# Contributing to Anki MCP

Thank you for your interest in contributing! 🎉

## Quick Start

1. **Fork** the repository
2. **Clone** your fork
3. **Create a branch**: `git checkout -b feature/my-feature`
4. **Make changes** and test
5. **Commit**: `git commit -m "Add my feature"`
6. **Push**: `git push origin feature/my-feature`
7. **Open a Pull Request**

## Development Setup

```bash
# Clone the repository
git clone https://github.com/guepardlover77/anki-mcp.git
cd anki-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Areas for Contribution

### Priority Features (Phase 4)
- [ ] PDF extraction for flashcard generation
- [ ] Web scraping for content import
- [ ] Advanced cloze deletion algorithms
- [ ] Card improvement suggestions with AI

### Additional Tools
- [ ] More statistics visualizations
- [ ] Spaced repetition algorithms
- [ ] Integration with other SRS systems
- [ ] Export to more formats

### Documentation
- [ ] Tutorial videos
- [ ] Example use cases
- [ ] API documentation
- [ ] Translations

## Code Guidelines

- **Style**: Follow PEP 8, use `ruff` for linting
- **Types**: Add type hints to all functions
- **Tests**: Write tests for new features
- **Docs**: Update README for user-facing changes

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=anki_mcp --cov-report=html

# Type checking
mypy src/
```

## Pull Request Process

1. Update tests for your changes
2. Update documentation if needed
3. Ensure all tests pass
4. Follow the commit message format:
   ```
   type: Short description

   Longer explanation if needed.

   Fixes #123
   ```

## Community

- Ask questions in [Discussions](https://github.com/guepardlover77/anki-mcp/discussions)
- Report bugs in [Issues](https://github.com/guepardlover77/anki-mcp/issues)
- Follow best practices and be respectful

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
