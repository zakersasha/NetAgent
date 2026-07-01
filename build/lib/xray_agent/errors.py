class XrayAgentError(Exception):
    """Base agent error."""


class ConfigError(XrayAgentError):
    """Raised when the Xray config cannot be read or updated safely."""


class UserLimitReached(XrayAgentError):
    """Raised when paying users reached the configured capacity."""


class UserNotFound(XrayAgentError):
    """Raised when a requested Xray client does not exist."""


class ReservedUserError(XrayAgentError):
    """Raised when an operation attempts to mutate a reserved admin client."""


class XrayCommandError(XrayAgentError):
    """Raised when Xray validation or restart fails."""
