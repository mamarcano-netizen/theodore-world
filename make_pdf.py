from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import re

OUTPUT = r"C:\Users\mamar\OneDrive\Desktop\TheodoresWorld_Illustrator_Brief.pdf"
INPUT  = r"C:\Users\mamar\OneDrive\Desktop\SuperTheo_Illustrator_Brief_COMPLETE.md"

# ── Colour palette ──────────────────────────────────────────────────────────
NAVY   = colors.HexColor("#1B1F3B")
LAV    = colors.HexColor("#C3A9F5")
GOLD   = colors.HexColor("#FFD166")
CORAL  = colors.HexColor("#FF6B6B")
LGREY  = colors.HexColor("#F5F5F8")
DGREY  = colors.HexColor("#444444")
WHITE  = colors.white

# ── Styles ───────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def S(name, parent="Normal", **kw):
    return ParagraphStyle(name, parent=base[parent], **kw)

styles = {
    "title":    S("title",    fontSize=22, textColor=WHITE,  fontName="Helvetica-Bold",
                              alignment=TA_CENTER, spaceAfter=4),
    "subtitle": S("subtitle", fontSize=11, textColor=LAV,    fontName="Helvetica",
                              alignment=TA_CENTER, spaceAfter=2),
    "conf":     S("conf",     fontSize=7.5,textColor=GOLD,   fontName="Helvetica-Oblique",
                              alignment=TA_CENTER, spaceAfter=14),
    "h1":       S("h1",       fontSize=14, textColor=WHITE,  fontName="Helvetica-Bold",
                              spaceBefore=14, spaceAfter=4, backColor=NAVY,
                              leftIndent=-18, rightIndent=-18,
                              borderPadding=(6,18,6,18)),
    "h2":       S("h2",       fontSize=11, textColor=NAVY,   fontName="Helvetica-Bold",
                              spaceBefore=12, spaceAfter=3,
                              borderPadding=(4,0,2,0)),
    "h3":       S("h3",       fontSize=9.5,textColor=DGREY,  fontName="Helvetica-Bold",
                              spaceBefore=8,  spaceAfter=2),
    "body":     S("body",     fontSize=9,  textColor=DGREY,  fontName="Helvetica",
                              leading=14,  spaceAfter=5),
    "bullet":   S("bullet",   fontSize=9,  textColor=DGREY,  fontName="Helvetica",
                              leftIndent=14, leading=13, spaceAfter=3,
                              bulletIndent=4),
    "check":    S("check",    fontSize=9,  textColor=NAVY,   fontName="Helvetica",
                              leftIndent=14, leading=13, spaceAfter=3),
    "quote":    S("quote",    fontSize=8.5,textColor=NAVY,   fontName="Helvetica-Oblique",
                              leftIndent=14, rightIndent=14, leading=13,
                              spaceAfter=6,  spaceBefore=4,
                              backColor=colors.HexColor("#EFF4FF"),
                              borderPadding=(6,10,6,10)),
    "table_h":  S("table_h",  fontSize=8.5,textColor=WHITE,  fontName="Helvetica-Bold",
                              alignment=TA_CENTER),
    "table_c":  S("table_c",  fontSize=8.5,textColor=DGREY,  fontName="Helvetica",
                              leading=12),
    "footer":   S("footer",   fontSize=7,  textColor=colors.HexColor("#888888"),
                              fontName="Helvetica-Oblique", alignment=TA_CENTER),
}

TABLE_STYLE = TableStyle([
    ("BACKGROUND",  (0,0),(-1,0), NAVY),
    ("TEXTCOLOR",   (0,0),(-1,0), WHITE),
    ("FONTNAME",    (0,0),(-1,0), "Helvetica-Bold"),
    ("FONTSIZE",    (0,0),(-1,-1), 8.5),
    ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, colors.HexColor("#F0F0F8")]),
    ("GRID",        (0,0),(-1,-1), 0.4, colors.HexColor("#CCCCCC")),
    ("VALIGN",      (0,0),(-1,-1), "TOP"),
    ("TOPPADDING",  (0,0),(-1,-1), 5),
    ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ("LEFTPADDING", (0,0),(-1,-1), 8),
    ("RIGHTPADDING",(0,0),(-1,-1), 8),
])

