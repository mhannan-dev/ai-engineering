"""Generate the PDF and DOCX sample documents for P5 retrieval testing.

Usage: python make_sample_docs.py <output_dir>
"""

import sys
from pathlib import Path

import fitz  # PyMuPDF
from docx import Document

NOTE = "Synthetic retrieval-test document. Northstar and all figures in it are fictional."

# One topic per page, so answers can be cited with a specific page number.
PDF_PAGES = [
    (
        "Northstar Field Sensor NS-200: User Manual",
        [
            NOTE,
            "Manual revision DOC-PRD-2026-01. This manual covers the NS-200 field sensor, "
            "a solar-assisted device that measures soil moisture, air temperature and humidity "
            "and reports readings over a cellular network.",
            "Contents: page 1 overview, page 2 installation, page 3 battery and charging, "
            "page 4 status lights and troubleshooting, page 5 warranty and support.",
        ],
    ),
    (
        "Installation",
        [
            "Mount the NS-200 on a pole between 1.2 and 1.5 metres above the ground, with the "
            "solar panel facing south. Insert the soil probe vertically to a depth of 30 cm. "
            "Keep the sensor at least 5 metres away from irrigation sprinklers.",
            "Press and hold the power button for 3 seconds. The device registers with the "
            "network within 10 minutes. Pair it in the Northstar Field app by scanning the QR "
            "code printed inside the battery cover.",
        ],
    ),
    (
        "Battery and charging",
        [
            "The NS-200 uses a 6,000 mAh lithium iron phosphate battery. With the default "
            "reporting interval of 15 minutes, a full charge lasts 21 days without sunlight. "
            "Reducing the interval to 5 minutes shortens battery life to about 8 days.",
            "The device charges from the built-in solar panel, or from a USB-C charger rated "
            "at 5 V and 2 A. A full charge over USB-C takes about 4 hours. Do not charge the "
            "battery when the air temperature is below 0 degrees Celsius.",
        ],
    ),
    (
        "Status lights and troubleshooting",
        [
            "Solid green: connected and reporting. Blinking green: searching for the network. "
            "Blinking amber: battery below 20 percent. Solid red: sensor fault.",
            "If the light is solid red, remove the soil probe, clean the contacts with a dry "
            "cloth and reinsert it. If the fault remains, perform a factory reset by holding "
            "the power and reset buttons together for 10 seconds. Error code E-17 means the "
            "SIM card is not detected; reseat the SIM card and restart the device.",
        ],
    ),
    (
        "Warranty and support",
        [
            "The NS-200 has a 24-month limited warranty from the date of delivery. The "
            "warranty does not cover physical damage, water entering through an open battery "
            "cover, or batteries older than 12 months.",
            "To make a claim, open a support ticket with the category PRD-WAR and include the "
            "serial number printed on the back of the device. Replacement units are shipped "
            "within 5 working days of an approved claim.",
        ],
    ),
]


def make_pdf(path: Path) -> None:
    doc = fitz.open()
    for title, paragraphs in PDF_PAGES:
        page = doc.new_page(width=595, height=842)  # A4 in points
        page.insert_text((60, 80), title, fontsize=18, fontname="helv")
        box = fitz.Rect(60, 110, 535, 790)
        page.insert_textbox(box, "\n\n".join(paragraphs), fontsize=11, fontname="helv")
    doc.set_metadata({"title": "Northstar NS-200 User Manual"})
    doc.save(path)


def make_docx(path: Path) -> None:
    doc = Document()
    doc.add_heading("Northstar New Joiner Onboarding Guide", level=0)
    doc.add_paragraph(NOTE)
    doc.add_paragraph("Guide revision DOC-HRM-2026-07. Owner: People Operations.")

    doc.add_heading("1. Before your first day", level=1)
    doc.add_paragraph(
        "People Operations emails your offer pack one week before you join. Bring your "
        "national ID card, two passport-size photos and your bank account details on day one. "
        "Your laptop is prepared by IT and handed over at 10:00 on your first morning."
    )

    doc.add_heading("2. First week schedule", level=1)
    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    header = table.rows[0].cells
    header[0].text, header[1].text, header[2].text = "Day", "Session", "Host"
    for day, session, host in [
        ("Day 1", "Welcome, ID card and laptop setup", "People Operations and IT"),
        ("Day 2", "Security training and MFA setup", "Information Security"),
        ("Day 3", "Team introduction and tools walkthrough", "Team lead"),
        ("Day 4", "Shadowing a teammate", "Assigned buddy"),
        ("Day 5", "First-week check-in", "Team lead"),
    ]:
        row = table.add_row().cells
        row[0].text, row[1].text, row[2].text = day, session, host

    doc.add_heading("3. Your buddy", level=1)
    doc.add_paragraph(
        "Every new joiner is paired with a buddy from another team for the first 60 days. "
        "Your buddy is your first contact for informal questions. You meet your buddy for "
        "30 minutes every week during that period."
    )

    doc.add_heading("4. Probation", level=1)
    doc.add_paragraph(
        "The probation period is 6 months. Your team lead holds review meetings at the end "
        "of month 3 and month 6. Probation can be extended once, by up to 3 months. During "
        "probation the notice period is 14 days on either side."
    )

    doc.add_heading("৫. বাংলায় সংক্ষেপে", level=1)
    doc.add_paragraph(
        "নতুন কর্মীদের প্রবেশন সময়কাল ৬ মাস। প্রথম ৬০ দিন প্রত্যেক নতুন কর্মীর সাথে "
        "অন্য দলের একজন বাডি থাকবেন। প্রথম দিন সকাল ১০টায় আইটি বিভাগ ল্যাপটপ বুঝিয়ে দেবে।"
    )
    doc.save(path)


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    make_pdf(out / "ns200_sensor_manual.pdf")
    make_docx(out / "onboarding_guide.docx")
    print("wrote", sorted(p.name for p in out.iterdir()))
