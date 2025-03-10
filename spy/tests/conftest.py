# type: ignore

import pytest
import shutil
import py

ROOT = py.path.local(__file__).dirpath()
HAVE_EMCC = shutil.which("emcc") is not None

def pytest_collection_modifyitems(session, config, items):
    """
    Reorder the test to have a "better" order. In particular:

      - test_zz_mypy.py is always the last, after the subdirectories
      - test_backend_spy.py must run after compiler/*
      - compiler/*.py comes after everythig else (apart mypy)

    The reasoning is that compiler/*.py tests are integration tests and it
    makes sense to run them after the unit tests. And mypy should be last
    because we are not interested in type errors if there are failures.

    The reason for why test_backend_spy must be run after compiler/* is
    explained in test_zz_sanity_check in that file.
    """
    def key(item):
        filename = item.fspath.relto(ROOT)
        if filename == 'test_zz_mypy.py':
            return 100 # last
        elif filename == 'test_backend_spy.py':
            return 99  # second to last
        elif filename.startswith('compiler/'):
            return 98  # third to last
        else:
            return 0   # don't touch

    items.sort(key=key)

def pytest_addoption(parser):
    parser.addoption(
        "--dump-c", action="store_true", default=False,
        help="Dump generated C code"
    )
    parser.addoption(
        "--dump-redshift", action="store_true", default=False,
        help="Dump the redshifted module"
    )


@pytest.fixture(autouse=True)
def skip_if_no_emcc(request):
    if request.node.get_closest_marker("emscripten") and not HAVE_EMCC:
        pytest.skip("Requires emcc")
