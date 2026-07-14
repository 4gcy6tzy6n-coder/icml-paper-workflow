class PaperFlowError(RuntimeError):
    exit_code = 1


class InvalidStageError(PaperFlowError):
    exit_code = 2


class ExternalToolError(PaperFlowError):
    exit_code = 3


class ValidationFailedError(PaperFlowError):
    exit_code = 4
