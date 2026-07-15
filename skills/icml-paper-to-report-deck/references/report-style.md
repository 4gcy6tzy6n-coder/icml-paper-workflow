# Academic Report Style Guide

## Report Structure (15 Required Sections)

1. 论文信息 (Paper Information)
2. 执行摘要 (Executive Summary)
3. 研究背景与实际问题 (Background and Practical Problem)
4. 现有方法与关键缺口 (Existing Methods and Key Gaps)
5. 核心观点与贡献 (Core Ideas and Contributions)
6. 方法总体框架 (Method Overview)
7. 关键模块与公式解释 (Key Modules and Formula Explanations)
8. 实验设计 (Experimental Design)
9. 主要实验结果 (Main Experimental Results)
10. 消融实验与机制分析 (Ablation and Mechanism Analysis)
11. 创新性与优点 (Novelty and Strengths)
12. 局限性与潜在风险 (Limitations and Potential Risks)
13. 可复现性分析 (Reproducibility Analysis)
14. 对后续研究的启示 (Implications for Future Research)
15. 讨论问题 (Discussion Questions)
16. 证据索引 (Evidence Index)

## Writing Rules

- **Length**: Read the confirmed `report.target_chinese_characters` and
  `report.target_pages` ranges from `source/authoring-requirements.json`. A recommendation
  such as 7,000–10,000 characters or 8–12 pages has no force until accepted and persisted.
- **Intent**: Apply the confirmed report purpose, audience, focus/de-emphasis, technical
  depth, narrative preference, reading context, terminology, visual, citation, constraint,
  and assumption fields.
- **Style**: Full paragraphs, not bullet points. Explain rather than translate.
- **Technical terms**: If `language.preserve_english_terms` is true, preserve terms as
  directed. If it is false, follow `language.translation_preferences`; keep source wording
  only where evidence fidelity requires it.
- **Audience**: Use the confirmed `use_case.audience` role, background, and familiarity.
  Do not assume a graduate-student audience.
- **Visual direction**: Use confirmed `visual.style`, brand, and accessibility fields;
  template defaults are recommendations and never override those confirmed values.
- **Tone**: Objective, analytical, scholarly.

## Evidence Requirements

- Every substantive paragraph must end with an HTML comment:
  ```
  <!-- evidence: ev-p03-b002, ev-p04-b007 -->
  ```
- Figures use relative paths:
  ```
  ![Figure 2: Method overview](../assets/figures/fig-p04-001.png){#fig-method}
  ```
- Distinguish author statements from analyst inferences in prose ("the authors claim...", "we infer from the results that...").
- Include a final evidence index mapping sections to evidence IDs.

## Allowed Bullets

Bullet points are allowed **only** in:
- Paper Information section
- Discussion Questions section
- Compact experimental configuration summary tables

## Prohibited

- Do not use bullets in the main body text.
- Do not include unsupported numerical claims.
- Do not leave placeholder text (TODO, TBD, XXXX, etc.).
- Do not reference evidence IDs that do not exist in the evidence map.
