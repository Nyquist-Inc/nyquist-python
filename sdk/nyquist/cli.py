"""``nyq`` — the console entry point of the Nyquist SDK (stdlib + httpx).

Verbs, each honest about what it could not do:

* ``nyq login`` — store the base URL and API key in ``~/.nyquist/config.json``
  (0600) after the gateway has accepted the key;
* ``nyq quote`` / ``nyq history`` / ``nyq desk`` — research verbs
  (:mod:`nyquist.cli_research`);
* ``nyq mcp`` — serve the MCP tools over stdio (needs ``pip install nyquist-mcp``);
* ``nyq tools search <words…>`` — rank governed tools; says when the surface
  is switched off instead of reporting "no match";
* ``nyq tools call <tool_id> [--json '{…}' | --file p.json]`` — execute one
  tool as you and print its JSON result;
* ``nyq doctor`` — probe a deployment: gateway health, the governed surface,
  the agents runtime. Every check prints ``ok`` / ``fail`` / ``skipped`` with
  a reason; a check that could not run is never reported as ``ok``.

Configuration, first match wins: ``--base-url`` / ``--api-key`` flags,
``NYQUIST_BASE_URL`` / ``NYQUIST_API_KEY`` env, then ``~/.nyquist/config.json``
(``endpoint`` / ``api_key`` — written by ``nyq login`` and by the backend onboarding CLI).

Exit codes: 0 done · 1 the platform refused or failed · 2 usage or config
error · 3 (``doctor`` only) nothing failed but some checks were skipped.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any

import httpx

from . import __version__
from .cli_research import add_research_commands
from .client import DEFAULT_BASE_URL, Nyquist, checked_base_url, clean_api_key
from .errors import NyquistError
from .tools import FLAG

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2
EXIT_INCOMPLETE = 3

DEFAULT_CONFIG = Path.home() / ".nyquist" / "config.json"


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_key: str | None
    config_path: Path = DEFAULT_CONFIG
    #: Where ``api_key`` came from: ``flag`` / ``env`` / ``config`` / ``None``.
    #: ``nyq login`` must not re-save the key it is meant to replace.
    api_key_source: str | None = None


def _read_config_file(path: Path) -> dict[str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def resolve_settings(
    args: argparse.Namespace, env: Mapping[str, str], config_path: Path
) -> Settings:
    stored = _read_config_file(config_path)
    base_url = (
        args.base_url
        or env.get("NYQUIST_BASE_URL")
        or stored.get("endpoint")
        or DEFAULT_BASE_URL
    )
    sources = (("flag", args.api_key), ("env", env.get("NYQUIST_API_KEY")),
               ("config", stored.get("api_key")))
    source, api_key = next(((name, key) for name, key in sources if key), (None, None))
    return Settings(base_url=str(base_url).rstrip("/"), api_key=api_key,
                    config_path=config_path, api_key_source=source)


# ─────────────────────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────────────────────


def _client(settings: Settings, transport: httpx.BaseTransport | None) -> Nyquist:
    return Nyquist(api_key=settings.api_key, base_url=settings.base_url, transport=transport)


def cmd_tools_search(args, settings: Settings, transport, out: IO[str], err: IO[str]) -> int:
    with _client(settings, transport) as nq:
        found = nq.tools.search(" ".join(args.words), limit=args.limit)
    if not found.enabled:
        print(f"The governed tool surface is off: {FLAG} is not set on the gateway "
              f"({settings.base_url}). Nothing is exposed — this is not 'no match'.", file=err)
        return EXIT_FAIL
    if args.json:
        json.dump({"query": found.query, "results": found.results,
                   "total_available": found.total_available}, out, indent=2)
        out.write("\n")
        return EXIT_OK
    if not found.results:
        print(f"no tools matched {found.query!r} ({found.total_available} available)", file=out)
        return EXIT_OK
    for tool in found:
        print(
            f"{tool['tool_id']}\n"
            f"    {tool['method']} {tool['path']}  [{tool.get('requires', '?')}]\n"
            f"    {tool.get('description', '').strip()}",
            file=out,
        )
    print(f"\n{len(found)} of {found.total_available} governed tools", file=out)
    return EXIT_OK


def _load_params(args, err: IO[str]) -> dict[str, Any] | None:
    """The parameter mapping, or ``None`` after printing why it is unusable."""
    if args.file:
        try:
            raw = Path(args.file).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"cannot read {args.file}: {exc}", file=err)
            return None
    else:
        raw = args.json or "{}"
    try:
        params = json.loads(raw)
    except ValueError as exc:
        print(f"parameters are not valid JSON: {exc}", file=err)
        return None
    if not isinstance(params, dict):
        print("parameters must be a JSON object", file=err)
        return None
    return params


def cmd_tools_call(args, settings: Settings, transport, out: IO[str], err: IO[str]) -> int:
    params = _load_params(args, err)
    if params is None:
        return EXIT_USAGE
    with _client(settings, transport) as nq:
        result = nq.tools.execute(args.tool_id, params)
    json.dump(result, out, indent=2, default=str)
    out.write("\n")
    return EXIT_OK


# ── doctor ───────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Check:
    name: str
    status: str  # ok | fail | skipped
    message: str


def _check_health(settings: Settings, transport) -> Check:
    try:
        with httpx.Client(base_url=settings.base_url, transport=transport, timeout=10.0) as http:
            resp = http.get("/health")
    except httpx.HTTPError as exc:
        return Check("health", "fail", f"{settings.base_url}/health unreachable: {exc}")
    if resp.status_code != 200:
        return Check("health", "fail", f"/health answered {resp.status_code}")
    try:
        body = resp.json()
    except ValueError:
        body = {}
    build = body.get("build") or body.get("version") or "unknown build"
    return Check("health", "ok", f"gateway reachable ({build})")


def _check_tools(nq: Nyquist) -> Check:
    try:
        gov = nq.tools.governance()
    except NyquistError as exc:
        return Check("tools", "fail", f"/api/ontology/tools/governance: {exc.detail}")
    if not gov.get("enabled"):
        return Check("tools", "fail",
                     f"{FLAG} is off on the gateway — tools/search, the MCP node's generated "
                     "tools and nyq are all empty until it is set")
    total = int(gov.get("total_tools") or 0)
    if total == 0:
        return Check("tools", "fail", f"{FLAG} is on but the surface is empty")
    return Check("tools", "ok", f"{total} governed tools")


def _check_agents(nq: Nyquist) -> Check:
    try:
        report = nq._request("GET", "/api/agents/readiness")
    except NyquistError as exc:
        return Check("agents", "fail", f"/api/agents/readiness: {exc.detail}")
    if report.get("ready"):
        return Check("agents", "ok", "agents runtime ready")
    blockers = report.get("blockers") or []
    reason = "; ".join(str(b) for b in blockers) if blockers else (
        "AGENTS_ENABLED is off" if not report.get("flag_enabled") else "no provider configured"
    )
    return Check("agents", "fail", f"agents not ready: {reason}")


def cmd_doctor(args, settings: Settings, transport, out: IO[str], err: IO[str]) -> int:
    checks = [_check_health(settings, transport)]
    if settings.api_key:
        with _client(settings, transport) as nq:
            checks.append(_check_tools(nq))
            checks.append(_check_agents(nq))
    else:
        reason = "no API key (set NYQUIST_API_KEY, pass --api-key, or run nyq login)"
        checks.append(Check("tools", "skipped", reason))
        checks.append(Check("agents", "skipped", reason))
    print(f"nyq doctor — {settings.base_url}", file=out)
    for check in checks:
        print(f"{check.status:<8}{check.name:<8}{check.message}", file=out)
    if any(c.status == "fail" for c in checks):
        return EXIT_FAIL
    if any(c.status == "skipped" for c in checks):
        return EXIT_INCOMPLETE
    return EXIT_OK


# ── login ────────────────────────────────────────────────────────────────────


def _write_config(path: Path, endpoint: str, api_key: str) -> None:
    """Merge ``endpoint``/``api_key`` into the config file, readable by the owner only.

    Other keys in the file (the onboarding CLI shares it) are kept. The key is
    written to a fresh 0600 file beside the target and moved over it: an
    existing file created 0644 by another tool is never written in place, a
    symlink at the path is replaced rather than followed, and a crash leaves
    either the old file or the new one.
    """
    merged = {**_read_config_file(path), "endpoint": endpoint, "api_key": api_key}
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".config-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(merged, fh, indent=2)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def cmd_login(args, settings: Settings, transport, out: IO[str], err: IO[str]) -> int:
    # Only a key given NOW counts: the stored one is what login replaces.
    api_key = settings.api_key if settings.api_key_source in ("flag", "env") else None
    if not api_key:
        if not sys.stdin.isatty():
            print("no API key: pass --api-key or set NYQUIST_API_KEY (no terminal to prompt on)",
                  file=err)
            return EXIT_USAGE
        api_key = getpass.getpass("Nyquist API key (nyquist.pro/settings/api): ")
    try:
        # The same checks the client applies, so --no-verify cannot save a key
        # or an endpoint that every later command would refuse.
        api_key = clean_api_key(api_key)
        checked_base_url(settings.base_url)
    except NyquistError as exc:
        print(exc.detail, file=err)
        return EXIT_USAGE
    if not args.no_verify:
        # governance needs a valid credential and nothing else: a 401 here is
        # about the key, not about a switched-off surface.
        with Nyquist(api_key=api_key, base_url=settings.base_url, transport=transport) as nq:
            nq.tools.governance()
    _write_config(settings.config_path, settings.base_url, api_key)
    verified = "not verified (--no-verify)" if args.no_verify else "accepted by the gateway"
    print(f"saved to {settings.config_path} — key {verified}, endpoint {settings.base_url}",
          file=out)
    return EXIT_OK


# ── mcp ──────────────────────────────────────────────────────────────────────


def cmd_mcp(args, settings: Settings, transport, out: IO[str], err: IO[str]) -> int:
    try:
        from nyquist_mcp.server import serve  # noqa: PLC0415 — optional package
    except ImportError:
        print("the MCP server ships separately: pip install nyquist-mcp", file=err)
        return EXIT_USAGE
    serve(base_url=settings.base_url, api_key=settings.api_key)
    return EXIT_OK


# ─────────────────────────────────────────────────────────────────────────────
# Parser + entry point
# ─────────────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nyq",
        description="Nyquist — the agent research desk, governed tools and deployment "
                    "checks from the terminal.",
        epilog="exit codes: 0 done · 1 platform refused/failed · 2 usage or config error · "
               "3 doctor: some checks skipped, none failed",
    )
    parser.add_argument("--version", action="version", version=f"nyq {__version__}")
    parser.add_argument("--base-url", help="gateway base URL (env NYQUIST_BASE_URL)")
    parser.add_argument("--api-key", help="personal B2B key (env NYQUIST_API_KEY)")
    sub = parser.add_subparsers(dest="command", required=True)

    login = sub.add_parser("login", help="verify an API key and save it to ~/.nyquist/config.json")
    login.add_argument("--no-verify", action="store_true",
                       help="save without asking the gateway to accept the key")
    login.set_defaults(handler=cmd_login)

    add_research_commands(sub)

    tools = sub.add_parser("tools", help="the governed tool surface")
    tools_sub = tools.add_subparsers(dest="tools_command", required=True)

    search = tools_sub.add_parser("search", help="rank tools against words")
    search.add_argument("words", nargs="+")
    search.add_argument("--limit", type=int, default=20)
    search.add_argument("--json", action="store_true", help="print the raw response")
    search.set_defaults(handler=cmd_tools_search)

    call = tools_sub.add_parser("call", help="execute one tool as you")
    call.add_argument("tool_id")
    source = call.add_mutually_exclusive_group()
    source.add_argument("--json", help="parameters as a JSON object")
    source.add_argument("--file", help="path to a JSON file with the parameters")
    call.set_defaults(handler=cmd_tools_call)

    doctor = sub.add_parser("doctor", help="probe the deployment: health, tools, agents")
    doctor.set_defaults(handler=cmd_doctor)

    mcp = sub.add_parser(
        "mcp", help="serve the Nyquist MCP tools over stdio (pip install nyquist-mcp)"
    )
    mcp.set_defaults(handler=cmd_mcp)
    return parser


#: Verbs that run without a stored key: doctor reports its absence, login
#: obtains one, and the MCP server starts anyway so a client can list tools.
_KEYLESS = frozenset({"doctor", "login", "mcp"})


def main(
    argv: list[str] | None = None,
    *,
    transport: httpx.BaseTransport | None = None,
    env: Mapping[str, str] | None = None,
    stdout: IO[str] | None = None,
    stderr: IO[str] | None = None,
    config_path: Path | None = None,
) -> int:
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0) if isinstance(exc.code, int) else EXIT_USAGE
    settings = resolve_settings(
        args, os.environ if env is None else env, config_path or DEFAULT_CONFIG
    )
    if args.command not in _KEYLESS and not settings.api_key:
        print("no API key: set NYQUIST_API_KEY, pass --api-key, or run `nyq login`", file=err)
        return EXIT_USAGE
    try:
        return int(args.handler(args, settings, transport, out, err))
    except NyquistError as exc:
        print(f"nyq: {exc.detail}", file=err)
        return EXIT_FAIL


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
