#!/usr/bin/env python3
"""Invoke a language-agnostic STP client adapter.

The adapter can be configured as either:
- STP_CLIENT_CMD: a CLI command that accepts one JSON argument and returns JSON
- STP_ADAPTER_URL: an HTTP endpoint that accepts a JSON POST and returns JSON
"""

import argparse
import json
import os
import shlex
import subprocess
import sys
import urllib.error
import urllib.request


def _load_request(args):
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            return json.load(f)
    if args.json:
        return json.loads(args.json)
    if not sys.stdin.isatty():
        return json.load(sys.stdin)
    raise SystemExit("missing JSON request: pass JSON, --file, or stdin")


def _call_http(url, request):
    body = json.dumps(request, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    http_req = urllib.request.Request(
        url,
        data=body,
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(http_req, timeout=120) as resp:
            data = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        data = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"adapter HTTP {e.code}: {data}") from e
    return json.loads(data)


def _call_cli(cmd, request):
    argv = shlex.split(cmd)
    payload = json.dumps(request, separators=(",", ":"), ensure_ascii=False)
    proc = subprocess.run(
        argv + [payload],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise SystemExit(
            json.dumps(
                {
                    "ok": False,
                    "error_code": "ADAPTER_PROCESS_FAILED",
                    "message": proc.stderr.strip() or proc.stdout.strip(),
                    "returncode": proc.returncode,
                },
                ensure_ascii=False,
            )
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise SystemExit(
            json.dumps(
                {
                    "ok": False,
                    "error_code": "ADAPTER_INVALID_JSON",
                    "message": str(e),
                    "stdout": proc.stdout,
                },
                ensure_ascii=False,
            )
        ) from e


def main():
    parser = argparse.ArgumentParser(description="Call an STP JSON adapter")
    parser.add_argument("json", nargs="?", help="JSON request")
    parser.add_argument("--file", help="Read JSON request from a file")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON response")
    args = parser.parse_args()

    request = _load_request(args)
    adapter_url = os.environ.get("STP_ADAPTER_URL")
    client_cmd = os.environ.get("STP_CLIENT_CMD")

    if adapter_url:
        response = _call_http(adapter_url, request)
    elif client_cmd:
        response = _call_cli(client_cmd, request)
    else:
        response = {
            "ok": False,
            "error_code": "STP_ADAPTER_NOT_CONFIGURED",
            "message": "Set STP_ADAPTER_URL or STP_CLIENT_CMD.",
        }

    if args.pretty:
        print(json.dumps(response, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(response, separators=(",", ":"), ensure_ascii=False))


if __name__ == "__main__":
    main()
