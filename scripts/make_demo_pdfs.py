"""Generate the FinBank demo requirement PDFs (fictional buyer; contains no claims about IOMETE).

demo/FinBank_Requirements.pdf          three text-based pages (background, numbered requirements, a small table)
demo/FinBank_Requirements_scanned.pdf  the same pages rasterised and re-embedded as image-only pages
"""

from pathlib import Path

import _bootstrap  # noqa: F401
import pymupdf
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import ListFlowable, ListItem, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT = Path(__file__).resolve().parents[1] / "demo"


def build_text_pdf(path: Path) -> None:
    ss = getSampleStyleSheet()
    body = ss["BodyText"]
    story = [
        Paragraph("FinBank — Analytics Platform Requirements", ss["Title"]),
        Paragraph("Document reference: FB-ARCH-2026-07 · Prepared by the FinBank Data Office (fictional organisation)", ss["Italic"]),
        Spacer(1, 6 * mm),
        Paragraph("1. Background", ss["Heading2"]),
        Paragraph(
            "FinBank is a mid-sized retail bank operating in three countries. Our current data warehouse is reaching its capacity limits "
            "and analysts wait hours for reports. We are evaluating modern data platforms to consolidate reporting, risk analytics and "
            "regulatory data preparation on a single platform.",
            body,
        ),
        Paragraph(
            "This document lists the requirements the selected platform must meet. It is shared with vendors for evaluation purposes only. "
            "Terms such as 'the platform' refer to the vendor's proposed solution.",
            body,
        ),
        Paragraph("2. Evaluation approach", ss["Heading2"]),
        Paragraph(
            "Vendors will be assessed against the numbered requirements in section 3 and the integration table in section 4. "
            "Responses should reference publicly available product documentation wherever possible.",
            body,
        ),
        PageBreak(),
        Paragraph("3. Requirements", ss["Heading2"]),
        ListFlowable(
            [
                ListItem(Paragraph("The platform must be deployable on-premises in FinBank's own data centres.", body)),
                ListItem(Paragraph("All customer data must remain within FinBank-controlled infrastructure at all times.", body)),
                ListItem(Paragraph("The platform must support an air-gapped deployment with no outbound internet connectivity.", body)),
                ListItem(Paragraph("The platform should be compatible with FinBank's existing data ingestion pipelines.", body)),
                ListItem(Paragraph("Access control must be granular, role-based and enforceable down to individual columns.", body)),
                ListItem(Paragraph("The platform must comply with the FinBank Internal Security Standard FBS-114.", body)),
                ListItem(
                    Paragraph("The vendor should provide an estimate of the migration effort from FinBank's existing data platform.", body)
                ),
                ListItem(Paragraph("The solution must be compliant with all applicable banking regulations.", body)),
            ],
            bulletType="1",
        ),
        PageBreak(),
        Paragraph("4. Existing ingestion landscape", ss["Heading2"]),
        Paragraph("For reference, the table below summarises FinBank's current ingestion pipelines (fictional).", body),
        Spacer(1, 3 * mm),
    ]
    table = Table(
        [
            ["Pipeline", "Source", "Frequency"],
            ["Core banking extract", "Relational database (JDBC)", "Nightly"],
            ["Card transactions", "Message queue", "Near real-time"],
            ["Risk models", "Files in object storage (Parquet)", "Daily"],
        ],
        colWidths=[55 * mm, 70 * mm, 40 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E0E7FF")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )
    story += [
        table,
        Spacer(1, 6 * mm),
        Paragraph("5. Contact", ss["Heading2"]),
        Paragraph("Questions about this document can be sent through the vendor evaluation portal.", body),
    ]
    SimpleDocTemplate(str(path), pagesize=A4, title="FinBank Requirements", author="FinBank Data Office (fictional)").build(story)


def build_scanned(src: Path, dst: Path) -> None:
    """Rasterise our own generated PDF and re-embed the pages as images (no text layer)."""
    doc = pymupdf.open(src)
    out = pymupdf.open()
    for page in doc:
        pix = page.get_pixmap(dpi=110)
        new = out.new_page(width=page.rect.width, height=page.rect.height)
        new.insert_image(new.rect, stream=pix.tobytes("png"))
    out.save(dst)
    out.close()
    doc.close()


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    text_pdf, scanned_pdf = OUT / "FinBank_Requirements.pdf", OUT / "FinBank_Requirements_scanned.pdf"
    build_text_pdf(text_pdf)
    build_scanned(text_pdf, scanned_pdf)
    for p in (text_pdf, scanned_pdf):
        d = pymupdf.open(p)
        chars = sum(len(pg.get_text("text").strip()) for pg in d)
        print(f"{p.name}: {d.page_count} pages, {chars} extractable characters")
        d.close()
