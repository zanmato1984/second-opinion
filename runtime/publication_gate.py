"""Trusted-host consent binding. Never expose this object to any model."""

import hashlib
import json
import re
import threading


def _account(account):
    if not isinstance(account, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}(?:\[bot\])?", account):
        raise ValueError("Expected an explicit GitHub account login")
    return account.lower()


def _binding(repository, pull_number, head_sha, payload):
    if not isinstance(repository, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Expected owner/repository")
    if any(part in (".", "..") for part in repository.split("/")):
        raise ValueError("Repository path segments are not allowed")
    if type(pull_number) is not int or pull_number <= 0:
        raise ValueError("Expected a positive PR number")
    if not isinstance(head_sha, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", head_sha):
        raise ValueError("Expected a full reviewed head SHA")
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object payload")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return repository.lower(), pull_number, head_sha.lower(), hashlib.sha256(encoded).digest()


class PublicationGate:
    """One review session's grant, held by trusted host code, not in artifacts.

    record_operator_approval is called ONLY after the host has checked an actual
    operator instruction. Passing model-generated booleans/text to it is unsafe.
    This helper binds consent; it cannot authenticate the host's event channel.
    """

    def __init__(self):
        self._approved = None
        self._lock = threading.Lock()

    def revoke(self):
        with self._lock:
            self._approved = None

    def record_operator_approval(self, repository, pull_number, reviewed_sha, payload, *, account):
        with self._lock:
            self._approved = None
            self._approved = _binding(repository, pull_number, reviewed_sha, payload) + (_account(account),)

    def consume(self, repository, pull_number, current_head_sha, payload, *, account):
        with self._lock:
            approved, self._approved = self._approved, None
        current = _binding(repository, pull_number, current_head_sha, payload) + (_account(account),)
        if approved is None or approved != current:
            raise PermissionError("No matching operator approval for this target, head, and payload")
