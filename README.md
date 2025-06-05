# Auto-Modeler: An AI-driven Operations-Research assistant

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Try%20Now-success?style=for-the-badge)](https://auto-modeler.onrender.com)

[![CI](https://github.com/dasberkant/auto-modeler/workflows/CI/badge.svg)](https://github.com/dasberkant/auto-modeler/actions)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Deployed on Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7.svg)](https://render.com)

## 1. Purpose

Auto-Modeler is a cross-platform application designed to assist users in solving deterministic Operations Research (OR) problems. It aims to streamline the process from problem statement to a verified solution by:

*   Ingesting a plain-language description of any deterministic OR problem (linear, mixed-integer, network flow, etc.).
*   Automatically formulating the mathematical model (sets, indices, parameters, variables, objective, constraints) and displaying it in textbook style (LaTeX-rendered with a plaintext fallback).
*   Allowing the user to run the model in an open-source LP/MILP solver (default: Python + PuLP/OR-Tools) with a single click.
*   Generating, running, and displaying the solver code in Python transparently.
*   Implementing self-healing capabilities:
    *   If runtime or syntactic errors occur, it captures the traceback, revises the code, and re-executes automatically.
    *   If the model produces infeasible/unbounded results, it diagnoses likely modeling issues (e.g., bad bounds, missing constraints, sign errors), revises the formulation, and reruns.
*   Validating successful solutions by:
    *   Performing sanity checks (e.g., constraint satisfaction, edge cases, units).
    *   Commenting on model reasonableness and recommending sensitivity analysis if needed.
*   Stopping iteration once the model passes all checks and explicitly stating, "Model and results verified: no further issues detected."

## 2. Key Features & UX Flow

The user experience will follow these general steps:

1.  **Enter/Paste Problem Statement**: The user provides the problem description in plain language.
    *   **System Response**: An NLP engine (powered by Gemini API) parses the input, and a draft OR model is displayed (LaTeX view with a collapsible plaintext option).
2.  **"Run in Solver" Button**: The user clicks to solve the formulated problem.
    *   **System Response**: Python code is auto-generated and executed in a sandboxed backend using PuLP or OR-Tools.
3.  **If Error**:
    *   **System Response**: The error is parsed, the code/model is auto-revised, and the solver is rerun (looping back to step 2 or a revised step 1).
4.  **If Success**:
    *   **System Response**: A solution table and charts (if applicable) are rendered. The "Validate" stage begins.
5.  **Validation Finds Issue**:
    *   **System Response**: The model is adjusted based on validation feedback, and the solver is rerun (looping back to step 2 or a revised step 1).
6.  **Validation Passes**:
    *   **System Response**: A final report is shown, and the application concludes the loop, stating: "Model and results verified: no further issues detected."

## 3. Core Technologies (Planned)

*   **AI Backend**: Gemini API for NLP, problem formulation, code generation, error diagnosis, and solution validation assistance.
*   **Solver**: Python with PuLP or Google OR-Tools.
*   **Mathematical Rendering**: LaTeX and plaintext.
*   **Platform**: Cross-platform (specific UI/framework TBD).

## 4. Installation

### Prerequisites
- Python 3.8 or higher
- Git

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/auto-modeler.git
   cd auto-modeler
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install the package in development mode:**
   ```bash
   pip install -e .
   ```

5. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env and replace the placeholder with your actual Gemini API key
   # Get your API key from: https://makersuite.google.com/app/apikey
   ```

## 5. Usage

### 🌐 Live Web Application
**Try Auto-Modeler online:** [https://auto-modeler.onrender.com](https://auto-modeler.onrender.com)

*Note: You'll need a free Google Gemini API key. Get one at [Google AI Studio](https://makersuite.google.com/app/apikey)*

### Quick Start (Local Development)
```bash
# Run the main application
python -m app.main

# Or use the command line interface
auto-modeler --help
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_nlp_processor.py
```

### Code Quality
```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type checking
mypy app/
```

## 6. Project Structure

```
auto-modeler/
├── app/                    # Main application package
│   ├── __init__.py
│   ├── main.py            # Entry point
│   ├── nlp_processor.py   # NLP processing logic
│   ├── model_formulator.py # Mathematical model formulation
│   ├── solver_engine.py   # Optimization solver interface
│   ├── validator.py       # Solution validation
│   └── ui/                # User interface components
│       ├── app.py         # Flask web interface
│       ├── templates/     # HTML templates
│       └── static/        # CSS, JS, images
├── tests/                 # Test suite
├── .github/workflows/     # CI/CD configuration
├── docs/                  # Documentation (optional)
├── requirements.txt       # Python dependencies
├── setup.py              # Package setup
├── pyproject.toml        # Tool configuration
├── .gitignore            # Git ignore patterns
├── LICENSE               # MIT License
└── README.md             # This file
```

## 7. Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the tests (`pytest`)
5. Format your code (`black . && isort .`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 8. License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 9. Support

If you encounter any issues or have questions, please:
1. Check the [Issues](https://github.com/yourusername/auto-modeler/issues) page
2. Create a new issue if your problem isn't already reported
3. Provide detailed information about the problem and your environment 