from paperflow.config import WorkflowConfig


def test_default_config_is_v1_scope() -> None:
    config = WorkflowConfig()
    assert config.output_language == "zh-CN"
    assert config.talk_minutes == 15
    assert config.min_slides == 13
    assert config.max_slides == 15
    assert config.allow_web_research is False
    assert config.allow_generated_result_figures is False
