"""Generate a deterministic two-page test PDF for parser testing."""

import textwrap
from pathlib import Path

import fitz  # PyMuPDF


def make_sample_pdf(output_path: Path) -> None:
    doc = fitz.open()
    page_w, page_h = 612, 792  # US Letter

    # --- Page 1: title, abstract, two-column body ---
    page1 = doc.new_page(width=page_w, height=page_h)

    title = "Attention Is All You Need: A Sample Paper for Testing"
    abstract_text = (
        "Abstract. We propose a novel approach to attention mechanisms that improves "
        "accuracy by 4.1 points over the previous state-of-the-art. Our method achieves "
        "87.4% on the benchmark while reducing computational cost by 30%."
    )

    col1 = (
        "1. Introduction\n"
        "Deep learning has transformed natural language processing. The Transformer "
        "architecture introduced self-attention as a core building block. However, "
        "standard attention scales quadratically with sequence length, limiting its "
        "application to long documents and high-resolution images. Recent work has "
        "explored sparse attention patterns and kernel-based approximations.\n\n"
        "2. Related Work\n"
        "Several approaches address the quadratic complexity of attention. Sparse "
        "attention restricts the attention pattern to local windows or predefined "
        "patterns. Linformer projects keys and values to a lower dimension. "
        "Performer uses random features to approximate softmax attention."
    )

    col2 = (
        "3. Method\n"
        "We introduce grouped-query attention with dynamic head selection. "
        "Given an input sequence X of length n, we compute queries Q, keys K, "
        "and values V through learned linear projections. The attention output "
        "for head h is: Attention(Q_h, K_h, V_h) = softmax(Q_h K_h^T / sqrt(d_k)) V_h.\n\n"
        "Our key insight is that not all heads need to attend to all positions. "
        "We learn a gating function that dynamically selects which heads are "
        "active for each input based on a lightweight relevance score. "
        "Figure 1 illustrates the overall architecture.\n\n"
        "Figure 1: Overview of the dynamic head selection mechanism. The gating "
        "module (shown in green) filters inactive attention heads based on "
        "input-dependent relevance scores."
    )

    # Title
    page1.insert_text((72, 72), title, fontsize=14, fontname="Helvetica-Bold")
    # Abstract
    rect = fitz.Rect(72, 110, page_w - 72, 200)
    page1.insert_textbox(rect, abstract_text, fontsize=10, fontname="Helvetica")
    # Two columns
    col1_rect = fitz.Rect(72, 220, 310, 700)
    col2_rect = fitz.Rect(340, 220, page_w - 72, 700)
    page1.insert_textbox(col1_rect, col1, fontsize=9, fontname="Helvetica")
    page1.insert_textbox(col2_rect, col2, fontsize=9, fontname="Helvetica")

    # --- Page 2: experiments, results, limitations ---
    page2 = doc.new_page(width=page_w, height=page_h)

    experiments = textwrap.dedent("""\
        4. Experiments

        We evaluate on three standard benchmarks: CIFAR-100, ImageNet-1K, and
        WMT-14 English-to-German translation. Our implementation uses PyTorch 2.0
        and trains on 8 NVIDIA A100 GPUs for 72 hours.

        Table 1: Comparison with baselines on ImageNet-1K.
        Method              Top-1 Acc (%)   FLOPs (G)
        Baseline A          82.1            12.4
        Baseline B          83.5            10.1
        Ours                87.4             7.2

        Our method achieves 87.4% top-1 accuracy, outperforming Baseline B by 3.9
        points while using 29% fewer FLOPs. The improvement is most pronounced
        on hard examples where standard attention fails to focus on relevant regions.

        5. Ablation Study

        We ablate two key design choices. Removing dynamic head selection drops
        accuracy to 83.9%, confirming its importance. Using fixed gating instead
        of learned gating reduces accuracy by 1.7 points.

        6. Limitations

        Our method has several limitations. Dynamic head selection introduces
        additional hyperparameters that require tuning per dataset. The gating
        module adds 5% overhead in wall-clock time despite the FLOP reduction.
        We only evaluate on image classification and machine translation;
        results may differ on other domains. Additionally, our largest model
        configuration requires 8 GPUs, which may not be accessible to all
        researchers.
        """)

    rect = fitz.Rect(72, 72, page_w - 72, page_h - 72)
    page2.insert_textbox(rect, experiments, fontsize=10, fontname="Helvetica")

    doc.save(str(output_path))
    doc.close()
