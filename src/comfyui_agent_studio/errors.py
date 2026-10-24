class StudioError(RuntimeError):
    """Base error with a user-facing message."""


class ConfigurationError(StudioError):
    pass


class ComfyUnavailableError(StudioError):
    pass


class WorkflowValidationError(StudioError):
    pass


class JobError(StudioError):
    pass
