"""Pytest bootstrap: deterministic Omega key for the test environment.

Production sets a real 32+ byte RAGNAR_OMEGA_KEY via environment; the lock is
fail-closed and contract-tested to REFUSE without it.
"""

import os

os.environ.setdefault("RAGNAR_OMEGA_KEY", "test-secret-key-for-contract-tests")
