import re
from pathlib import Path

import fitz  # type: ignore[import-untyped]

from paperflow.models.common import AssetType
from paperflow.models.document import DocumentAsset, ParsedDocument

_CAPTION_PATTERN = re.compile(
    r"^\s*(Figure|Fig\.?|Table)\s*(\d+)[\s:：].*",
    re.IGNORECASE,
)


def extract_page_images(
    pdf_path: Path, output_dir: Path, dpi: int = 150
) -> list[Path]:
    """Render every page of a PDF as a PNG at the given DPI."""
    output_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf_path))
    paths: list[Path] = []

    for page_num in range(doc.page_count):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=dpi)
        out_path = output_dir / f"page-{page_num + 1:03d}.png"
        pix.save(str(out_path))
        paths.append(out_path)

    doc.close()
    return paths


class AssetExtractor:
    def __init__(self, pdf_path: Path, workspace: Path) -> None:
        self._pdf_path = pdf_path
        self._workspace = workspace

    def extract(self, document: ParsedDocument) -> list[DocumentAsset]:
        assets: list[DocumentAsset] = []
        page_images_dir = self._workspace / "assets" / "page-images"
        figures_dir = self._workspace / "assets" / "figures"
        tables_dir = self._workspace / "assets" / "tables"
        for d in (figures_dir, tables_dir):
            d.mkdir(parents=True, exist_ok=True)

        # Render page images
        page_image_paths = extract_page_images(self._pdf_path, page_images_dir, dpi=150)
        for i, img_path in enumerate(page_image_paths):
            assets.append(
                DocumentAsset(
                    id=f"page-p{i + 1:02d}",
                    asset_type=AssetType.FIGURE,
                    page=i + 1,
                    file_path=str(img_path.relative_to(self._workspace)),
                )
            )

        # Detect caption blocks
        fig_idx = 1
        tbl_idx = 1
        for block in document.blocks:
            m = _CAPTION_PATTERN.match(block.text)
            if not m:
                continue
            kind = m.group(1).lower()
            is_table = kind.startswith("table")
            asset_type = AssetType.TABLE if is_table else AssetType.FIGURE

            if is_table:
                asset_id = f"tbl-p{block.page:02d}-{tbl_idx:03d}"
                tbl_idx += 1
            else:
                asset_id = f"fig-p{block.page:02d}-{fig_idx:03d}"
                fig_idx += 1

            # Crop region: for figures, area above caption; for tables, caption + area below
            if block.bbox:
                b = block.bbox
                x0, y0, x1, y1 = float(b[0]), float(b[1]), float(b[2]), float(b[3])
                crop_bbox: tuple[float, float, float, float] = (
                    (x0, max(0.0, y0 - 100), x1, y1 + 200)
                    if is_table
                    else (x0, max(0.0, y0 - 250), x1, y0)
                )
                crop_path = self._crop_page(
                    block.page, crop_bbox, asset_type, asset_id
                )
            else:
                crop_path = None

            assets.append(
                DocumentAsset(
                    id=asset_id,
                    asset_type=asset_type,
                    page=block.page,
                    label=m.group(0).strip(),
                    caption=block.text.strip(),
                    file_path=str(crop_path.relative_to(self._workspace))
                    if crop_path
                    else str(page_image_paths[block.page - 1].relative_to(self._workspace)),
                    bbox=crop_bbox if block.bbox else None,
                )
            )

        return assets

    def _crop_page(
        self,
        page_num: int,
        bbox: tuple[float, float, float, float],
        asset_type: AssetType,
        asset_id: str,
    ) -> Path:
        doc = fitz.open(str(self._pdf_path))
        page = doc[page_num - 1]
        subdir = "figures" if asset_type == AssetType.FIGURE else "tables"
        out_path = self._workspace / "assets" / subdir / f"{asset_id}.png"

        rect = fitz.Rect(*bbox)
        rect.intersect(page.rect)
        pix = page.get_pixmap(clip=rect, dpi=150)
        pix.save(str(out_path))
        doc.close()
        return out_path