# ── Header / Footer ──────────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    w, h = letter
    # header bar
    canvas.setFillColor(NAVY)
    canvas.rect(0, h-36, w, 36, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(inch*0.5, h-22, "THEODORE'S WORLD — Illustrator Brief")
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(w - inch*0.5, h-22, "© Anthony Marcano  |  theodore-world.com")
    # footer
    canvas.setFillColor(DGREY)
    canvas.setFont("Helvetica-Oblique", 7)
    canvas.drawCentredString(w/2, 22, f"CONFIDENTIAL  —  Page {doc.page}")
    canvas.restoreState()

# ── Parse markdown → flowables ───────────────────────────────────────────────
def parse(md):
    story = []
    lines = md.split("\n")
    i = 0
    table_buf = []

    def flush_table():
        if len(table_buf) < 2:
            table_buf.clear(); return
        rows = []
        for r in table_buf:
            cols = [c.strip() for c in r.strip("|").split("|")]
            rows.append(cols)
        # remove separator row
        rows = [r for r in rows if not all(set(c)=={'|','-',' ',''} or re.match(r'^-+$',c) for c in r)]
        if not rows: table_buf.clear(); return
        ncols = max(len(r) for r in rows)
        data = []
        for ri, row in enumerate(rows):
            while len(row) < ncols: row.append("")
            st = styles["table_h"] if ri==0 else styles["table_c"]
            data.append([Paragraph(c, st) for c in row])
        col_w = (6.5*inch) / ncols
        t = Table(data, colWidths=[col_w]*ncols)
        t.setStyle(TABLE_STYLE)
        story.append(Spacer(1,6))
        story.append(t)
        story.append(Spacer(1,8))
        table_buf.clear()

    while i < len(lines):
        line = lines[i]

        # table row
        if line.strip().startswith("|"):
            table_buf.append(line)
            i+=1; continue
        else:
            if table_buf: flush_table()

        # headings
        if line.startswith("# ") and not line.startswith("## "):
            story.append(Spacer(1,10))
            story.append(Paragraph(line[2:].strip(), styles["h1"]))
            story.append(Spacer(1,4))
        elif line.startswith("## "):
            story.append(Spacer(1,6))
            story.append(HRFlowable(width="100%", thickness=1.5, color=LAV, spaceAfter=2))
            story.append(Paragraph(line[3:].strip(), styles["h2"]))
        elif line.startswith("### "):
            story.append(Paragraph(line[4:].strip(), styles["h3"]))
        # blockquote / note
        elif line.startswith("> "):
            txt = line[2:].strip()
            txt = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', txt)
            story.append(Paragraph(txt, styles["quote"]))
        # checkbox / bullet
        elif line.strip().startswith("- [ ]"):
            txt = line.strip()[5:].strip()
            txt = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', txt)
            story.append(Paragraph(f"☐  {txt}", styles["check"]))
        elif line.strip().startswith("- "):
            txt = line.strip()[2:].strip()
            txt = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', txt)
            txt = re.sub(r'\*(.+?)\*', r'<i>\1</i>', txt)
            story.append(Paragraph(f"•  {txt}", styles["bullet"]))
        # hr
        elif line.strip().startswith("---"):
            story.append(Spacer(1,4))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC")))
            story.append(Spacer(1,4))
        # code block (skip)
        elif line.strip().startswith("```"):
            pass
        # blank
        elif line.strip() == "":
            story.append(Spacer(1,4))
        # normal paragraph
        else:
            txt = line.strip()
            if not txt: i+=1; continue
            txt = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', txt)
            txt = re.sub(r'\*(.+?)\*',     r'<i>\1</i>',  txt)
            story.append(Paragraph(txt, styles["body"]))

        i += 1

    if table_buf: flush_table()
    return story

# ── Cover page ───────────────────────────────────────────────────────────────
def cover():
    elems = []
    elems.append(Spacer(1, 1.6*inch))
    # Gold bar
    elems.append(Table([[""]], colWidths=[6.5*inch], rowHeights=[6]))
    elems[-1].setStyle(TableStyle([("BACKGROUND",(0,0),(0,0),GOLD),("LINEABOVE",(0,0),(0,0),0,GOLD)]))
    elems.append(Spacer(1, 0.3*inch))
    elems.append(Paragraph("THEODORE'S WORLD", styles["title"]))
    elems.append(Paragraph("Visual Character Bible", styles["subtitle"]))
    elems.append(Paragraph("Official Illustrator Commission Brief", styles["subtitle"]))
    elems.append(Spacer(1, 0.2*inch))
    elems.append(Table([[""]], colWidths=[6.5*inch], rowHeights=[6]))
    elems[-1].setStyle(TableStyle([("BACKGROUND",(0,0),(0,0),GOLD)]))
    elems.append(Spacer(1, 0.4*inch))
    elems.append(Paragraph("Prepared by: Anthony Marcano", styles["conf"]))
    elems.append(Paragraph("theodore-world.com", styles["conf"]))
    elems.append(Spacer(1, 1.0*inch))
    elems.append(Paragraph(
        "CONFIDENTIAL — This document and all content within it is the exclusive "
        "intellectual property of Anthony Marcano © 2024–2025. Do not share or "
        "reproduce without written permission.",
        styles["quote"]))
    elems.append(PageBreak())
    return elems

# ── Build PDF ────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=letter,
    leftMargin=inch*0.85,
    rightMargin=inch*0.85,
    topMargin=inch*0.75,
    bottomMargin=inch*0.6,
)

with open(INPUT, "r", encoding="utf-8") as f:
    md = f.read()

# strip the very first heading (we use the cover instead)
md = re.sub(r'^# THEODORE.*?\n={3,}\n', '', md, flags=re.DOTALL)

story = cover()
story += parse(md)
story.append(Spacer(1, 0.3*inch))
story.append(HRFlowable(width="100%", thickness=1, color=GOLD))
story.append(Spacer(1, 8))
story.append(Paragraph(
    "© Anthony Marcano — Theodore's World 2024–2025. All rights reserved. "
    "This document is confidential. Unauthorized sharing is prohibited.",
    styles["footer"]))

doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(f"PDF saved: {OUTPUT}")
