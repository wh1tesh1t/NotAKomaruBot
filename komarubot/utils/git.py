from subprocess import run, CalledProcessError

class Git:
    @staticmethod
    def commit() -> str:
        """Return the short commit hash or 'None' if failed."""
        try:
            result = run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except CalledProcessError:
            return "None"

    @staticmethod
    def version() -> str:
        """Return the commit count (version) or '0' if failed."""
        try:
            result = run(
                ["git", "rev-list", "--count", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except CalledProcessError:
            return "0"
