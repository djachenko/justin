# justin

Photo processing and management tool.

## Installation

### Basic installation

```bash
pip install -e .
```

### With development dependencies

```bash
pip install -e ".[dev]"
```

### With server dependencies (for web interface)

```bash
pip install -e ".[server]"
```

### All dependencies

```bash
pip install -e ".[dev,server]"
```

## Development setup

For local development with editable local packages:

1. Install the package in development mode:
```bash
pip install -e ".[dev]"
```

2. Install local dependencies (if needed):
```bash
pip install -e ../pyvko
pip install -e ../justin_utils
```

## Usage

```bash
justin <command> [options]
```