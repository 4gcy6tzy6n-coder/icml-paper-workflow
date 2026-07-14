from typing import Any

from paperflow.models.authoring_requirements import compute_requirements_digest


def make_authoring_requirements(pdf_sha256: str) -> dict[str, Any]:
    data: dict[str, Any] = {
        "schema_version": "1.0",
        "source": {"pdf_sha256": pdf_sha256, "title": "Test Paper"},
        "use_case": {
            "scenario": "研究生组会",
            "desired_outcome": "准确理解论文贡献、结果与局限",
            "audience": {
                "role": "研究生",
                "background": "机器学习基础",
                "subject_familiarity": "intermediate",
            },
        },
        "report": {
            "required": True,
            "purpose": "论文精读报告",
            "target_pages": {"minimum": 7, "maximum": 9},
            "target_chinese_characters": {"minimum": 7000, "maximum": 10000},
            "formats": ["qmd", "docx", "report_pdf"],
            "focus_topics": ["方法", "实验", "局限"],
            "de_emphasized_topics": ["逐条复述参考文献"],
            "technical_depth": "deep",
            "narrative_preference": "证据驱动的学术叙事",
            "reading_context": "会前精读与会后复习",
        },
        "presentation": {
            "required": True,
            "purpose": "十五分钟组会汇报",
            "duration_minutes": 15,
            "target_slides": {"minimum": 13, "maximum": 15},
            "formats": ["pptx", "slides_pdf", "speaker_notes"],
            "focus_topics": ["核心结论", "关键实验", "失败分析"],
            "speaker_notes_required": True,
            "speaking_context": "现场口头汇报",
        },
        "language": {
            "locale": "zh-CN",
            "preserve_english_terms": True,
            "translation_preferences": "中文叙述并保留方法、数据集和指标英文名",
        },
        "visual": {
            "style": "清晰、克制、学术化",
            "template_path": None,
            "brand_requirements": [],
            "accessibility_requirements": ["高对比度", "不以颜色作为唯一编码"],
        },
        "evidence_policy": {
            "allow_web_research": False,
            "allow_generated_result_figures": False,
            "prefer_original_figures": True,
            "citation_expectations": "所有实质性结论追溯到论文证据块",
        },
        "deliverables": {
            "formats": [
                "qmd",
                "docx",
                "report_pdf",
                "pptx",
                "slides_pdf",
                "speaker_notes",
            ],
            "output_location": "workspace/dist/test-paper",
            "naming_requirements": "使用稳定的英文文件名",
        },
        "user_constraints": ["不得夸大论文性能"],
        "assumptions": [],
    }
    data["confirmation"] = {
        "status": "confirmed",
        "confirmed_at": "2026-07-14T12:00:00+08:00",
        "content_sha256": compute_requirements_digest(data),
    }
    return data
