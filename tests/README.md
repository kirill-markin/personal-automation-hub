# Tests

This directory contains the test suite for the Personal Automation Hub.

## Test Structure

```
tests/
├── README.md                    # This file
├── __init__.py                  # Python package marker
└── integration/                 # Integration tests (require real API credentials)
    ├── __init__.py
    ├── README.md                # Integration tests documentation
    ├── test_calendar_access.py  # Google Calendar access tests
    └── test_list_calendars.py   # Calendar listing utility tests
```

## Test Types

### Unit Tests
- **Location**: `tests/unit/` (to be created)
- **Purpose**: Fast, isolated tests of individual functions and classes
- **Dependencies**: Mock objects, no external services
- **Run by default**: Yes

### Integration Tests
- **Location**: `tests/integration/`
- **Purpose**: Test real API connections and end-to-end workflows
- **Dependencies**: Real Google API credentials in `.env` file
- **Run by default**: No (excluded by default)

## Running Tests

### Default Test Run (Unit Tests Only)
```bash
# Run all unit tests (excludes integration tests)
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=backend
```

### Integration Tests
```bash
# Run only integration tests (requires real API credentials)
pytest -m integration

# Run integration tests with verbose output
pytest -m integration -v

# Run specific integration test file
pytest tests/integration/test_calendar_access.py -m integration
```

### All Tests
```bash
# Run all tests (including integration tests)
pytest -m ""

# Or override the default marker filter
pytest --override-ini="addopts="
```

## Test Configuration

Test configuration is defined in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-m", "not integration",  # Exclude integration tests by default
    "--tb=short",
    "--strict-markers",
    "--strict-config",
]
markers = [
    "integration: marks tests as integration tests that require real API credentials",
]
```

## Test Markers

### @pytest.mark.integration
- Marks tests that require real API credentials
- Excluded from default test runs
- Must be explicitly included with `-m integration`

Example:
```python
@pytest.mark.integration
def test_google_calendar_connection():
    """Test real Google Calendar API connection."""
    # This test requires real API credentials
    pass
```

## Environment Variables for Integration Tests

Integration tests require a `.env` file with real Google API credentials:

```bash
# Google Calendar Account 1 (Personal)
GOOGLE_ACCOUNT_1_NAME=your-personal-account
GOOGLE_ACCOUNT_1_CLIENT_ID=your-client-id
GOOGLE_ACCOUNT_1_CLIENT_SECRET=your-client-secret
GOOGLE_ACCOUNT_1_REFRESH_TOKEN=your-refresh-token

# Google Calendar Account 2 (Work)
GOOGLE_ACCOUNT_2_NAME=your-work-account
GOOGLE_ACCOUNT_2_CLIENT_ID=your-work-client-id
GOOGLE_ACCOUNT_2_CLIENT_SECRET=your-work-client-secret
GOOGLE_ACCOUNT_2_REFRESH_TOKEN=your-work-refresh-token

# Sync Flow Configuration
SYNC_FLOW_1_NAME=Work to Personal Busy
SYNC_FLOW_1_SOURCE_ACCOUNT_ID=2
SYNC_FLOW_1_SOURCE_CALENDAR_ID=your-work-calendar-id
SYNC_FLOW_1_TARGET_ACCOUNT_ID=1
SYNC_FLOW_1_TARGET_CALENDAR_ID=your-personal-busy-calendar-id
```

## CI/CD Integration

The test configuration is designed to be safe for CI/CD:

- **Default behavior**: Only runs unit tests (no real API calls)
- **Integration tests**: Explicitly excluded unless specifically requested
- **No accidental API calls**: Integration tests cannot run without explicit opt-in

Example GitHub Actions workflow:
```yaml
- name: Run unit tests
  run: pytest  # Only runs unit tests

- name: Run integration tests (manual)
  run: pytest -m integration  # Only if environment variables are set
  if: github.event_name == 'workflow_dispatch'  # Manual trigger only
```

## Adding New Tests

### Unit Tests
1. Create test files in `tests/unit/`
2. Use standard pytest conventions
3. Mock external dependencies
4. No special markers needed

### Integration Tests
1. Create test files in `tests/integration/`
2. Add `@pytest.mark.integration` decorator
3. Document required environment variables
4. Test real API connections

## Best Practices

1. **Unit tests first**: Write unit tests for all business logic
2. **Integration tests sparingly**: Only for critical end-to-end workflows
3. **Mock external services**: Use mocks in unit tests
4. **Clear test names**: Use descriptive test function names
5. **Test isolation**: Each test should be independent
6. **Environment safety**: Never commit real credentials 