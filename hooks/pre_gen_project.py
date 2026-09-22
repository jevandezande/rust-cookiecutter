"""Hooks to run before generating the project."""

import re

# Rust 2024 keywords, including those reserved for future use
RUST_KEYWORDS = frozenset(
    """
    abstract as async await become box break const continue crate do dyn else enum extern
    false final fn for gen if impl in let loop macro match mod move mut override priv pub
    ref return self static struct super trait true try type typeof unsafe unsized use
    virtual where while yield
    """.split()
)

# Names cargo refuses (or that shadow the standard library)
RESERVED_CRATE_NAMES = frozenset(
    {"alloc", "build", "core", "deps", "examples", "incremental", "proc_macro", "std", "test"}
)

# kebab-case only. Cargo also accepts `_`, but crates.io treats the two as the same name and the
# ecosystem writes package names with `-`; the snake_case identifier code uses is derived from this
CRATE_REGEX = r"[a-z][a-z0-9]*(-[a-z0-9]+)*"

# GitHub's rule for user and organization names; `project_url` embeds it in `Cargo.toml`
GITHUB_USERNAME_REGEX = r"[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}"

# A host and a path: `git_add_remote` splits the URL into the two to build the `git@` form
PROJECT_URL_REGEX = r"https://[^/\s]+/\S+"

# What crates.io accepts in a keyword, and how many it accepts
KEYWORD_REGEX = r"[a-zA-Z0-9][a-zA-Z0-9_-]*"
KEYWORD_MAX_LENGTH = 20
KEYWORD_MAX_COUNT = 5


def main() -> None:
    """Check every option, failing generation on first one that cannot work."""
    check_crate_name("{{cookiecutter.crate_name}}")
    check_github_username("{{cookiecutter.github_username}}")
    check_project_url("{{cookiecutter.project_url}}")
    check_author_name("{{cookiecutter.author_name}}")
    check_release_compatibility(
        "{{cookiecutter.crate_type}}",
        "{{cookiecutter.release_ci}}",
        "{{cookiecutter.license}}",
    )
    check_interop_compatibility(
        "{{cookiecutter.python_interop}}",
        "{{cookiecutter.release_ci}}",
        "{{cookiecutter.python_dependencies}}",
    )
    check_toml_string("project_name", "{{cookiecutter.project_name}}")
    check_toml_string("author_name", "{{cookiecutter.author_name}}")
    check_toml_string("description", "{{cookiecutter.description}}")
    check_keywords("{{cookiecutter.keywords}}")
    check_publish_metadata(
        "{{cookiecutter.release_ci}}",
        "{{cookiecutter.description}}",
        "{{cookiecutter.keywords}}",
    )


def check_crate_name(crate_name: str) -> None:
    """Check that the crate name is a kebab-case Rust package name.

    Cargo compares the identifier code uses (`-` replaced by `_`) against keywords and reserved
    names, so that is what this checks.

    Args:
        crate_name: name of the crate to check

    Raises:
        ValueError: crate name is not a valid kebab-case Rust package name

    Examples:
        >>> check_crate_name("valid-crate-name")
        >>> check_crate_name("valid_crate_name")
        Traceback (most recent call last):
        ...
        ValueError: crate_name='valid_crate_name' is not a kebab-case Rust package name.
        >>> check_crate_name("invalid crate name")
        Traceback (most recent call last):
        ...
        ValueError: crate_name='invalid crate name' is not a kebab-case Rust package name.
        >>> check_crate_name("trailing-")
        Traceback (most recent call last):
        ...
        ValueError: crate_name='trailing-' is not a kebab-case Rust package name.
        >>> check_crate_name("match")
        Traceback (most recent call last):
        ...
        ValueError: crate_name='match' is a Rust keyword and cannot be used as a crate name.
        >>> check_crate_name("proc-macro")
        Traceback (most recent call last):
        ...
        ValueError: crate_name='proc-macro' is reserved and cannot be used as a crate name.
        >>> check_crate_name("")
        Traceback (most recent call last):
        ...
        ValueError: Crate name cannot be empty.
    """
    if not crate_name:
        raise ValueError("Crate name cannot be empty.")

    identifier = crate_name.replace("-", "_")

    if identifier in RUST_KEYWORDS:
        raise ValueError(f"{crate_name=} is a Rust keyword and cannot be used as a crate name.")

    if identifier in RESERVED_CRATE_NAMES:
        raise ValueError(f"{crate_name=} is reserved and cannot be used as a crate name.")

    if not re.fullmatch(CRATE_REGEX, crate_name):
        raise ValueError(f"{crate_name=} is not a kebab-case Rust package name.")


