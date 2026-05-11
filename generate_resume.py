#!/usr/bin/env python3
"""Generate Rachel McDonald's resume as docs/resume.pdf."""

from fpdf import FPDF


class ResumePDF(FPDF):
    def __init__(self):
        super().__init__("P", "mm", "Letter")
        self.set_auto_page_break(auto=True, margin=10)
        self.set_margins(12, 8, 12)

    def _set(self, style="", size=10):
        self.set_font("Helvetica", style, size)

    @staticmethod
    def _a(text):
        """Replace unicode chars with ASCII equivalents."""
        return (text.replace("\u2014", "-").replace("\u2013", "-")
                .replace("\u2018", "'").replace("\u2019", "'")
                .replace("\u201c", '"').replace("\u201d", '"')
                .replace("\u2022", "-").replace("\u2026", "..."))

    def section_header(self, title):
        self.ln(1.5)
        self._set("B", 10)
        self.cell(0, 4.5, title.upper(), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0)
        self.set_line_width(0.35)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(1)

    def entry_header(self, left, right, bold=True):
        self._set("B" if bold else "", 9.5)
        self.cell(0, 4, self._a(left), new_x="LMARGIN")
        self._set("" if bold else "", 9.5)
        self.cell(0, 4, self._a(right), align="R", new_x="LMARGIN", new_y="NEXT")

    def entry_subheader(self, left, right):
        self._set("I", 9)
        self.cell(0, 4, self._a(left), new_x="LMARGIN")
        self._set("", 9)
        self.cell(0, 4, self._a(right), align="R", new_x="LMARGIN", new_y="NEXT")

    def bullet(self, text):
        self._set("", 9)
        self.cell(3, 3.8, "-")
        self.multi_cell(0, 3.8, self._a(text), new_x="LMARGIN", new_y="NEXT")
        self.ln(0.3)


