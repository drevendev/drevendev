"""CI-only publication guard. No force push, no writes outside README."""
import os
from pathlib import Path
import subprocess
import sys

from refresh_profile import ROOT, ProfileError, assert_only_block, report


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.STDOUT)


def publish(branch):
    if not branch or branch.startswith("-") or any(c.isspace() for c in branch):
        raise ProfileError("Invalid target branch")
    before = git("show", "HEAD:README.md")
    after = (ROOT / "README.md").read_bytes()
    assert_only_block(before, after)
    status = git("status", "--porcelain", "--untracked-files=all").decode().splitlines()
    if before == after:
        if status:
            raise ProfileError("Unexpected worktree changes")
        report({"publication": "no change", "commit_created": False})
        return
    if status != [" M README.md"]:
        raise ProfileError("Publication must change only unstaged README.md")
    git("add", "--", "README.md")
    git("-c", "user.name=github-actions[bot]", "-c",
        "user.email=41898282+github-actions[bot]@users.noreply.github.com",
        "commit", "-m", "docs(profile): refresh verified public releases")
    try:
        git("-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential",
            "push", "origin", f"HEAD:refs/heads/{branch}")
    except subprocess.CalledProcessError:
        # A protection rule or concurrent human commit wins. Never rebase/force.
        raise ProfileError("Push refused; check branch protection or rerun on latest default branch") from None
    report({"publication": "pushed", "commit_created": True, "sha": git("rev-parse", "HEAD").decode().strip()})


if __name__ == "__main__":
    try:
        publish(os.environ.get("PROFILE_DEFAULT_BRANCH"))
    except (ProfileError, subprocess.CalledProcessError) as exc:
        report({"publication": "failed", "error": str(exc) if isinstance(exc, ProfileError) else "git operation failed"})
        sys.exit(2)

