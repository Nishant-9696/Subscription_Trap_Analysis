from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak

out = Path(r'C:\Data Analytics\Subscription_Trap_Analysis_Case_Study.pdf')

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Center', parent=styles['BodyText'], alignment=1, fontName='Times-Roman', fontSize=11, leading=14, spaceAfter=8))
styles.add(ParagraphStyle(name='Heading', parent=styles['Heading1'], fontName='Times-Bold', fontSize=16, leading=20, alignment=1, spaceBefore=12, spaceAfter=10, keepWithNext=1))
styles.add(ParagraphStyle(name='SubHeading', parent=styles['Heading2'], fontName='Times-Bold', fontSize=12, leading=14, spaceBefore=12, spaceAfter=6, keepWithNext=1))
styles.add(ParagraphStyle(name='Body', parent=styles['BodyText'], fontName='Times-Roman', fontSize=11, leading=14, spaceAfter=8))

sections = [
    ('COVER PAGE', [
        'Case Study', 'On', 'Subscription Trap Analysis', 'Subject / Code: Data Analytics / [Course Code]', 'Submitted by', '[Student Name] ([Roll Number])', 'Under the guidance of', '[Guide Name]', 'in partial fulfilment for the award of the degree of', 'MASTER OF COMPUTER APPLICATIONS', '(ARTIFICIAL INTELLIGENCE & MACHINE LEARNING)', 'Chandigarh University', '[Month, Year]'
    ]),
    ('BONAFIDE CERTIFICATE', [
        'Certified that this case study titled "Subscription Trap Analysis" is the bonafide work of [Student Name], who carried out this project work under our supervision.',
        'SIGNATURE', '[Dean / HOD Name]', 'HEAD OF THE DEPARTMENT', 'UIC-MCA',
        'SIGNATURE', '[Guide Name]', 'ASSISTANT PROFESSOR', 'UIC-MCA'
    ]),
    ('ACKNOWLEDGEMENT', [
        'I would like to express my sincere gratitude to everyone who supported and guided me throughout the completion of this Data Analytics case study titled "Subscription Trap Analysis."',
        'Their guidance, support, and encouragement helped me understand the project and complete it successfully.',
        'I am also thankful to my institution for providing the opportunity and resources for practical learning.',
        'This project helped me gain hands-on experience in data cleaning, analysis, dashboard design, and business reporting using Python, Excel, SQL, and Tableau.'
    ]),
    ('ABSTRACT', [
        'This project examines recurring subscription expenses and identifies patterns of unnecessary spending. It uses a synthetic dataset containing user, subscription, billing, usage, and budget-related information.',
        'The project focuses on detecting high-cost, low-usage subscriptions and users exceeding their monthly budgets. The analysis includes cleaning the dataset, normalizing billing cycles, computing monthly equivalent cost, and assigning review priorities.',
        'The final output is an interactive dashboard that supports business insight generation and data-driven decision-making. This project demonstrates how analytics can be used to reduce wasteful subscription spending and improve financial awareness.'
    ]),
    ('TABLE OF CONTENTS', [
        '1. Introduction', '2. Literature Review', '3. System Design and Methodology', '4. Implementation and Results', '5. Conclusion and Future Scope', '6. References', '7. GitHub Link'
    ]),
    ('INTRODUCTION', [
        'Data analytics has become critical in understanding recurring financial behavior, especially in the context of digital subscriptions.',
        'The project titled "Subscription Trap Analysis" focuses on evaluating recurring subscription costs, usage levels, and budget pressure. It helps identify services that are high in cost but low in value.',
        'This project is relevant for individuals and organizations because many users pay for services without measuring usage or cost efficiency. The dashboard-based analysis supports better financial decisions and more structured budgeting.'
    ]),
    ('LITERATURE REVIEW', [
        'Existing systems for financial tracking are often manual, spreadsheet-based, or app-based. These systems are useful for recordings but often do not provide analytical review logic for underused subscriptions.',
        'The role of tools such as Python, Excel, SQL, Streamlit, and Tableau is important in transforming raw data into useful business insights. These technologies allow users to validate data, compute metrics, and build interactive dashboards.',
        'Data analytics is important because it provides measurable signals for spending pressure, low-usage services, and budget overruns. The project addresses this gap by combining data cleaning, analytical metric creation, and visual reporting.'
    ]),
    ('SYSTEM DESIGN AND METHODOLOGY', [
        'The project follows a simple three-layer architecture: data layer, analysis layer, and reporting layer.',
        'The data layer stores raw and cleaned records. The analysis layer performs validation, standardization, and metric calculation. The reporting layer visualizes insights using charts, KPI cards, and tabular summaries.',
        'The methodology includes data collection, cleaning, cost normalization, review-priority logic, and dashboard implementation. The formula used for monthly equivalent cost is: Monthly Equivalent Cost = Cost / Billing Cycle Factor.'
    ]),
    ('IMPLEMENTATION AND RESULTS', [
        'The implementation involved Python-based data preparation, SQL-based summarization, and dashboard building using Streamlit and Plotly.',
        'The cleaned dataset was used to compute total spend, average monthly cost, low-usage subscriptions, users exceeding budget, and high-priority review items.',
        'The results show that high-cost, low-usage subscriptions create the strongest business opportunity for review. Category-wise analysis also identified Fitness and Education as major spend contributors.'
    ]),
    ('CONCLUSION AND FUTURE SCOPE', [
        'The project successfully demonstrates how data analytics can support better subscription management and improved financial awareness.',
        'Future improvements may include automated data import, alert-based budget monitoring, predictive analysis, and advanced interactive dashboards.',
        'This project provides a strong academic and practical foundation for understanding analytics-driven decision-making in subscription-based environments.'
    ]),
    ('REFERENCES', [
        '1. Microsoft, Microsoft Excel documentation.',
        '2. Tableau Public documentation.',
        '3. Streamlit documentation.',
        '4. Plotly documentation.',
        '5. Pandas documentation.'
    ]),
    ('GITHUB LINK', [
        'GitHub Link: [To be added after repository is published / not provided in the current project folder]'
    ])
]

story = []
for title, paras in sections:
    story.append(Paragraph(title, styles['Heading']))
    for para in paras:
        if para.upper().startswith('SIGNATURE') or para.startswith('[') or para.startswith('UIC'):
            story.append(Paragraph(para, styles['Center']))
        else:
            story.append(Paragraph(para, styles['Body']))
    story.append(PageBreak())
if story and isinstance(story[-1], PageBreak):
    story.pop()


def add_page_number(canvas, doc):
    canvas.setFont('Times-Roman', 9)
    canvas.drawRightString(A4[0] - 40, 25, f'Page {doc.page}')

pdf = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=72, rightMargin=72, topMargin=72, bottomMargin=72)
pdf.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
print(f'Saved PDF: {out}')
