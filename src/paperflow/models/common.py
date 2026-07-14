from enum import StrEnum


class WorkflowStage(StrEnum):
    INITIALIZED = "initialized"
    PARSED = "parsed"
    IR_READY = "ir_ready"
    REPORT_READY = "report_ready"
    STORYBOARD_READY = "storyboard_ready"
    RENDERED = "rendered"
    CONTENT_QA_PASSED = "content_qa_passed"
    VISUAL_QA_PASSED = "visual_qa_passed"
    FINALIZED = "finalized"


class SourceType(StrEnum):
    AUTHOR_STATED = "author_stated"
    ANALYST_INFERRED = "analyst_inferred"


class AssetType(StrEnum):
    FIGURE = "figure"
    TABLE = "table"
    EQUATION = "equation"


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class SlideLayout(StrEnum):
    TITLE = "title"
    ASSERTION_FIGURE = "assertion_figure"
    TWO_COLUMN = "two_column"
    METHOD_FLOW = "method_flow"
    RESULT_HIGHLIGHT = "result_highlight"
    COMPARISON = "comparison"
    LIMITATIONS = "limitations"
    TAKEAWAY = "takeaway"
