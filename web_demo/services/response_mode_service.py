from __future__ import annotations

"""Select the response path for the latency-critical chat endpoint.

The default path builds a complete, cited answer from the local curated KB.
It has a bounded local runtime and does not make a user's completed response
depend on a remote model finishing token generation.  Operators can explicitly
choose ``dify`` for the richer generative workflow when that trade-off is wanted.
"""

import os


def use_local_complete_response() -> bool:
    """Return whether `/api/chat` should complete on the local KB path.

    Accepted Dify-only values are intentionally narrow so a typo cannot quietly
    disable the response-time protection in a deployment.
    """

    mode = os.getenv("LABSAFE_RESPONSE_MODE", "local_complete").strip().lower()
    return mode not in {"dify", "dify_only"}
