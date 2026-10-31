"""Generate the PDF and DOCX test-split documents of the bilingual RAG eval dataset.

Usage (from api/, so it uses the API environment's pymupdf and python-docx):
    uv run python ../sample_documents/eval_test/make_eval_docs.py ../sample_documents/eval_test
"""

import sys
from pathlib import Path

import pymupdf as fitz
from docx import Document

NOTE = "Synthetic retrieval-test document. Meghna Cooperative and all figures in it are fictional."
NOTE_BN = "রিট্রিভাল পরীক্ষার জন্য তৈরি কাল্পনিক নথি। মেঘনা সমবায় এবং এখানে উল্লিখিত সকল নিয়ম, কোড ও অঙ্ক কাল্পনিক।"

# One topic per page, so answers can be cited with a page number. English only: the PDF
# base fonts have no Bangla glyphs.
PDF_PAGES = [
    (
        "Meghna Central Warehouse: Safety Manual",
        [
            NOTE,
            "Manual revision DOC-WHS-2027-05. This manual applies to everyone who enters the "
            "Meghna central warehouse at Tongi, including staff, drivers, contractors and visitors.",
            "Contents: page 1 overview, page 2 protective equipment, page 3 forklifts, page 4 "
            "chemical storage, page 5 fire safety, page 6 incident reporting.",
        ],
    ),
    (
        "Personal protective equipment",
        [
            "Safety shoes with steel toe caps and a high-visibility vest must be worn at all "
            "times on the warehouse floor. Hard hats are required in the racking aisles, where "
            "pallets are stored up to 9 metres high.",
            "Visitors receive a vest and a hard hat at the gate and must be escorted by a "
            "warehouse employee. Damaged equipment is replaced free of charge at the store room; "
            "employees should not buy their own.",
        ],
    ),
    (
        "Forklift operation",
        [
            "Only employees holding a valid Meghna forklift licence, code FL-2, may drive a "
            "forklift. The licence is valid for 2 years and is renewed after a refresher "
            "course and a practical test.",
            "The speed limit inside the warehouse is 8 km/h, and 5 km/h near loading bays and "
            "pedestrian crossings. Never lift a load heavier than the 2,500 kg rated capacity "
            "shown on the mast plate. Pedestrians must keep at least 3 metres away from a "
            "moving forklift.",
        ],
    ),
    (
        "Chemical storage",
        [
            "Fertilisers and pesticides are stored only in Zone C, which is locked and "
            "ventilated. Each container must carry its original label and a safety data sheet "
            "kept in the Zone C cabinet.",
            "Liquids are stored on the lowest shelf, never above 1.5 metres. A spill kit is "
            "kept at the Zone C door. Spills larger than 5 litres must be reported to the "
            "shift supervisor immediately, and the area must be cleared before clean-up.",
        ],
    ),
    (
        "Fire safety",
        [
            "Fire extinguishers are placed every 20 metres along the main aisles and are "
            "inspected every month. Smoking is allowed only in the marked area outside Gate 2.",
            "When the fire alarm sounds, stop work, switch off forklifts and walk to the "
            "assembly point in the north parking lot. Fire drills are held every 3 months, and "
            "the whole building must be cleared within 4 minutes.",
        ],
    ),
    (
        "Incident reporting",
        [
            "Every injury, near miss or damage to stock must be reported on form SAF-IR "
            "before the end of the shift, even when nobody is hurt. Serious injuries are "
            "reported to the safety officer by phone at once, on extension 4040.",
            "The safety officer investigates every report within 48 hours and shares the "
            "lessons learned at the monthly safety meeting. Reporting an incident never leads "
            "to disciplinary action against the person who reports it.",
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
    doc.set_metadata({"title": "Meghna Central Warehouse Safety Manual"})
    doc.save(path)


def add_table(doc: Document, header: list[str], rows: list[tuple[str, ...]]) -> None:
    table = doc.add_table(rows=1, cols=len(header))
    table.style = "Table Grid"
    for cell, text in zip(table.rows[0].cells, header, strict=True):
        cell.text = text
    for values in rows:
        for cell, text in zip(table.add_row().cells, values, strict=True):
            cell.text = text


def make_training_calendar(path: Path) -> None:
    doc = Document()
    doc.add_heading("Meghna Staff Training Calendar 2027", level=0)
    doc.add_paragraph(NOTE)
    doc.add_paragraph("Calendar revision DOC-LND-2027-01. Owner: Learning and Development.")

    doc.add_heading("1. January to June courses", level=1)
    add_table(doc, ["Code", "Course", "Dates", "Venue", "Seats"], [
        ("TRN-101", "Customer service basics", "12-13 January", "Head office, room 4", "25"),
        ("TRN-205", "Credit risk assessment", "9-11 February", "Training centre, Gazipur", "20"),
        ("TRN-118", "Excel for reporting", "16 March", "Online", "40"),
        ("TRN-230", "Fraud detection", "20-21 April", "Head office, room 4", "20"),
        ("TRN-140", "First aid and fire safety", "18 May", "Central warehouse, Tongi", "30"),
    ])

    doc.add_heading("2. July to December courses", level=1)
    add_table(doc, ["Code", "Course", "Dates", "Venue", "Seats"], [
        ("TRN-310", "Team leadership", "6-8 July", "Training centre, Gazipur", "16"),
        ("TRN-118", "Excel for reporting", "14 September", "Online", "40"),
        ("TRN-260", "Data protection and privacy", "5 October", "Online", "50"),
        ("TRN-101", "Customer service basics", "16-17 November", "Chattogram branch", "25"),
    ])

    doc.add_heading("3. Registration and attendance", level=1)
    doc.add_paragraph(
        "Register in the Meghna Learning portal at least 10 days before a course starts. "
        "Your line manager must approve the registration. Seats are given in order of "
        "approval. If you cannot attend, cancel at least 3 working days before the course, "
        "otherwise the missed course counts against your yearly training quota of 5 courses."
    )

    doc.add_heading("4. Certificates", level=1)
    doc.add_paragraph(
        "A certificate is issued to participants who attend at least 80 percent of the "
        "sessions and pass the end-of-course quiz with a score of 70 or more. Certificates "
        "appear in the Learning portal within 7 days. Courses with codes starting with "
        "TRN-2 count towards the annual compliance requirement."
    )

    doc.add_heading("৫. বাংলায় সংক্ষেপে", level=1)
    doc.add_paragraph(
        "যেকোনো কোর্স শুরুর অন্তত ১০ দিন আগে লার্নিং পোর্টালে নিবন্ধন করতে হবে। "
        "কোর্সে যেতে না পারলে ৩ কর্মদিবস আগে বাতিল করুন। ৮০ শতাংশ সেশনে উপস্থিত থাকলে "
        "এবং কুইজে ৭০ বা তার বেশি নম্বর পেলে সনদ দেওয়া হয়। অনলাইন কোর্সের জন্য "
        "ক্যামেরা চালু রাখা বাধ্যতামূলক।"
    )
    doc.save(path)


def make_procurement_rules(path: Path) -> None:
    doc = Document()
    doc.add_heading("মেঘনা সমবায়: ক্রয় নীতিমালা", level=0)
    doc.add_paragraph(NOTE_BN)
    doc.add_paragraph("নীতিমালার সংস্করণ: DOC-PRC-2027-02। দায়িত্বপ্রাপ্ত বিভাগ: ক্রয় ও সরবরাহ বিভাগ।")

    doc.add_heading("১. ক্রয়ের পদ্ধতি ও সীমা", level=1)
    add_table(doc, ["মূল্যসীমা", "পদ্ধতি", "অনুমোদনকারী"], [
        ("১০,০০০ টাকা পর্যন্ত", "সরাসরি ক্রয়, একটি রসিদ যথেষ্ট", "বিভাগীয় প্রধান"),
        ("১০,০০১ থেকে ২,০০,০০০ টাকা", "কমপক্ষে ৩টি দরপ্রস্তাব (কোটেশন)", "ক্রয় কমিটি"),
        ("২,০০,০০১ থেকে ২০,০০,০০০ টাকা", "সীমিত দরপত্র, কমপক্ষে ৫টি প্রতিষ্ঠান", "ক্রয় কমিটি ও অর্থ পরিচালক"),
        ("২০,০০,০০০ টাকার বেশি", "উন্মুক্ত দরপত্র, পত্রিকায় বিজ্ঞাপন", "পরিচালনা পর্ষদ"),
    ])

    doc.add_heading("২. সরবরাহকারী তালিকাভুক্তি", level=1)
    doc.add_paragraph(
        "মেঘনা সমবায়ে মালামাল সরবরাহ করতে হলে প্রতিষ্ঠানকে আগে তালিকাভুক্ত হতে হবে। "
        "তালিকাভুক্তির ফর্মের কোড PRC-VEN-01। আবেদনের সাথে হালনাগাদ ট্রেড লাইসেন্স, ই-টিআইএন "
        "সনদ এবং ভ্যাট নিবন্ধন সনদ দিতে হবে। তালিকাভুক্তি ২ বছরের জন্য বৈধ থাকে।"
    )

    doc.add_heading("৩. স্বার্থের সংঘাত", level=1)
    doc.add_paragraph(
        "কোনো কর্মীর নিকটাত্মীয় যদি কোনো সরবরাহকারী প্রতিষ্ঠানের মালিক বা অংশীদার হন, তবে সেই কর্মী "
        "ওই ক্রয়ের মূল্যায়ন বা অনুমোদনে অংশ নিতে পারবেন না। বিষয়টি PRC-COI ফর্মে লিখিতভাবে জানাতে "
        "হবে। সরবরাহকারীর কাছ থেকে ৫০০ টাকার বেশি মূল্যের কোনো উপহার নেওয়া নিষিদ্ধ।"
    )

    doc.add_heading("৪. মালামাল গ্রহণ ও বিল পরিশোধ", level=1)
    doc.add_paragraph(
        "মালামাল পৌঁছানোর পর তিন সদস্যের গ্রহণ কমিটি ৫ কর্মদিবসের মধ্যে পরিমাণ ও মান যাচাই করে "
        "গ্রহণ প্রতিবেদন দেবে। গ্রহণ প্রতিবেদন পাওয়ার ৩০ দিনের মধ্যে সরবরাহকারীর বিল ব্যাংক "
        "হিসাবে পরিশোধ করা হয়। নির্ধারিত সময়ের পরে সরবরাহ করলে প্রতি সপ্তাহ দেরির জন্য চুক্তিমূল্যের "
        "২ শতাংশ জরিমানা কাটা হয়, যা সর্বোচ্চ ১০ শতাংশ পর্যন্ত হতে পারে।"
    )
    doc.save(path)


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    make_pdf(out / "warehouse_safety_manual.pdf")
    make_training_calendar(out / "training_calendar_2027.docx")
    make_procurement_rules(out / "procurement_rules_bn.docx")
    print("wrote", sorted(p.name for p in out.iterdir()))
