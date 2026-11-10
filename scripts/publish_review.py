"""Operator-terminal publication entry point; never launch as a model tool."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.github_publisher import GitHubPublisher, snapshot_request
from runtime.publication_gate import PublicationGate


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pull-number", type=int, required=True)
    parser.add_argument("--reviewed-sha", required=True)
    parser.add_argument("--request", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        with args.request.open("rb") as handle:
            raw = handle.read(4 * 1024 * 1024 + 1)
        if len(raw) > 4 * 1024 * 1024:
            raise ValueError("Request exceeds size limit")
        request = snapshot_request(args.repository, args.pull_number, args.reviewed_sha,
                                   json.loads(raw))
        preview = json.dumps(request, sort_keys=True, indent=2, ensure_ascii=True)
        digest = hashlib.sha256(preview.encode()).hexdigest()
        challenge = f"publish {args.repository}#{args.pull_number} {args.reviewed_sha} {digest}"
        # No --approve flag, grant file, stdin boolean, or model-output consent.
        # The host must keep this terminal and process outside model capabilities.
        with open("/dev/tty", "r+") as terminal:
            if not terminal.isatty():
                raise PermissionError("An operator-controlled terminal is required")
            terminal.write(f"Target: {args.repository}#{args.pull_number}\nReviewed head: {args.reviewed_sha}\n{preview}\nType exactly to authorize this one request:\n{challenge}\n> ")
            terminal.flush()
            if terminal.readline().rstrip("\r\n") != challenge:
                raise PermissionError("No matching operator approval")
        gate = PublicationGate()
        gate.record_operator_approval(args.repository, args.pull_number, args.reviewed_sha, request)
        result = GitHubPublisher().publish(gate, args.repository, args.pull_number,
                                           args.reviewed_sha, request)
        print(json.dumps({"url": result["html_url"], "state": result.get("state")}))
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"Publication failed ({type(error).__name__}); inspect GitHub before retrying.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
