# Contributing to Office Assistant

We love your input! We want to make contributing to Office Assistant as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## We Develop with Github
We use Github to host code, to track issues and feature requests, as well as accept pull requests.

## We Use [Github Flow](https://guides.github.com/introduction/flow/index.html)
Pull requests are the best way to propose changes to the codebase. We actively welcome your pull requests:

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Any contributions you make will be under the MIT Software License
In short, when you submit code changes, your submissions are understood to be under the same [MIT License](http://choosealicense.com/licenses/mit/) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using Github's [issue tracker](https://github.com/yourusername/office-assistant/issues)
We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/yourusername/office-assistant/issues/new); it's that easy!

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## Development Process

1. Clone the repository:
```bash
git clone https://github.com/yourusername/office-assistant.git
cd office-assistant
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create your .env file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run tests:
```bash
pytest
```

## Code Style

We use [flake8](https://flake8.pycqa.org/en/latest/) for Python style guide enforcement. Please ensure your code follows these guidelines:

- Use 4 spaces for indentation
- Keep lines under 100 characters
- Follow PEP 8 naming conventions
- Add docstrings to all functions and classes
- Include type hints where appropriate

## Documentation

- Update the README.md if you change required dependencies
- Add docstrings to your code
- Comment complex code sections
- Update function/class documentation when changing interfaces

## Testing

- Write tests for new features
- Update tests when changing functionality
- Ensure all tests pass before submitting PR
- Include integration tests where appropriate

## License
By contributing, you agree that your contributions will be licensed under its MIT License.