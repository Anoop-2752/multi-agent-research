import re
from datetime import datetime
from fpdf import FPDF


class ReportPDF(FPDF):
    def __init__(self, topic: str):
        super().__init__()
        self.topic = topic
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(20, 20, 20)

    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, "Multi-Agent Research System", align="L")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, f"Page {self.page_no()}  ·  Generated {datetime.now().strftime('%B %d, %Y')}", align="C")


def _strip_inline_markdown(text: str) -> str:
    # Remove **bold** and *italic* markers — fpdf doesn't support inline styles
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*",     r"\1", text)
    text = re.sub(r"`(.+?)`",       r"\1", text)
    return text.strip()


def generate_pdf(report_markdown: str, topic: str) -> bytes:
    pdf = ReportPDF(topic=topic)
    pdf.add_page()

    for line in report_markdown.splitlines():
        raw = line.rstrip()
        clean = _strip_inline_markdown(raw)

        # Skip empty lines — handled as spacing between blocks
        if not clean:
            pdf.ln(3)
            continue

        # H1 — report title
        if raw.startswith("# "):
            pdf.set_font("Helvetica", "B", 20)
            pdf.set_text_color(30, 27, 75)
            pdf.multi_cell(0, 10, clean[2:])
            pdf.ln(4)

        # H2 — section headers
        elif raw.startswith("## "):
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_text_color(67, 56, 202)
            pdf.multi_cell(0, 8, clean[3:])
            pdf.set_draw_color(199, 210, 254)
            pdf.set_line_width(0.4)
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 170, pdf.get_y())
            pdf.ln(3)

        # H3 — subsection headers
        elif raw.startswith("### "):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(55, 48, 163)
            pdf.multi_cell(0, 7, clean[4:])
            pdf.ln(1)

        # Horizontal rule
        elif raw.strip() in ("---", "***", "___"):
            pdf.ln(2)
            pdf.set_draw_color(199, 210, 254)
            pdf.set_line_width(0.5)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(4)

        # Bullet points
        elif raw.lstrip().startswith(("- ", "* ", "✓ ", "• ")):
            text = re.sub(r"^[\s\-\*✓•]+", "", clean).strip()
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(30, 30, 30)
            pdf.set_x(25)
            pdf.cell(5, 6, "•")
            pdf.set_x(30)
            pdf.multi_cell(0, 6, text)

        # Numbered list items
        elif re.match(r"^\d+\.\s", raw.lstrip()):
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(30, 30, 30)
            pdf.set_x(25)
            pdf.multi_cell(0, 6, clean)

        # Regular paragraph text
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(40, 40, 40)
            pdf.set_x(20)
            pdf.multi_cell(0, 6, clean)

    return bytes(pdf.output())