def check_github_username(github_username: str) -> None:
    """Check that a GitHub username was provided and is one GitHub would accept.

    `project_url` embeds it, and lands in `Cargo.toml` unescaped.

    Args:
        github_username: GitHub username to check

    Raises:
        ValueError: username is blank, or not a valid GitHub user or organization name

    Examples:
        >>> check_github_username("octocat")
        >>> check_github_username("my-org")
        >>> check_github_username("")
        Traceback (most recent call last):
        ...
        ValueError: github_username cannot be empty.
        >>> check_github_username("   ")
        Traceback (most recent call last):
        ...
        ValueError: github_username cannot be empty.
        >>> check_github_username('oct"cat')
        Traceback (most recent call last):
        ...
        ValueError: github_username='oct"cat' is not a valid GitHub user or organization name.
        >>> check_github_username("-octocat")
        Traceback (most recent call last):
        ...
        ValueError: github_username='-octocat' is not a valid GitHub user or organization name.
    """
    if not github_username.strip():
        raise ValueError("github_username cannot be empty.")
    if not re.fullmatch(GITHUB_USERNAME_REGEX, github_username):
        raise ValueError(f"{github_username=} is not a valid GitHub user or organization name.")


def check_project_url(project_url: str) -> None:
    """Check that the project URL is an HTTPS URL with a host and a path.

    `Cargo.toml` embeds it as `repository`, unescaped, and `git_add_remote` splits it into host
    and path to build the `git@` form of the `origin` remote.

    Args:
        project_url: repository URL to check

    Raises:
        ValueError: URL contains a quote or backslash, or is not `https://<host>/<path>`

    Examples:
        >>> check_project_url("https://github.com/octocat/spam")
        >>> check_project_url("https://github.com")
        Traceback (most recent call last):
        ...
        ValueError: project_url='https://github.com' is not an https:// URL with a host and path.
        >>> check_project_url("git@github.com:o/s")
        Traceback (most recent call last):
        ...
        ValueError: project_url='git@github.com:o/s' is not an https:// URL with a host and path.
        >>> check_project_url('https://github.com/o/s"')
        Traceback (most recent call last):
        ...
        ValueError: project_url cannot contain quotes or backslashes.
    """
    check_toml_string("project_url", project_url)
    if not re.fullmatch(PROJECT_URL_REGEX, project_url):
        raise ValueError(f"{project_url=} is not an https:// URL with a host and path.")


def check_author_name(author_name: str) -> None:
    """Check that an author name was provided, since `Cargo.toml` and `LICENSE` embed it.

    Args:
        author_name: author name to check

    Raises:
        ValueError: name is blank

    Examples:
        >>> check_author_name("Jane Doe")
        >>> check_author_name("")
        Traceback (most recent call last):
        ...
        ValueError: author_name cannot be empty.
        >>> check_author_name("   ")
        Traceback (most recent call last):
        ...
        ValueError: author_name cannot be empty.
    """
    if not author_name.strip():
        raise ValueError("author_name cannot be empty.")


def check_release_compatibility(crate_type: str, release_ci: str, license_name: str) -> None:
    """Reject option combinations that cannot produce a working project.

    Args:
        crate_type: workspace layout
        release_ci: selected release workflow
        license_name: selected license

    Raises:
        ValueError: combination cannot work after generation

    Examples:
        >>> check_release_compatibility("both", "binaries", "MIT")
        >>> check_release_compatibility("lib", "None", "None")
        >>> check_release_compatibility("lib", "binaries", "MIT")
        Traceback (most recent call last):
        ...
        ValueError: release_ci='binaries' requires crate_type='both'; lib workspaces have no CLI.
        >>> check_release_compatibility("both", "crates.io", "None")
        Traceback (most recent call last):
        ...
        ValueError: release_ci='crates.io' requires an open-source license; 'None' is proprietary.
    """
    if crate_type == "lib" and release_ci == "binaries":
        raise ValueError(
            "release_ci='binaries' requires crate_type='both'; lib workspaces have no CLI."
        )
    if license_name == "None" and release_ci == "crates.io":
        raise ValueError(
            "release_ci='crates.io' requires an open-source license; 'None' is proprietary."
        )


