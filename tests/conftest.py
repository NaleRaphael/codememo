import pytest


def pytest_addoption(parser):
    parser.addoption(
        '--run_with_display', action='store_true',
        help='Run test cases required to be run with display.'
    )


def pytest_configure(config):
    config.addinivalue_line(
        'markers',
        'run_with_display: mark test which should be run with display'
    )


def pytest_collection_modifyitems(config, items):
    # Comment this out to prevent being in conflict with module level mark.
    # setup_marker_run_with_display(config, items)
    pass


def setup_marker_run_with_display(config, items):
    if config.getoption('--run_with_display'):
        return
    marker = pytest.mark.skip(reason='need --run_with_display option to run')
    for item in items:
        if 'run_with_display' in item.keywords:
            item.add_marker(marker)