def build():
    pdf = ResumePDF()
    pdf.add_page()

    # ── NAME & CONTACT ──────────────────────────────────────────────
    pdf._set("B", 15)
    pdf.cell(0, 6, "Rachel O. McDonald", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf._set("", 8.5)
    pdf.cell(
        0, 4,
        "linkedin.com/in/rachel-mcdonald-803219213  |  mcdonaldr810@gmail.com  |  210.748.7257",
        align="C", new_x="LMARGIN", new_y="NEXT",
    )

    # ── EDUCATION ────────────────────────────────────────────────────
    pdf.section_header("Education")
    pdf.entry_header("Loyola Marymount University", "Los Angeles, CA")
    pdf.entry_subheader(
        "B.B.A. Finance & Information Systems and Business Analytics, Minor in Music",
        "May 2026",
    )
    pdf._set("", 9)
    pdf.cell(0, 4, "GPA: 3.65", new_x="LMARGIN", new_y="NEXT")
    pdf._set("", 8.5)
    pdf.multi_cell(
        0, 3.8,
        "Relevant Coursework: Database Management, Developing Business Applications with SQL, "
        "Programming with Python, Systems Design & Analysis, Financial Accounting, "
        "Accounting Information for Decision Making",
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf._set("", 8.5)
    pdf.multi_cell(
        0, 3.8,
        "Involvements: Former President, Delta Sigma Pi  |  Analyst, Student Investment Fund  |  "
        "Member, Alpha Chi Omega  |  Study Abroad, Antibes, France",
        new_x="LMARGIN", new_y="NEXT",
    )

    # ── EXPERIENCE ───────────────────────────────────────────────────
    pdf.section_header("Experience")

    # Warner Chappell - Production Music
    pdf.entry_header("Warner Chappell Music", "Los Angeles, CA")
    pdf.entry_subheader("Emerging Talent Associate - Production Music", "Jan 2026 - Mar 2026")
    pdf.bullet(
        "Constructed and processed 60+ licenses across advertising, film, television, trailer, "
        "and digital media verticals."
    )
    pdf.bullet(
        "Drafted and issued invoices using GLS, ensuring accurate billing aligned with "
        "contractual terms and licensing structures."
    )
    pdf.bullet(
        "Utilized Salesforce to verify contract details, including grant of rights, usage "
        "parameters, and renewal fee calculations."
    )

    # Warner Chappell - Copyright
    pdf.entry_subheader("Emerging Talent Associate - Copyright", "Sep 2025 - Nov 2025")
    pdf.bullet(
        "Maintained data integrity for 200+ works by auditing songwriter information and "
        "publishing splits across the Company's internal database."
    )
    pdf.bullet(
        "Led the team's Grammy Nominations Initiative, developing predictive analysis models "
        "and automation strategies to streamline submission preparation and ensure compliance "
        "with eligibility criteria."
    )

    # Warner Chappell - Finance
    pdf.entry_subheader("Emerging Talent Associate - Finance", "Feb 2025 - Apr 2025")
    pdf.bullet(
        "Analyzed 75 publishing contracts by tracking songwriter advances, confirming recognition "
        "status, and identifying financial risk across deal terms."
    )
    pdf.bullet(
        "Monitored 70+ sync licensing invoices to ensure accurate payment receipt and resolve "
        "discrepancies across departments."
    )
    pdf.bullet(
        "Collaborated cross-functionally to design a 360 record deal for an emerging artist, "
        "including DCF modeling, comparable deal analysis, tour/album planning, and budget strategy."
    )

    # GHJ
    pdf.entry_header("GHJ", "Los Angeles, CA")
    pdf.entry_subheader("Profit Participations Intern", "Jun 2025 - Aug 2025")
    pdf.bullet(
        "Built movement schedules tracking revenue and expense fluctuations in studio statements "
        "to support forensic audit processes."
    )
    pdf.bullet(
        "Conducted agreement abstracting and statement analysis for major film and TV titles, "
        "including tracking licensing terms across 15+ Warner Bros. TV deals."
    )

    # Fender
    pdf.entry_header("Fender", "Los Angeles, CA")
    pdf.entry_subheader("Intern", "Jun - Jul 2023")
    pdf.bullet(
        "Listed and confirmed all 269 artist signature products on the company's internal "
        "tracking sheet."
    )
    pdf.bullet("Reviewed the accuracy of artist signature licensing agreements.")
    pdf.bullet(
        "Prepared a market study regarding the ESG efforts of five similarly situated "
        "organizations to aid in the board's strategic endeavors."
    )

    # ── PROJECTS ─────────────────────────────────────────────────────
    pdf.section_header("Projects")
    pdf.entry_header("Live Music Analytics Pipeline", "GitHub")
    pdf.entry_subheader(
        "End-to-End BI Pipeline  -  Python, SQL, dbt, Snowflake, Streamlit, GitHub Actions",
        "Spring 2026",
    )
    pdf.bullet(
        "Designed and built a data pipeline ingesting 1,900+ live music events from Ticketmaster, "
        "Spotify, and SeatGeek APIs into a Snowflake star schema, modeling the analytical workflows "
        "of a Sr. BI Analyst at a major ticketing platform like AXS."
    )
    pdf.bullet(
        "Authored dbt staging views, mart tables, and 17 data-quality tests to transform raw API "
        "data into a dimensional model (fact_events, dim_artists, dim_venues, dim_dates), enabling "
        "cross-source analysis of streaming demand, ticket pricing, and tour revenue."
    )
    pdf.bullet(
        "Deployed an interactive Streamlit dashboard with five analytical tabs - pricing analytics, "
        "artist demand signals, geographic event distribution, and scheduling trends - surfacing "
        "insights such as California's 2x price premium and Thursday scheduling dominance."
    )

    # ── HONORS & AWARDS ──────────────────────────────────────────────
    pdf.section_header("Honors & Awards")
    pdf._set("", 9)
    awards = [
        "Dean's List, Spring 2025 & Fall 2024",
        "Delta Sigma Pi Regional Collegian of the Year, 2025",
        "Michael Leahy CBA Scholarship Recipient, 2024",
        "NYU Music Industry Essentials Certificate (Royalty & Licensing)",
    ]
    for a in awards:
        pdf.cell(3, 3.8, "-")
        pdf.cell(0, 3.8, a, new_x="LMARGIN", new_y="NEXT")

    # ── SKILLS & LANGUAGES ───────────────────────────────────────────
    pdf.section_header("Skills & Languages")
    pdf._set("B", 9)
    pdf.cell(15, 4, "Technical: ")
    pdf._set("", 9)
    pdf.multi_cell(
        0, 4,
        "SQL  |  Python  |  dbt  |  Snowflake  |  Streamlit  |  GitHub & GitHub Actions  |  "
        "Tableau  |  Salesforce  |  Microsoft Excel, Word, Outlook, PowerPoint  |  DCF Modeling  |  "
        "Violin (10+ Years)",
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf._set("B", 9)
    pdf.cell(17, 4, "Language: ")
    pdf._set("", 9)
    pdf.cell(0, 4, "Conversational French & Mandarin", new_x="LMARGIN", new_y="NEXT")

    # ── OUTPUT ───────────────────────────────────────────────────────
    pdf.output("docs/resume.pdf")
    print("Saved to docs/resume.pdf")


if __name__ == "__main__":
    build()
