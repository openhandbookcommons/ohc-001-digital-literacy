#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_QMD = ROOT / "back-matter/contributors.qmd"


def run_cmd(cmd: list[str]) -> str:
    """Run a shell command and return stdout as text."""
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_repo_from_git_remote() -> tuple[str, str]:
    """
    Detect owner/repo from git remote origin.

    Supports:
      git@github.com:owner/repo.git
      https://github.com/owner/repo.git
      https://github.com/owner/repo
    """
    remote = run_cmd(["git", "config", "--get", "remote.origin.url"])

    patterns = [
        r"git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$",
        r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$",
        r"https://www\.github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$",
    ]

    for pattern in patterns:
        m = re.match(pattern, remote)
        if m:
            return m.group("owner"), m.group("repo")

    raise RuntimeError(
        f"Could not detect GitHub owner/repo from remote.origin.url: {remote}"
    )


def github_api_get(url: str, token: str | None = None) -> tuple[int, list[dict], dict]:
    """
    Make a GET request to GitHub API and return:
      status_code, parsed_json, headers
    """
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "quarto-contributors-render-script")

    if token:
        req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            headers = dict(resp.headers.items())
            body = resp.read().decode("utf-8")
            data = json.loads(body) if body.strip() else []
            return status, data, headers
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(body) if body.strip() else []
        except Exception:
            data = [{"message": body}]
        return e.code, data, dict(e.headers.items())


def parse_next_link(link_header: str | None) -> str | None:
    """Extract next page URL from GitHub Link header."""
    if not link_header:
        return None

    parts = [p.strip() for p in link_header.split(",")]
    for part in parts:
        if 'rel="next"' in part:
            m = re.match(r"<([^>]+)>;\s*rel=\"next\"", part)
            if m:
                return m.group(1)
    return None


def fetch_all_contributors(owner: str, repo: str, token: str | None = None) -> list[dict]:
    """
    Fetch all contributors via pagination.
    Includes anonymous contributors if present.
    """
    base_url = (
        f"https://api.github.com/repos/"
        f"{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}"
        f"/contributors?per_page=100&anon=true"
    )

    contributors: list[dict] = []
    url = base_url

    while url:
        status, data, headers = github_api_get(url, token=token)

        if status == 204:
            return []
        if status != 200:
            msg = data[0]["message"] if isinstance(data, list) and data else str(data)
            raise RuntimeError(f"GitHub API error ({status}): {msg}")

        if not isinstance(data, list):
            raise RuntimeError("Unexpected GitHub API response format.")

        contributors.extend(data)
        url = parse_next_link(headers.get("Link"))

    return contributors


def escape_markdown(text: str) -> str:
    """Escape markdown table-breaking characters."""
    return text.replace("|", "\\|").replace("\n", " ").strip()


def normalize_contributor(entry: dict) -> tuple[str, str, int]:
    """
    Return (display_name, github_link_or_empty, contributions)
    """
    contributions = int(entry.get("contributions", 0))

    if entry.get("type") == "Anonymous" or entry.get("login") is None:
        name = entry.get("name") or entry.get("email") or "Anonymous contributor"
        return name, "", contributions

    login = entry.get("login", "unknown")
    html_url = entry.get("html_url", f"https://github.com/{login}")
    return login, html_url, contributions


def build_qmd(owner: str, repo: str, contributors: list[dict]) -> str:
    """
    Build the contributors.qmd content.
    """
    lines: list[str] = []
    lines.append("---")
    lines.append("title: GitHub Contributors")
    lines.append("---")
    lines.append("")
    #lines.append("\\clearpage")
    lines.append("")
    lines.append(
        f"This page was generated automatically from the GitHub repository "
        f"`{owner}/{repo}` at render time."
    )
    lines.append("")

    if not contributors:
        lines.append("No contributors were found for this repository.")
        lines.append("")
        return "\n".join(lines)

    lines.append("| Contributor | GitHub | Contributions |")
    lines.append("|---|---|---:|")

    for entry in contributors:
        name, link, contributions = normalize_contributor(entry)
        name = escape_markdown(name)

        if link:
            gh = f"[profile]({link})"
        else:
            gh = ""

        lines.append(f"| {name} | {gh} | {contributions} |")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    try:
        owner, repo = get_repo_from_git_remote()
        token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        contributors = fetch_all_contributors(owner, repo, token=token)

        # sort by contribution count descending just to be explicit
        contributors.sort(key=lambda x: int(x.get("contributions", 0)), reverse=True)

        qmd = build_qmd(owner, repo, contributors)
        OUTPUT_QMD.write_text(qmd, encoding="utf-8")

        print(f"Wrote {OUTPUT_QMD}")
        return 0

    except Exception as e:
        # Fail gracefully by writing a fallback page
        fallback = "\n".join([
            "---",
            "title: Contributors",
            "---",
            "",
            "\\clearpage",
            "",
            "The contributors list could not be generated automatically.",
            "",
            f"Error: `{str(e)}`",
            "",
        ])
        OUTPUT_QMD.write_text(fallback, encoding="utf-8")
        print(f"Warning: {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