def check_interop_compatibility(
    python_interop: str, release_ci: str, python_dependencies: str
) -> None:
    """Reject option combinations the selected interop direction cannot support.

    Args:
        python_interop: selected Python interop direction
        release_ci: selected release workflow
        python_dependencies: space-separated Python packages

    Raises:
        ValueError: combination cannot work after generation

    Examples:
        >>> check_interop_compatibility("embedded", "None", "numpy")
        >>> check_interop_compatibility("extension", "pypi", "numpy")
        >>> check_interop_compatibility("none", "binaries", "")
        >>> check_interop_compatibility("embedded", "pypi", "")
        Traceback (most recent call last):
        ...
        ValueError: release_ci='pypi' requires python_interop='extension'; only it builds a wheel.
        >>> check_interop_compatibility("none", "None", "numpy")
        Traceback (most recent call last):
        ...
        ValueError: python_interop='none' requires empty python_dependencies; nothing imports them.
    """
    if release_ci == "pypi" and python_interop != "extension":
        raise ValueError(
            "release_ci='pypi' requires python_interop='extension'; only it builds a wheel."
        )
    if python_interop == "none" and python_dependencies.strip():
        raise ValueError(
            "python_interop='none' requires empty python_dependencies; nothing imports them."
        )


def check_toml_string(name: str, value: str) -> None:
    r"""Check that a value survives being written into a basic TOML string.

    `project_name` (the description fallback), `author_name`, and `description` all land in
    `Cargo.toml` between double quotes, unescaped.

    Args:
        name: option being checked, for the error message
        value: option value to check

    Raises:
        ValueError: value contains a character that would break `Cargo.toml`

    Examples:
        >>> check_toml_string("description", "")
        >>> check_toml_string("description", "Scores things, quickly")
        >>> check_toml_string("description", 'Scores "things"')
        Traceback (most recent call last):
        ...
        ValueError: description cannot contain quotes or backslashes.
        >>> check_toml_string("author_name", "Jane \\ Doe")
        Traceback (most recent call last):
        ...
        ValueError: author_name cannot contain quotes or backslashes.
    """
    if set(value) & {'"', "\\"}:
        raise ValueError(f"{name} cannot contain quotes or backslashes.")


def check_keywords(keywords: str) -> None:
    """Check that the keywords are ones crates.io will accept, if any were given.

    Args:
        keywords: space-separated keywords to check

    Raises:
        ValueError: keyword is malformed or too long, or too many were given

    Examples:
        >>> check_keywords("")
        >>> check_keywords("pyo3 embedding")
        >>> check_keywords("a b c d e f")
        Traceback (most recent call last):
        ...
        ValueError: crates.io allows at most 5 keywords; 6 given.
        >>> check_keywords("py.o3")
        Traceback (most recent call last):
        ...
        ValueError: keyword='py.o3' is not a valid crates.io keyword.
        >>> check_keywords("-embedding")
        Traceback (most recent call last):
        ...
        ValueError: keyword='-embedding' is not a valid crates.io keyword.
        >>> check_keywords("interprocedural-optimization")
        Traceback (most recent call last):
        ...
        ValueError: keyword='interprocedural-optimization' exceeds 20 characters.
    """
    if not (words := keywords.split()):
        return

    if len(words) > KEYWORD_MAX_COUNT:
        raise ValueError(
            f"crates.io allows at most {KEYWORD_MAX_COUNT} keywords; {len(words)} given."
        )

    for keyword in words:
        if len(keyword) > KEYWORD_MAX_LENGTH:
            raise ValueError(f"{keyword=} exceeds {KEYWORD_MAX_LENGTH} characters.")
        if not re.fullmatch(KEYWORD_REGEX, keyword):
            raise ValueError(f"{keyword=} is not a valid crates.io keyword.")


def check_publish_metadata(release_ci: str, description: str, keywords: str) -> None:
    """Require the metadata crates.io publishes, when a crates.io release was selected.

    Without these the crate publishes under the template's placeholder metadata, which cannot be
    corrected in place: a published version's metadata is immutable.

    Args:
        release_ci: selected release workflow
        description: crate description
        keywords: space-separated crates.io keywords

    Raises:
        ValueError: metadata is missing for a crates.io release

    Examples:
        >>> check_publish_metadata("None", "", "")
        >>> check_publish_metadata("crates.io", "Scores things", "scoring")
        >>> check_publish_metadata("crates.io", "", "scoring")
        Traceback (most recent call last):
        ...
        ValueError: release_ci='crates.io' requires a description; it is published with the crate.
        >>> check_publish_metadata("crates.io", "Scores things", "  ")
        Traceback (most recent call last):
        ...
        ValueError: release_ci='crates.io' requires keywords; they are published with the crate.
    """
    if release_ci != "crates.io":
        return

    if not description.strip():
        raise ValueError(f"{release_ci=} requires a description; it is published with the crate.")
    if not keywords.strip():
        raise ValueError(f"{release_ci=} requires keywords; they are published with the crate.")


if __name__ == "__main__":
    main()
