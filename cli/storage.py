"""CLI storage shim – re-exports from leeter_core.analytics.

Existing CLI modules (e.g. cli/run.py) import mark_problem_solved and
session helpers from this module.  This shim keeps those imports working
while the actual logic now lives in leeter_core.analytics.
"""

from leeter_core.analytics import (
    load_session,
    save_session,
    update_streak,
    mark_problem_solved,
    set_last_accessed_problem,
    get_last_accessed_problem,
)

# Re-export the session file helper for any direct users
from leeter_core.analytics import _get_session_file as get_session_file
