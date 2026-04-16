import pytest


# On Windows, Bazel creates NTFS junctions (bazel-bin, bazel-out, bazel-workspace, …).
# pathlib.Path.is_dir() raises OSError on these junctions, which crashes pytest's
# built-in pytest_ignore_collect before norecursedirs or any other filter can apply.
# This tryfirst hook runs before the built-in one and short-circuits the crash.
@pytest.hookimpl(tryfirst=True)
def pytest_ignore_collect(collection_path, config):
    try:
        collection_path.stat()
    except OSError:
        return True
