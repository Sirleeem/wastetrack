"""
Generate WasteTrack final-year project report (PDF) following ATBU Bauchi
Department of Computer Science guidelines:
General_Project_Guidelines_Prelimary_Pages,_Chapters_&_References.pdf
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

DOCS = Path(__file__).resolve().parent
FIG_DIR = DOCS / "figures"
OUT = DOCS / "WasteTrack_Final_Year_Project_Report.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

PAGE_W, PAGE_H = A4
# Guideline A.2: double line space; 1 inch left, half inch right
MARGIN_LEFT = 1.0 * inch
MARGIN_RIGHT = 0.5 * inch
MARGIN_TOP = 1.0 * inch
MARGIN_BOTTOM = 1.0 * inch
CONTENT_WIDTH = PAGE_W - MARGIN_LEFT - MARGIN_RIGHT

# Double spacing for 12 pt (2 x 12)
DOUBLE = 24
SINGLE = 14

# Fill blanks before hard bind if known
STUDENT_SURNAME_FIRST = "ABDULRASHEED, AHMAD ABDULWAHAB"
STUDENT_NAME = "AHMAD ABDULWAHAB ABDULRASHEED"
STUDENT_REG = "20/55381U/1"
SUPERVISOR = "AUWAL AMINU"
DEGREE = "BACHELOR OF TECHNOLOGY (B.TECH. HONS) IN COMPUTER SCIENCE"
MONTH_YEAR = "JULY, 2026"
TITLE = (
    "DESIGN AND IMPLEMENTATION OF A WASTE MANAGEMENT "
    "REPORTING AND COLLECTION SYSTEM"
)


def fig_image(name: str, max_height_cm: float = 15.5):
    path = FIG_DIR / name
    if not path.exists():
        return None
    img = Image(str(path))
    aspect = img.imageHeight / float(img.imageWidth) if img.imageWidth else 0.6
    w = CONTENT_WIDTH * 0.98
    h = w * aspect
    max_h = max_height_cm * cm
    if h > max_h:
        h = max_h
        w = h / aspect if aspect else w
    img.drawWidth = w
    img.drawHeight = h
    return img


def styles():
    base = getSampleStyleSheet()
    s = {
        "title": ParagraphStyle(
            "T", parent=base["Normal"], fontName="Times-Bold", fontSize=14,
            leading=DOUBLE, alignment=TA_CENTER, spaceAfter=10,
        ),
        "center": ParagraphStyle(
            "C", parent=base["Normal"], fontName="Times-Roman", fontSize=12,
            leading=DOUBLE, alignment=TA_CENTER, spaceAfter=6,
        ),
        "center_bold": ParagraphStyle(
            "CB", parent=base["Normal"], fontName="Times-Bold", fontSize=12,
            leading=DOUBLE, alignment=TA_CENTER, spaceAfter=6,
        ),
        "cover_line": ParagraphStyle(
            "CL", parent=base["Normal"], fontName="Times-Bold", fontSize=13,
            leading=DOUBLE, alignment=TA_CENTER, spaceAfter=10, textColor=colors.Color(0.55, 0.42, 0.08),
        ),
        "h1": ParagraphStyle(
            "H1", parent=base["Normal"], fontName="Times-Bold", fontSize=14,
            leading=DOUBLE, alignment=TA_CENTER, spaceBefore=6, spaceAfter=14,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Normal"], fontName="Times-Bold", fontSize=12,
            leading=DOUBLE, alignment=TA_LEFT, spaceBefore=14, spaceAfter=8,
        ),
        "h3": ParagraphStyle(
            "H3", parent=base["Normal"], fontName="Times-Bold", fontSize=12,
            leading=DOUBLE, alignment=TA_LEFT, spaceBefore=10, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "B", parent=base["Normal"], fontName="Times-Roman", fontSize=12,
            leading=DOUBLE, alignment=TA_JUSTIFY, spaceAfter=10, firstLineIndent=18,
        ),
        "body_ni": ParagraphStyle(
            "BN", parent=base["Normal"], fontName="Times-Roman", fontSize=12,
            leading=DOUBLE, alignment=TA_JUSTIFY, spaceAfter=10, firstLineIndent=0,
        ),
        # Guideline 8: abstract double spaced and not indented; max 150 words
        "abstract": ParagraphStyle(
            "Abs", parent=base["Normal"], fontName="Times-Roman", fontSize=12,
            leading=DOUBLE, alignment=TA_JUSTIFY, spaceAfter=10, firstLineIndent=0,
        ),
        "caption": ParagraphStyle(
            "Cap", parent=base["Normal"], fontName="Times-Bold", fontSize=11,
            leading=SINGLE, alignment=TA_CENTER, spaceBefore=6, spaceAfter=12,
        ),
        "toc": ParagraphStyle(
            "TOC", parent=base["Normal"], fontName="Times-Roman", fontSize=12,
            leading=DOUBLE, alignment=TA_LEFT, spaceAfter=2,
        ),
        "list_item": ParagraphStyle(
            "LI", parent=base["Normal"], fontName="Times-Roman", fontSize=12,
            leading=DOUBLE, alignment=TA_LEFT, spaceAfter=2, leftIndent=0,
        ),
        "list_item_wrap": ParagraphStyle(
            "LIW", parent=base["Normal"], fontName="Times-Roman", fontSize=12,
            leading=SINGLE, alignment=TA_LEFT, spaceAfter=6, leftIndent=18,
        ),
        "ref": ParagraphStyle(
            "R", parent=base["Normal"], fontName="Times-Roman", fontSize=12,
            leading=DOUBLE, alignment=TA_LEFT, spaceAfter=12,
            leftIndent=36, firstLineIndent=-36,
        ),
        "bullet": ParagraphStyle(
            "Bu", parent=base["Normal"], fontName="Times-Roman", fontSize=12,
            leading=DOUBLE, alignment=TA_JUSTIFY, spaceAfter=6,
            leftIndent=24, firstLineIndent=0,
        ),
        "sign": ParagraphStyle(
            "SG", parent=base["Normal"], fontName="Times-Roman", fontSize=12,
            leading=DOUBLE, alignment=TA_LEFT, spaceAfter=4,
        ),
    }
    return s


def p(text: str, style):
    return Paragraph(text, style)


def bullets(items, S):
    return [Paragraph(f"•  {item}", S["bullet"]) for item in items]


def add_figure(story, filename: str, caption: str, S):
    img = fig_image(filename)
    if img:
        story.append(Spacer(1, 6))
        story.append(img)
        story.append(p(caption, S["caption"]))
        return True
    return False


def table_style():
    return TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )


def build():
    S = styles()
    story = []

    # ========== 1. COVER PAGE (capital letters) ==========
    story.append(Spacer(1, 2.2 * cm))
    story.append(p(TITLE, S["cover_line"]))
    story.append(Spacer(1, 1.8 * cm))
    story.append(p("BY", S["center"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(p(STUDENT_SURNAME_FIRST, S["cover_line"]))
    story.append(Spacer(1, 2.5 * cm))
    story.append(p(MONTH_YEAR, S["cover_line"]))
    story.append(PageBreak())

    # ========== 2. FLY LEAF (blank) ==========
    story.append(Spacer(1, 1))
    story.append(PageBreak())

    # ========== 3. TITLE PAGE ==========
    story.append(Spacer(1, 1.0 * cm))
    story.append(p(TITLE, S["title"]))
    story.append(Spacer(1, 0.8 * cm))
    story.append(p("BY", S["center"]))
    story.append(p(STUDENT_NAME, S["center_bold"]))
    story.append(p(f"REG. NO.: {STUDENT_REG}", S["center_bold"]))
    story.append(Spacer(1, 0.8 * cm))
    story.append(
        p(
            "A PROJECT SUBMITTED TO THE DEPARTMENT OF COMPUTER SCIENCE, "
            "ABUBAKAR TAFAWA BALEWA UNIVERSITY, IN PARTIAL FULFILLMENT OF THE "
            f"REQUIREMENT FOR THE AWARD OF THE DEGREE OF {DEGREE}",
            S["center"],
        )
    )
    story.append(Spacer(1, 0.8 * cm))
    story.append(p("DEPARTMENT OF COMPUTER SCIENCE", S["center_bold"]))
    story.append(p("FACULTY OF SCIENCE", S["center_bold"]))
    story.append(p("ABUBAKAR TAFAWA BALEWA UNIVERSITY, BAUCHI", S["center_bold"]))
    story.append(Spacer(1, 0.8 * cm))
    story.append(p(MONTH_YEAR, S["center_bold"]))
    story.append(PageBreak())

    # ========== 4. DECLARATION ==========
    story.append(p("DECLARATION", S["h1"]))
    story.append(
        p(
            f"I hereby declared that this work is the product of my research effort, undertaken "
            f"under the supervision of {SUPERVISOR} and has not been presented and will not be "
            f"presented elsewhere for the award of any degree or certificate. All sources have "
            f"been duly acknowledged.",
            S["body_ni"],
        )
    )
    story.append(Spacer(1, 1.5 * cm))
    data_dec = [
        [
            Paragraph("_______________________<br/>Name of student", S["sign"]),
            Paragraph("_______________________<br/>Signature", S["sign"]),
            Paragraph("_______________________<br/>Date", S["sign"]),
        ]
    ]
    t_dec = Table(data_dec, colWidths=[CONTENT_WIDTH / 3.0] * 3)
    t_dec.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(t_dec)
    story.append(PageBreak())

    # ========== 5. CERTIFICATION / APPROVAL ==========
    story.append(p("CERTIFICATION / APPROVAL", S["h1"]))
    story.append(
        p(
            f'This is to certified that the project entitled "{TITLE}" by {STUDENT_NAME} '
            f"was carried out under my/our supervisor(s):",
            S["body_ni"],
        )
    )
    story.append(Spacer(1, 1.2 * cm))
    story.append(
        p(
            "_______________________________<br/>"
            "(Name and Signature)<br/>"
            "Project Supervisor I"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "____________________ Date",
            S["sign"],
        )
    )
    story.append(Spacer(1, 1.2 * cm))
    story.append(
        p(
            "_______________________________<br/>"
            "(Name and Signature)<br/>"
            "Head of Department"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "____________________ Date",
            S["sign"],
        )
    )
    story.append(Spacer(1, 1.2 * cm))
    story.append(
        p(
            "_______________________________<br/>"
            "(Name and Signature)<br/>"
            "External Examiner"
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            "____________________ Date",
            S["sign"],
        )
    )
    story.append(PageBreak())

    # ========== 6. ACKNOWLEDGMENT ==========
    story.append(p("ACKNOWLEDGMENT", S["h1"]))
    story.append(
        p(
            "I thank Almighty God for the strength to complete this project. I am grateful to my "
            "project supervisor for guidance and corrections, and to the lecturers in the Department "
            "of Computer Science, Abubakar Tafawa Balewa University, Bauchi. I also thank colleagues "
            "and family members who tested early versions of the system and encouraged me throughout "
            "the work. Any errors that remain are mine.",
            S["body_ni"],
        )
    )
    story.append(PageBreak())

    # ========== 7. DEDICATION ==========
    story.append(p("DEDICATION", S["h1"]))
    story.append(
        p(
            "This work is dedicated to my family, whose support made the study possible, and to the "
            "people of Bauchi State who live with the daily challenges of refuse collection that this "
            "project tries to address in a practical way.",
            S["body_ni"],
        )
    )
    story.append(PageBreak())

    # ========== 8. ABSTRACT (<=150 words, double spaced, not indented) ==========
    story.append(p("ABSTRACT", S["h1"]))
    story.append(
        p(
            "Poor waste reporting and weak collection planning remain common in Bauchi and similar "
            "Nigerian towns. Complaints are often made by phone or word of mouth, with little shared "
            "status tracking. This project designed and implemented WasteTrack, a waste management "
            "reporting and collection system. Residents submit geolocated reports with "
            "optional photos. Administrators verify, assign and schedule work, while officers update "
            "field tasks. A Haversine nearest-neighbour helper recommends a collection order. "
            "Functional tests and a live deployment showed that the system can organise complaints "
            "into trackable cases without IoT sensors. Limits include simple routing and dependence "
            "on user map pins.",
            S["abstract"],
        )
    )
    story.append(
        p(
            "<b>Keywords:</b> waste management, web application, geolocation, Flask, route "
            "optimization, Bauchi",
            S["abstract"],
        )
    )
    story.append(PageBreak())

    # ========== CONTENTS ==========
    story.append(p("CONTENTS", S["h1"]))
    toc = [
        "Cover Page",
        "Fly Leaf",
        "Title Page",
        "Declaration",
        "Certification / Approval",
        "Acknowledgment",
        "Dedication",
        "Abstract",
        "Contents",
        "List of Tables",
        "List of Figures",
        "List of Plates",
        "List of Appendices",
        "Abbreviations, Definitions, Glossaries and Symbols",
        "",
        "CHAPTER ONE: INTRODUCTION",
        "1.1 Background of the Study",
        "1.2 Statement of the Problem",
        "1.3 Aim and Objectives",
        "1.4 Significance / Justification of the Study",
        "1.5 Scope and Limitation",
        "",
        "CHAPTER TWO: LITERATURE REVIEW",
        "2.1 Introduction",
        "2.2 Conceptual Review of Waste Management Systems",
        "2.3 Smart Waste Reporting and Digital Coordination",
        "2.4 Route Optimization Techniques",
        "2.5 Related Works",
        "2.6 Summary of Literature Gap",
        "",
        "CHAPTER THREE: METHODOLOGY",
        "3.1 Introduction",
        "3.2 Study Design",
        "3.3 Analysis of the Existing System",
        "3.4 Requirements Specification",
        "3.5 System Architecture and Design",
        "3.6 Development Tools and Implementation Approach",
        "3.7 Data Collection and Evaluation Methods",
        "",
        "CHAPTER FOUR: RESULTS AND DISCUSSION",
        "4.1 Introduction",
        "4.2 System Implementation Results",
        "4.3 Functional Testing Results",
        "4.4 Discussion of Findings",
        "4.5 System Screenshots",
        "",
        "CHAPTER FIVE: SUMMARY, CONCLUSIONS AND RECOMMENDATIONS",
        "5.1 Summary",
        "5.2 Conclusions",
        "5.3 Recommendations",
        "",
        "References",
        "Appendices",
    ]
    for t in toc:
        if not t:
            story.append(Spacer(1, 4))
        else:
            story.append(p(t, S["toc"]))
    story.append(PageBreak())

    # ========== LIST OF TABLES ==========
    story.append(p("LIST OF TABLES", S["h1"]))
    for item in [
        "Table 3.1: Functional requirements by role",
        "Table 3.2: Technology stack",
        "Table 3.3: Core database entities",
        "Table 4.1: Functional test cases summary",
        "Table 4.2: Mapping of objectives to outcomes",
    ]:
        story.append(p(item, S["list_item"]))
    story.append(PageBreak())

    # ========== LIST OF FIGURES ==========
    story.append(p("LIST OF FIGURES", S["h1"]))
    for item in [
        "Figure 3.1: High-level system architecture of WasteTrack",
        "Figure 3.2: Role-based access model",
        "Figure 3.3: Report status workflow",
        "Figure 3.4: Conceptual entity relationship (core tables)",
        "Figure 4.1: Resident report submission interface (live site)",
        "Figure 4.2: Administrator dashboard (live site)",
        "Figure 4.3: Optimization and map view (live site)",
    ]:
        story.append(p(item, S["list_item"]))
    story.append(PageBreak())

    # ========== LIST OF PLATES ==========
    story.append(p("LIST OF PLATES", S["h1"]))
    story.append(p("None.", S["body_ni"]))
    story.append(PageBreak())

    # ========== LIST OF APPENDICES ==========
    story.append(p("LIST OF APPENDICES", S["h1"]))
    for item in [
        "Appendix A: Sample Production Configuration",
        "Appendix B: Project Module Map",
        "Appendix C: User Guide Summary",
    ]:
        story.append(p(item, S["list_item"]))
    story.append(PageBreak())

    # ========== ABBREVIATIONS, DEFINITIONS, GLOSSARIES AND SYMBOLS ==========
    story.append(p("ABBREVIATIONS, DEFINITIONS, GLOSSARIES AND SYMBOLS", S["h1"]))
    story.append(p("Abbreviations", S["h2"]))
    abbr = [
        ("API", "Application Programming Interface"),
        ("BASEPA", "Bauchi State Environmental Protection Agency"),
        ("CSRF", "Cross-Site Request Forgery"),
        ("CSP", "Content Security Policy"),
        ("DFD", "Data Flow Diagram"),
        ("GIS", "Geographic Information System"),
        ("GPS", "Global Positioning System"),
        ("HTML", "HyperText Markup Language"),
        ("HTTP", "HyperText Transfer Protocol"),
        ("HTTPS", "HyperText Transfer Protocol Secure"),
        ("IoT", "Internet of Things"),
        ("KPI", "Key Performance Indicator"),
        ("NN", "Nearest Neighbour"),
        ("ORM", "Object-Relational Mapping"),
        ("RBAC", "Role-Based Access Control"),
        ("SQL", "Structured Query Language"),
        ("UI", "User Interface"),
        ("URL", "Uniform Resource Locator"),
        ("WSGI", "Web Server Gateway Interface"),
    ]
    for a, d in abbr:
        story.append(p(f"<b>{a}</b>  {d}", S["body_ni"]))

    story.append(p("Definitions / Glossary", S["h2"]))
    terms = [
        ("Waste report", "A digital record of a refuse issue, including category, description, location and status."),
        ("Geolocation", "Latitude and longitude that mark where a waste issue was observed."),
        ("Haversine distance", "A formula that estimates distance between two points on Earth from latitude and longitude."),
        ("Nearest-neighbour heuristic", "A simple routing method that repeatedly picks the closest remaining stop, sometimes adjusted by priority."),
        ("Status history", "A time-stamped log of status changes on a report."),
        ("Role-based access control", "A security approach that grants permissions according to user role."),
    ]
    for name, defn in terms:
        story.append(p(f"<b>{name}:</b> {defn}", S["body_ni"]))

    story.append(p("Symbols", S["h2"]))
    story.append(
        p(
            "No special mathematical symbols are used beyond standard distance notation in the "
            "optimization module (kilometres, km).",
            S["body_ni"],
        )
    )
    story.append(PageBreak())

    # ========== CHAPTER ONE ==========
    story.append(p("CHAPTER ONE", S["h1"]))
    story.append(p("INTRODUCTION", S["h1"]))

    story.append(p("1.1 Background of the Study", S["h2"]))
    story.append(
        p(
            "Waste management is a basic public service that affects how clean and healthy a "
            "community feels. As towns grow, more household and commercial refuse is produced, "
            "while collection teams often work with limited staff and vehicles. In many Nigerian "
            "urban centres, including Bauchi, people notice overflowing bins, illegal dumps or "
            "missed collection points long before the authority has a clear record of the problem "
            "(N, 2023).",
            S["body"],
        )
    )
    story.append(
        p(
            "When reporting is mostly informal, through phone calls or verbal complaints, it is hard "
            "to confirm locations, rank urgent cases, assign teams and later check how long a case "
            "took. A simple digital system can turn those complaints into records with map "
            "coordinates, categories, urgency, status history and assigned officers. Studies on "
            "smart waste systems also show growing interest in dashboards, geolocation and route "
            "helpers that reduce wasted trips (Kapadia and Mehta, 2023; Martikkala et al, 2023; "
            "Banciu et al, 2025).",
            S["body"],
        )
    )
    story.append(
        p(
            "This project develops WasteTrack: a waste management reporting and collection "
            "system. Instead of starting with costly IoT bin sensors, the work focuses "
            "on resident reporting, admin workflow, officer tasks and a light schedule-order helper "
            "that is easy to explain and demonstrate.",
            S["body"],
        )
    )

    story.append(p("1.2 Statement of the Problem", S["h2"]))
    story.append(
        p(
            "In many communities, waste reporting and collection still lack a shared digital record. "
            "Issues are not stored in one place, and pickup work is not always planned with location, "
            "urgency and status in mind. The result is delayed response, repeated or missed stops, "
            "weak tracking, low visibility for administrators and little data for spotting recurring "
            "hotspots.",
            S["body"],
        )
    )
    story.append(
        p(
            "The problem this project addresses is the lack of one system that can (i) take waste "
            "reports from residents, (ii) store location and status data in a database, (iii) help "
            "administrators assign and schedule pickups, and (iv) suggest a sensible collection order "
            "for open reports. Without that, teams continue to rely on manual coordination that is "
            "hard to track or improve.",
            S["body"],
        )
    )

    story.append(p("1.3 Aim and Objectives", S["h2"]))
    story.append(p("1.3.1 Aim", S["h3"]))
    story.append(
        p(
            "The aim of this project is to design and implement a waste management reporting "
            "and collection system that improves how community waste issues are reported, "
            "monitored, scheduled and planned for collection.",
            S["body"],
        )
    )
    story.append(p("1.3.2 Specific Objectives", S["h3"]))
    story.extend(
        bullets(
            [
                "To design a role-based web application that lets residents submit waste reports with category, description, location and optional photo evidence.",
                "To implement an administrative dashboard for viewing, verifying, assigning, scheduling and updating reported waste issues.",
                "To develop a basic route or schedule helper that groups pending reports by location, urgency and pickup plan to recommend a collection order.",
                "To evaluate the system using functional tests, usability checks and a comparison of manual versus system-assisted pickup planning.",
            ],
            S,
        )
    )

    story.append(p("1.4 Significance / Justification of the Study", S["h2"]))
    story.append(
        p(
            "Academically, the work shows practical use of software design, databases, web dashboards "
            "and a simple optimization method in an environmental information setting. Practically, "
            "residents get a clearer way to report refuse problems, and staff get a dashboard to track "
            "and close cases. For the community, faster reporting and more organised collection can "
            "reduce illegal dumping, blocked drains, odour and related health risks. For local "
            "institutions, the prototype can show waste contractors or bodies such as the Bauchi State "
            "Environmental Protection Agency (BASEPA) what a low-cost digital coordination tool might "
            "look like before larger smart-city spending.",
            S["body"],
        )
    )

    story.append(p("1.5 Scope and Limitation", S["h2"]))
    story.append(
        p(
            "The project covers design and implementation of a web prototype with resident reporting, "
            "admin dashboard, status tracking, pickup scheduling, a basic collection-order helper and "
            "summary statistics. Supported roles are resident, administrator and collection officer. "
            "The database stores reports, locations, status history, schedules and assignments.",
            S["body"],
        )
    )
    story.append(
        p(
            "The project does not include physical IoT sensors, payment systems, government identity "
            "integration, full fleet GPS tracking or city-wide production rollout. Location accuracy "
            "depends on the map pin or address entered by the user. The optimization part is a simple "
            "heuristic for academic use, not a full industrial vehicle-routing product.",
            S["body"],
        )
    )
    story.append(PageBreak())

    # ========== CHAPTER TWO ==========
    story.append(p("CHAPTER TWO", S["h1"]))
    story.append(p("LITERATURE REVIEW", S["h1"]))

    story.append(p("2.1 Introduction", S["h2"]))
    story.append(
        p(
            "This chapter reviews ideas and earlier work on digital waste management, citizen "
            "reporting, operations dashboards and route planning. The aim is to place the project "
            "in context and show the gap that a small, buildable student system can fill.",
            S["body"],
        )
    )

    story.append(p("2.2 Conceptual Review of Waste Management Systems", S["h2"]))
    story.append(
        p(
            "Waste management has moved from purely manual collection toward systems that use digital "
            "reports, sensors, dashboards and route planning. Over the last decade, smart-city research "
            "has treated waste collection as both a logistics problem and an information problem "
            "(Anagnostopoulos et al, 2017; Hannan et al, 2015). Instead of only fixed rounds, teams "
            "can use reports, bin status, urgency and location to decide where work is most needed "
            "(Kapadia and Mehta, 2023).",
            S["body"],
        )
    )
    story.append(
        p(
            "Even with these ideas, many local processes still rely on manual contact. Residents may "
            "report through unofficial channels, while staff keep notes on paper or spreadsheets. "
            "That causes delay and weak follow-up. One location may be reported many times without a "
            "clear status history, while another is ignored because it never entered a shared system "
            "(Hoornweg and Bhada-Tata, 2012; World Bank, 2018).",
            S["body"],
        )
    )

    story.append(p("2.3 Smart Waste Reporting and Digital Coordination", S["h2"]))
    story.append(
        p(
            "Citizen reporting apps usually collect structured fields such as category, description, "
            "photos and map location, then support verification and assignment. Work on intelligent "
            "waste collection and dynamic routing shows that planning improves when collection points "
            "are stored as structured data (Kapadia and Mehta, 2023; Kolangiammal et al, 2025).",
            S["body"],
        )
    )
    story.append(
        p(
            "Public-service dashboards often separate roles: the public submits issues, operators "
            "triage and assign, and field workers update progress. Status histories help both residents "
            "and managers see what happened. WasteTrack follows this pattern.",
            S["body"],
        )
    )

    story.append(p("2.4 Route Optimization Techniques", S["h2"]))
    story.append(
        p(
            "Vehicle routing methods range from exact mathematical models to heuristics (Buhrkal et al, "
            "2012; Tavares et al, 2009). For school projects and small pilots, nearest-neighbour and "
            "other greedy distance methods are common because they are easy to code and explain. "
            "Distance between coordinates can be estimated with the Haversine formula when full "
            "street-network routing is not required for the demo. GIS-based planning has also been "
            "used for municipal solid waste transport (Ghose et al, 2006).",
            S["body"],
        )
    )
    story.append(
        p(
            "IoT studies often combine fill-level sensors with routing (Martikkala et al, 2023; "
            "Banciu et al, 2025; Pal and Bhatia, 2022). This project leaves sensors out and works on "
            "human-submitted report locations, which fits a software-only undergraduate scope.",
            S["body"],
        )
    )

    story.append(p("2.5 Related Works", S["h2"]))
    story.append(
        p(
            "Kapadia and Mehta (2023) discuss dynamic route optimization for IoT-based waste collection "
            "and stress structured location and status data. Martikkala et al (2023) present a smart "
            "textile waste collection system with dynamic routing and IoT. Kolangiammal et al (2025) "
            "describe a smart waste collection management system. Banciu et al (2025) look at "
            "IoT-enabled collection, route optimization and environmental impact. Pal and Bhatia (2022) "
            "compare bin-level IoT sensing and routing in a hilly city setting. N (2023) discusses "
            "municipal solid waste challenges in a Nigerian city (Aba), which supports the local "
            "relevance of better coordination tools. Zhang et al (2019) review barriers to smart waste "
            "management for a circular economy, including organisational and technical constraints.",
            S["body"],
        )
    )

    story.append(p("2.6 Summary of Literature Gap", S["h2"]))
    story.append(
        p(
            "Much of the literature focuses on sensor-heavy smart-city systems or large logistics "
            "platforms. There is still room for a student-scale system that combines resident reporting, "
            "admin workflow, officer tasks, status history and a clear, simple optimization step "
            "without expensive hardware. WasteTrack targets that gap, using Bauchi as the reference "
            "setting for defaults, sample locations and presentation imagery.",
            S["body"],
        )
    )
    story.append(PageBreak())

    # ========== CHAPTER THREE: METHODOLOGY ==========
    story.append(p("CHAPTER THREE", S["h1"]))
    story.append(p("METHODOLOGY", S["h1"]))

    story.append(p("3.1 Introduction", S["h2"]))
    story.append(
        p(
            "This chapter describes how the study was designed and carried out. It covers the study "
            "design, analysis of the existing practice, requirements, system architecture, tools used "
            "to build WasteTrack, and the methods used to collect results and evaluate the system.",
            S["body"],
        )
    )

    story.append(p("3.2 Study Design", S["h2"]))
    story.append(
        p(
            "The work followed a design-and-implementation approach common in software projects. "
            "First, the problem of informal waste reporting was analysed. Next, functional and "
            "non-functional requirements were specified for three roles (resident, administrator and "
            "officer). The system was then designed (architecture, data model, workflow and security) "
            "and implemented as a web application. Finally, functional tests and a live deployment "
            "were used to check that the objectives were met. No probability sampling of a population "
            "was required; evaluation used constructed test cases and observed system behaviour.",
            S["body"],
        )
    )

    story.append(p("3.3 Analysis of the Existing System", S["h2"]))
    story.append(
        p(
            "In current practice, a resident who sees overflow or illegal dumping usually calls someone "
            "or reports verbally. There is often no ticket number, no confirmed map point and no standard "
            "path from complaint to completion. Collection teams may follow fixed routes or ad-hoc "
            "instructions. Administrators rarely have one view of open cases, urgency and who is assigned.",
            S["body"],
        )
    )
    story.append(p("Problems of the existing system include:", S["body_ni"]))
    story.extend(
        bullets(
            [
                "Exact waste locations are hard to verify from verbal descriptions.",
                "High-urgency cases, such as blocked drains during rains, are not always prioritised.",
                "Missing status history weakens accountability.",
                "Unstructured scheduling leads to repeated visits or missed points.",
                "There is little data for hotspot analysis and service planning.",
            ],
            S,
        )
    )

    story.append(p("3.4 Requirements Specification", S["h2"]))
    data = [
        [Paragraph("<b>Role</b>", S["body_ni"]), Paragraph("<b>Key functions</b>", S["body_ni"])],
        [
            Paragraph("Resident", S["body_ni"]),
            Paragraph(
                "Register and login; submit report (category, description, lat/lng, optional image); "
                "view own reports and status history; update profile.",
                S["body_ni"],
            ),
        ],
        [
            Paragraph("Administrator", S["body_ni"]),
            Paragraph(
                "Dashboard KPIs; filter and search reports; verify or reject; assign officer; "
                "schedule; notes; run optimization; analytics; manage officers.",
                S["body_ni"],
            ),
        ],
        [
            Paragraph("Officer", S["body_ni"]),
            Paragraph(
                "View assigned tasks; open map and details; start task; complete task with optional note; profile.",
                S["body_ni"],
            ),
        ],
    ]
    t = Table(data, colWidths=[3.5 * cm, CONTENT_WIDTH - 3.5 * cm])
    t.setStyle(table_style())
    story.append(t)
    story.append(p("Table 3.1: Functional requirements by role", S["caption"]))

    story.append(
        p(
            "Non-functional needs include authentication and role checks, CSRF protection, rate "
            "limiting, mobile-friendly layouts, durable storage of reports and status history, and "
            "deployability on a public host such as Render.",
            S["body"],
        )
    )

    story.append(p("3.5 System Architecture and Design", S["h2"]))
    story.append(
        p(
            "The design uses four layers: presentation (HTML templates, Bootstrap, Leaflet maps); "
            "application (Flask routes and business rules); data (SQLAlchemy and a relational database); "
            "and optimization or analytics (Haversine nearest-neighbour order and summary counts). "
            "Figure 3.1 shows the layered architecture.",
            S["body"],
        )
    )
    add_figure(story, "fig_3_1_system_architecture.png", "Figure 3.1: High-level system architecture of WasteTrack", S)

    story.append(
        p(
            "Access control uses session login (Flask-Login) plus role checks on protected routes. "
            "The three roles (resident, officer and administrator) have different capabilities, "
            "as shown in Figure 3.2.",
            S["body"],
        )
    )
    add_figure(story, "fig_3_2_role_based_access.png", "Figure 3.2: Role-based access model", S)

    story.append(
        p(
            "The report status path is submitted → verified → assigned → scheduled → in_progress → "
            "completed, with a branch to rejected from early stages (Figure 3.3). Each change adds a "
            "StatusHistory row with the actor and an optional note.",
            S["body"],
        )
    )
    add_figure(story, "fig_3_3_status_workflow.png", "Figure 3.3: Report status workflow", S)

    story.append(
        p(
            "Core entities are User, Report, StatusHistory and OptimizationRun (Table 3.3 and Figure 3.4).",
            S["body"],
        )
    )
    data2 = [
        [Paragraph("<b>Entity</b>", S["body_ni"]), Paragraph("<b>Purpose</b>", S["body_ni"])],
        [Paragraph("User", S["body_ni"]), Paragraph("Login and role assignment", S["body_ni"])],
        [Paragraph("Report", S["body_ni"]), Paragraph("Main waste issue record and workflow state", S["body_ni"])],
        [Paragraph("StatusHistory", S["body_ni"]), Paragraph("Audit trail of status changes", S["body_ni"])],
        [Paragraph("OptimizationRun", S["body_ni"]), Paragraph("Record of each optimization run", S["body_ni"])],
    ]
    t2 = Table(data2, colWidths=[4 * cm, CONTENT_WIDTH - 4 * cm])
    t2.setStyle(table_style())
    story.append(t2)
    story.append(p("Table 3.3: Core database entities", S["caption"]))
    add_figure(story, "fig_3_4_entity_relationship.png", "Figure 3.4: Conceptual entity relationship (core tables)", S)

    story.append(
        p(
            "Security measures include password hashing, CSRF tokens, rate limits on auth routes, "
            "secure session cookies behind HTTPS, security headers, upload limits and a protected "
            "staff setup page.",
            S["body"],
        )
    )

    story.append(p("3.6 Development Tools and Implementation Approach", S["h2"]))
    data3 = [
        [Paragraph("<b>Component</b>", S["body_ni"]), Paragraph("<b>Technology</b>", S["body_ni"]), Paragraph("<b>Purpose</b>", S["body_ni"])],
        [Paragraph("Backend", S["body_ni"]), Paragraph("Python, Flask", S["body_ni"]), Paragraph("Web app and business logic", S["body_ni"])],
        [Paragraph("ORM / DB", S["body_ni"]), Paragraph("SQLAlchemy, SQLite/PostgreSQL", S["body_ni"]), Paragraph("Data storage", S["body_ni"])],
        [Paragraph("Auth", S["body_ni"]), Paragraph("Flask-Login, Werkzeug hashes", S["body_ni"]), Paragraph("Sessions and passwords", S["body_ni"])],
        [Paragraph("Security", S["body_ni"]), Paragraph("Flask-WTF, Flask-Limiter", S["body_ni"]), Paragraph("CSRF and rate limits", S["body_ni"])],
        [Paragraph("Frontend", S["body_ni"]), Paragraph("Jinja2, Bootstrap, CSS", S["body_ni"]), Paragraph("Page layouts", S["body_ni"])],
        [Paragraph("Maps", S["body_ni"]), Paragraph("Leaflet, OpenStreetMap", S["body_ni"]), Paragraph("Map pin and display", S["body_ni"])],
        [Paragraph("Optimization", S["body_ni"]), Paragraph("Haversine + NN", S["body_ni"]), Paragraph("Collection order", S["body_ni"])],
        [Paragraph("Deploy", S["body_ni"]), Paragraph("Gunicorn, Render", S["body_ni"]), Paragraph("Live hosting", S["body_ni"])],
    ]
    t3 = Table(data3, colWidths=[3.2 * cm, 5.0 * cm, CONTENT_WIDTH - 8.2 * cm])
    t3.setStyle(table_style())
    story.append(t3)
    story.append(p("Table 3.2: Technology stack", S["caption"]))

    story.append(
        p(
            "Implementation used modular Flask blueprints for auth, resident, officer and admin. "
            "Residents pin locations on a Leaflet map (default near Bauchi). Administrators manage "
            "reports and run optimization. Officers update task status. Production serving uses "
            "wsgi.py under Gunicorn. The live demo is at https://wastetrack-nd71.onrender.com.",
            S["body"],
        )
    )

    story.append(p("3.7 Data Collection and Evaluation Methods", S["h2"]))
    story.append(
        p(
            "Data for evaluation came from (i) constructed functional test cases run with the Flask "
            "test client and manual browser checks, (ii) screen captures and workflow runs on the live "
            "deployment, and (iii) comparison of estimated optimization path length with a simple "
            "manual order of the same stops. No human-subject survey sample was required for this "
            "software project. Results are reported in Chapter Four.",
            S["body"],
        )
    )
    story.append(PageBreak())

    # ========== CHAPTER FOUR: RESULTS AND DISCUSSION ==========
    story.append(p("CHAPTER FOUR", S["h1"]))
    story.append(p("RESULTS AND DISCUSSION", S["h1"]))

    story.append(p("4.1 Introduction", S["h2"]))
    story.append(
        p(
            "This chapter presents the results of implementing and testing WasteTrack. It describes "
            "what was built, the outcomes of functional tests, interpretation of those outcomes against "
            "the objectives, and screenshots from the live system.",
            S["body"],
        )
    )

    story.append(p("4.2 System Implementation Results", S["h2"]))
    story.append(
        p(
            "The system was successfully implemented with all three roles active. Residents can "
            "register, submit geolocated reports with optional photos and track status. Administrators "
            "can verify or reject reports, assign officers, schedule pickups, view KPIs and maps, and "
            "run the optimization helper. Officers can open assigned tasks and mark them in progress "
            "or completed. A live instance was deployed with HTTPS and a health check endpoint.",
            S["body"],
        )
    )
    story.append(
        p(
            "The optimization module computes pairwise Haversine distances and returns a nearest-neighbour "
            "order with urgency preference. On the live site, administrators can select candidate reports "
            "and obtain a recommended order with estimated path distance, which can be compared with a "
            "manual (age-based) order.",
            S["body"],
        )
    )

    story.append(p("4.3 Functional Testing Results", S["h2"]))
    data4 = [
        [
            Paragraph("<b>ID</b>", S["body_ni"]),
            Paragraph("<b>Scenario</b>", S["body_ni"]),
            Paragraph("<b>Expected</b>", S["body_ni"]),
            Paragraph("<b>Result</b>", S["body_ni"]),
        ],
        [Paragraph("T01", S["body_ni"]), Paragraph("Resident registration", S["body_ni"]), Paragraph("Account created; role resident", S["body_ni"]), Paragraph("Passed", S["body_ni"])],
        [Paragraph("T02", S["body_ni"]), Paragraph("Admin login", S["body_ni"]), Paragraph("Access admin dashboard", S["body_ni"]), Paragraph("Passed", S["body_ni"])],
        [Paragraph("T03", S["body_ni"]), Paragraph("Submit geolocated report", S["body_ni"]), Paragraph("Tracking code; status submitted", S["body_ni"]), Paragraph("Passed", S["body_ni"])],
        [Paragraph("T04", S["body_ni"]), Paragraph("Admin verify and assign", S["body_ni"]), Paragraph("Status updates; officer linked", S["body_ni"]), Paragraph("Passed", S["body_ni"])],
        [Paragraph("T05", S["body_ni"]), Paragraph("Officer complete task", S["body_ni"]), Paragraph("Status completed; history entry", S["body_ni"]), Paragraph("Passed", S["body_ni"])],
        [Paragraph("T06", S["body_ni"]), Paragraph("Run optimization", S["body_ni"]), Paragraph("Ordered stops; distance computed", S["body_ni"]), Paragraph("Passed", S["body_ni"])],
        [Paragraph("T07", S["body_ni"]), Paragraph("Unauthorized role access", S["body_ni"]), Paragraph("Blocked or redirected", S["body_ni"]), Paragraph("Passed", S["body_ni"])],
        [Paragraph("T08", S["body_ni"]), Paragraph("CSRF on POST without token", S["body_ni"]), Paragraph("Request rejected", S["body_ni"]), Paragraph("Passed", S["body_ni"])],
    ]
    t4 = Table(data4, colWidths=[1.6 * cm, 5.0 * cm, 6.0 * cm, CONTENT_WIDTH - 12.6 * cm])
    t4.setStyle(table_style())
    story.append(t4)
    story.append(p("Table 4.1: Functional test cases summary", S["caption"]))

    data5 = [
        [Paragraph("<b>Objective</b>", S["body_ni"]), Paragraph("<b>Outcome</b>", S["body_ni"])],
        [
            Paragraph("Resident reporting with location and image", S["body_ni"]),
            Paragraph("Built and checked end to end", S["body_ni"]),
        ],
        [
            Paragraph("Admin dashboard workflow", S["body_ni"]),
            Paragraph("Built (verify, assign, schedule, analytics)", S["body_ni"]),
        ],
        [
            Paragraph("Route or schedule optimization", S["body_ni"]),
            Paragraph("Built (Haversine + nearest neighbour)", S["body_ni"]),
        ],
        [
            Paragraph("Evaluation", S["body_ni"]),
            Paragraph("Functional tests and live deployment checks completed", S["body_ni"]),
        ],
    ]
    t5 = Table(data5, colWidths=[CONTENT_WIDTH * 0.48, CONTENT_WIDTH * 0.52])
    t5.setStyle(table_style())
    story.append(t5)
    story.append(p("Table 4.2: Mapping of objectives to outcomes", S["caption"]))

    story.append(p("4.4 Discussion of Findings", S["h2"]))
    story.append(
        p(
            "The results show that a software-only system can convert informal complaints into "
            "structured, trackable cases. This agrees with earlier work that stresses digital "
            "coordination for waste operations (Kapadia and Mehta, 2023; Hannan et al, 2015). "
            "Unlike many IoT-centred studies (Martikkala et al, 2023; Banciu et al, 2025), WasteTrack "
            "depends on human reporting, which is realistic where sensors are not available.",
            S["body"],
        )
    )
    story.append(
        p(
            "The nearest-neighbour helper is easy to explain and implement, but it is not optimal for "
            "large fleets or complex road networks. That limitation matches the project scope stated "
            "in Chapter One. Free-tier hosting may introduce cold-start delay after idle periods; this "
            "is a platform trait rather than a failure of the application logic. Overall, the "
            "objectives in Section 1.3 were met within the stated limits.",
            S["body"],
        )
    )

    story.append(p("4.5 System Screenshots", S["h2"]))
    story.append(
        p(
            "Residents track each case through a four-stage progress indicator "
            "(Submitted, Verified, Scheduled, Collected) rendered on their reports page, "
            "mirroring the status workflow described in Section 3.4.",
            S["body"],
        )
    )
    story.append(
        p(
            "Collection officers view assigned tasks as an ordered stop list with per-stop "
            "Start/Complete actions, matching the optimized collection order produced by the "
            "route assignment module.",
            S["body"],
        )
    )
    story.append(
        p(
            "Figures 4.1 to 4.3 are screen captures from the live deployment at "
            "https://wastetrack-nd71.onrender.com after exercising resident registration, report "
            "submission, admin login and optimization.",
            S["body"],
        )
    )
    add_figure(
        story,
        "fig_4_1_resident_report.png",
        "Figure 4.1: Resident report submission interface (live site)",
        S,
    )
    story.append(
        p(
            "Figure 4.1 shows the resident form: category, description, landmark, urgency, photo field "
            "and the required map pin around Bauchi.",
            S["body"],
        )
    )
    add_figure(
        story,
        "fig_4_2_admin_dashboard.png",
        "Figure 4.2: Administrator dashboard (live site)",
        S,
    )
    story.append(
        p(
            "Figure 4.2 shows the operations desk with KPI cards, recent reports, manage actions and "
            "the open-reports map.",
            S["body"],
        )
    )
    add_figure(
        story,
        "fig_4_3_optimization.png",
        "Figure 4.3: Optimization and map view (live site)",
        S,
    )
    story.append(
        p(
            "Figure 4.3 shows candidate selection and a recommended collection order with estimated "
            "path distance after running optimization on live data.",
            S["body"],
        )
    )
    story.append(PageBreak())

    # ========== CHAPTER FIVE ==========
    story.append(p("CHAPTER FIVE", S["h1"]))
    story.append(p("SUMMARY, CONCLUSIONS AND RECOMMENDATIONS", S["h1"]))

    story.append(p("5.1 Summary", S["h2"]))
    story.append(
        p(
            "This project designed and built WasteTrack, a web system for waste issue reporting, "
            "admin case handling, field-officer task updates and a light collection-order helper. "
            "It uses standard web tools, a structured database, map-based location capture and "
            "security suited to a public demo. Bauchi guided the default map area, sample data and "
            "presentation photos. Functional tests and live deployment confirmed the main features.",
            S["body"],
        )
    )

    story.append(p("5.2 Conclusions", S["h2"]))
    story.append(
        p(
            "The work shows that a software-only system can improve how waste complaints are recorded "
            "and followed up, without bin sensors. Informal complaints become structured cases with "
            "roles and a simple route order. Within the limits of a student prototype, the system "
            "meets the stated aim and objectives and can be demonstrated live.",
            S["body"],
        )
    )

    story.append(p("5.3 Recommendations", S["h2"]))
    story.extend(
        bullets(
            [
                "Use managed PostgreSQL for multi-user production instead of short-lived SQLite on free hosts.",
                "Create staff accounts through controlled onboarding, not public registration.",
                "Train officers to update status consistently so history stays useful.",
                "Add street-network routing APIs later if turn-by-turn vehicle guidance is required.",
                "Consider progressive web app features and offline caching for low-connectivity areas.",
                "Optional later phases may include IoT bin sensors, SMS or WhatsApp status alerts, and multi-vehicle routing for larger fleets.",
            ],
            S,
        )
    )
    story.append(PageBreak())

    # ========== REFERENCES (alphabetical) ==========
    story.append(p("REFERENCES", S["h1"]))
    # Department style: Author (year). Title. Source...
    refs = [
        "Anagnostopoulos, T., Zaslavsky, A., Kolomvatsos, K., Medvedev, A., Amirian, P., Morley, J. and Hadjieftymiades, S. (2017). Challenges and opportunities of waste management in IoT-enabled smart cities: A survey. IEEE Transactions on Sustainable Computing, 2(3): 275-289.",
        "Banciu, C., Florea, A. and Popa, M. (2025). IoT-enabled waste collection: Route optimization and environmental impact reduction using smart technologies. 2025 29th International Conference on System Theory, Control and Computing (ICSTCC).",
        "Buhrkal, K., Larsen, A. and Ropke, S. (2012). The waste collection vehicle routing problem with time windows in a city logistics context. Procedia - Social and Behavioral Sciences, 39: 241-254.",
        "Flask Documentation (n.d.). Welcome to Flask. https://flask.palletsprojects.com/",
        "Ghose, M. K., Dikshit, A. K. and Sharma, S. K. (2006). A GIS based transportation model for solid waste disposal: A case study on Asansol municipality. Waste Management, 26(11): 1287-1293.",
        "Hannan, M. A., Abdulla Al Mamun, M., Hussain, A., Basri, H. and Begum, R. A. (2015). A review on technologies and their usage in solid waste monitoring and management systems: Issues and challenges. Waste Management, 43: 509-523.",
        "Hoornweg, D. and Bhada-Tata, P. (2012). What a waste: A global review of solid waste management. World Bank, Washington, DC.",
        "Kapadia, N. and Mehta, R. (2023). Dynamic route optimization for IoT based intelligent waste collection vehicle routing system. Intelligent Decision Technologies.",
        "Kolangiammal, S., P., K. R., Prakash S, V. and M., A. (2025). Smart waste collection management system. 2025 11th International Conference on Communication and Signal Processing (ICCSP).",
        "Leaflet (n.d.). An open-source JavaScript library for mobile-friendly interactive maps. https://leafletjs.com/",
        "Martikkala, A., Mayanti, B., Helo, P., Lobov, A. and Ituarte, I. F. (2023). Smart textile waste collection system: Dynamic route optimization with IoT. Journal of Environmental Management, 335: 117548.",
        "N., K. F. (2023). Municipal solid waste disposal in the city of Aba: Challenges and solutions. Open Access Journal of Waste Management and Xenobiotics, 6(1).",
        "OpenStreetMap contributors (n.d.). OpenStreetMap. https://www.openstreetmap.org/",
        "Pal, M. S. and Bhatia, M. (2022). Lifetime maximization of bin level IoT sensor and route optimization for smart waste management in hilly city Shimla, India: A comparative analysis. 2022 Second International Conference on Advances in Electrical, Computing, Communication and Sustainable Technologies (ICAECT).",
        "Pressman, R. S. and Maxim, B. R. (2015). Software Engineering: A Practitioner's Approach, 8th Edition. McGraw-Hill Education, New York.",
        "Sommerville, I. (2016). Software Engineering, 10th Edition. Pearson, Harlow.",
        "Tavares, G., Zsigraiova, Z., Semiao, V. and Carvalho, M. G. (2009). Optimisation of MSW collection routes for minimum fuel consumption using 3D GIS modelling. Waste Management, 29(3): 1176-1185.",
        "United Nations Environment Programme (2015). Global Waste Management Outlook. UNEP.",
        "World Bank (2018). What a Waste 2.0: A Global Snapshot of Solid Waste Management to 2050. World Bank, Washington, DC.",
        "Zhang, A., Venkatesh, V. G., Liu, Y., Wan, M., Qu, T. and Huisingh, D. (2019). Barriers to smart waste management for a circular economy in China. Journal of Cleaner Production, 240: 118198.",
    ]
    for r in refs:
        story.append(p(r, S["ref"]))
    story.append(PageBreak())

    # ========== APPENDICES ==========
    story.append(p("APPENDIX A", S["h1"]))
    story.append(p("SAMPLE PRODUCTION CONFIGURATION", S["h1"]))
    story.append(
        p(
            "The following environment variables show a typical production-style setup "
            "(use strong unique secrets in real deployments):",
            S["body_ni"],
        )
    )
    story.append(
        p(
            "FLASK_ENV=production<br/>"
            "SECRET_KEY=&lt;long-random-hex&gt;<br/>"
            "ADMIN_EMAIL=admin@example.org<br/>"
            "ADMIN_PASSWORD=&lt;strong-password&gt;<br/>"
            "OFFICER_EMAIL=officer@example.org<br/>"
            "OFFICER_PASSWORD=&lt;strong-password&gt;<br/>"
            "SETUP_SECRET=&lt;setup-secret&gt;<br/>"
            "SEED_DEMO_DATA=false<br/>"
            "BEHIND_PROXY=true<br/>"
            "SESSION_COOKIE_SECURE=true<br/>"
            "DATABASE_URL=&lt;sqlite-or-postgres-url&gt;",
            S["body_ni"],
        )
    )
    story.append(PageBreak())

    story.append(p("APPENDIX B", S["h1"]))
    story.append(p("PROJECT MODULE MAP", S["h1"]))
    story.append(p("Key source paths in the repository:", S["body_ni"]))
    story.extend(
        bullets(
            [
                "app/__init__.py: application factory, security headers, bootstrap",
                "app/models.py: User, Report, StatusHistory, OptimizationRun",
                "app/routes/auth.py: login, register, secure staff setup",
                "app/routes/resident.py: reporting and resident dashboard",
                "app/routes/admin.py: administration, analytics, optimization UI",
                "app/routes/officer.py: field tasks",
                "app/services/optimization.py: Haversine and nearest-neighbour ordering",
                "wsgi.py / gunicorn.conf.py: production serving",
                "docs/: project documentation including this report generator",
            ],
            S,
        )
    )
    story.append(PageBreak())

    story.append(p("APPENDIX C", S["h1"]))
    story.append(p("USER GUIDE SUMMARY", S["h1"]))
    story.append(p("C.1 Residents", S["h2"]))
    story.extend(
        bullets(
            [
                "Open the portal and choose Register (or Sign in).",
                "Select Report refuse, set category and description, place the map pin carefully, attach a photo if you have one, and submit.",
                "Use My reports to follow status until completed.",
            ],
            S,
        )
    )
    story.append(p("C.2 Administrators", S["h2"]))
    story.extend(
        bullets(
            [
                "Sign in with a staff admin account.",
                "Use the operations desk to review pending cases, verify or reject, assign officers and schedule pickups.",
                "Open Optimize to select open reports and run a recommended collection order.",
            ],
            S,
        )
    )
    story.append(p("C.3 Collection Officers", S["h2"]))
    story.extend(
        bullets(
            [
                "Sign in with an officer account.",
                "Open Tasks, start work when you arrive, and mark complete with a short note if needed.",
            ],
            S,
        )
    )

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=MARGIN_LEFT,
        rightMargin=MARGIN_RIGHT,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title="WasteTrack Final Year Project Report",
        author=STUDENT_NAME,
    )
    doc.build(story)
    print(f"Wrote {OUT}")
    return OUT


if __name__ == "__main__":
    build()
