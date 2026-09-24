import logging
import pathlib
from collections.abc import Sequence

import git
import semver

from clover2_dev.errors import ToolingError
from clover2_dev.plugins.version.stores import (
    VersionStore,
    bare,
    reference_store,
    write_all,
)

logger = logging.getLogger(__name__)

LATEST_RC = "rc"
LATEST_STABLE = "stable"


def _open_repo(base_path: pathlib.Path) -> git.Repo | None:
    try:
        return git.Repo(base_path, search_parent_directories=True)
    except (git.InvalidGitRepositoryError, git.NoSuchPathError):
        return None


def parse_tag(tag: str) -> semver.Version:
    if not tag.startswith("v"):
        raise ToolingError(f"Tag '{tag}' must start with 'v'")

    try:
        return semver.Version.parse(tag[1:])
    except ValueError as exc:
        raise ToolingError(f"Tag '{tag}' is not a valid semver version") from exc


def _max_tag(tags: list[str]) -> str | None:
    candidates = []

    for tag in tags:
        try:
            candidates.append((semver.Version.parse(tag[1:]), tag))
        except ValueError:
            continue

    return max(candidates)[1] if candidates else None


def _tag_names(repo: git.Repo) -> list[str]:
    return [t.name for t in repo.tags]


def _payload(base: str, tag: str, stores_changed: bool) -> dict:
    return {"base": base, "tag": tag, "stores_changed": stores_changed}


def _latest_tag(repo: git.Repo, kind: str) -> dict:
    if kind == LATEST_RC:
        tags = [n for n in _tag_names(repo) if n.startswith("v") and "-rc." in n]
        what = "rc"
    else:
        tags = [n for n in _tag_names(repo)
                if n.startswith("v") and "-" not in n]
        what = "stable"

    tag = _max_tag(tags)
    if not tag:
        raise ToolingError(f"No {what} tags found")

    version = parse_tag(tag)
    return {"tag": tag,
            "version": str(version.finalize_version() if what == "rc" else version),
            "commit": repo.commit(tag).hexsha}


def bump(stores: Sequence[VersionStore], field: str,
         reference: str) -> dict:
    current = reference_store(stores, reference).read()
    target = getattr(current, f"bump_{field}")()
    write_all(stores, target)
    return _payload(str(bare(target)), f"v{bare(target)}", True)


def bump_rc(stores: Sequence[VersionStore], base_path: pathlib.Path,
            base_field: str, reference: str) -> dict:
    current = reference_store(stores, reference).read()

    repo = _open_repo(base_path)
    if repo is None:
        logger.warning(
            "Not a git repo; treating '%s' as a fresh rc base", current)
        rc_names, stable_exists = [], False
    else:
        names = _tag_names(repo)
        rc_names = [n for n in names if n.startswith(f"v{current}-rc.")]
        stable_exists = f"v{current}" in names

    if rc_names:
        next_rc = max(int(name.rsplit(".", 1)[1]) for name in rc_names) + 1
        return _payload(str(current), f"v{current}-rc.{next_rc}", False)

    if stable_exists:
        target = getattr(current, f"bump_{base_field}")()
        write_all(stores, target)
        return _payload(str(bare(target)), f"v{target}-rc.1", True)

    return _payload(str(current), f"v{current}-rc.1", False)


def compose(stores: Sequence[VersionStore] | None, base_path: pathlib.Path,
            reference: str, ref: str | None = None, mode: str | None = None,
            latest_rc: bool = False, latest_stable: bool = False) -> dict:
    repo = _open_repo(base_path)
    if repo is None:
        raise ToolingError(f"'{base_path}' is not a git repository")

    if latest_rc:
        return _latest_tag(repo, LATEST_RC)

    if latest_stable:
        return _latest_tag(repo, LATEST_STABLE)

    base = reference_store(stores or [], reference).read()
    if ref and not ref.startswith("refs/"):
        if not ref.startswith("v"):
            raise ToolingError(
                "--ref must be a full git ref or a v-prefixed tag")

        ref = f"refs/tags/{ref}"

    if ref and ref.startswith("refs/tags/"):
        tag_name = ref[len("refs/tags/"):]
        version = parse_tag(tag_name)
        tag = next((t for t in repo.tags if t.name == tag_name), None)

        if tag is None:
            raise ToolingError(f"Tag '{tag_name}' not found in repository")

        build_mode = "pre-release" if version.prerelease else "release"
        git_hash = tag.commit.hexsha[:7]
    else:
        try:
            commit = repo.commit(ref if ref else "HEAD")
        except git.BadName:
            logger.warning("Ref '%s' not found; using HEAD", ref)
            commit = repo.commit("HEAD")

        git_hash = commit.hexsha[:7]
        build_mode = mode

        if build_mode is None:
            build_mode = "master" if ref == "refs/heads/master" else "develop"

        version = _version_for_mode(repo, base, build_mode, git_hash)

    return {"base_version": str(base), "git_hash": git_hash,
            "build_mode": build_mode, "version": str(version)}


def _dev_version(repo: git.Repo, base: semver.Version, git_hash: str) -> str:
    try:
        describe = repo.git.describe("--tags", "--long", "--match", "v*")
        count = int(describe.rsplit("-", 2)[-2])
    except (git.GitCommandError, ValueError, IndexError):
        count = 0

    build = git_hash
    if repo.is_dirty():
        build += ".dirty"
    return f"{base}-dev.{count}+{build}"


def _version_for_mode(repo: git.Repo, base: semver.Version,
                      mode: str, git_hash: str) -> str:
    if mode in ("develop", "master"):
        return _dev_version(repo, base, git_hash)

    try:
        tag = repo.git.describe("--tags", "--exact-match", "HEAD")
    except git.GitCommandError:
        tag = None

    if tag:
        version = parse_tag(tag)
        if (mode == "release") == (version.prerelease is None):
            return str(version)
        logger.warning(
            "Tag '%s' does not match %s mode; using bare base version", tag, mode)
    else:
        logger.warning(
            "No tag on HEAD; %s build uses the bare base version", mode)

    return str(base)
