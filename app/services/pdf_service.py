import os
import qrcode
from PIL import Image
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm

def generate_qr_code_image(qr_text, output_path):
    """Mijoz uchun xavfsiz QR-kod rasmini yaratadi"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=3,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#255F38", back_color="white")
    img.save(output_path)
    return output_path


def generate_receipt_pdf(receipt_data, output_path):
    """
    Elektron chek PDF formatini ReportLab yordamida yaratadi.
    receipt_data = {
        'receipt_number': 'CHK-2026-0001',
        'club_name': 'IRON FITNESS CLUB',
        'club_phone': '+998 90 123 45 67',
        'club_address': 'Urganch sh., Al-Xorazmiy ko\'chasi',
        'date_time': '06.11.2026 14:30',
        'client_name': 'Aliyev Vali',
        'items': [{'name': '1 oylik - Juft kunlar', 'qty': 1, 'price': 300000, 'total': 300000}],
        'subtotal': 300000,
        'discount': 0,
        'total': 300000,
        'payment_method': 'Naqd pul',
        'qr_token': 'IFC-ABC12345'
    }
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 80mm kenglikdagi kassa cheki o'lchami yoki A6
    page_width = 80 * mm
    page_height = 200 * mm
    doc = SimpleDocTemplate(
        output_path,
        pagesize=(page_width, page_height),
        rightMargin=4*mm,
        leftMargin=4*mm,
        topMargin=5*mm,
        bottomMargin=5*mm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ClubTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        alignment=1, # Center
        textColor=colors.HexColor('#255F38')
    )
    subtitle_style = ParagraphStyle(
        'ClubSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        alignment=1,
        textColor=colors.HexColor('#444444')
    )
    normal_style = ParagraphStyle(
        'ReceiptNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11
    )
    bold_style = ParagraphStyle(
        'ReceiptBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12
    )

    story = []

    # Sarlavha
    story.append(Paragraph(receipt_data.get('club_name', 'IRON FITNESS CLUB'), title_style))
    story.append(Paragraph(receipt_data.get('club_address', ''), subtitle_style))
    story.append(Paragraph(f"Tel: {receipt_data.get('club_phone', '')}", subtitle_style))
    story.append(Spacer(1, 3*mm))

    # Chek ma'lumotlari
    story.append(Paragraph(f"<b>Chek №:</b> {receipt_data.get('receipt_number', '')}", normal_style))
    story.append(Paragraph(f"<b>Sana:</b> {receipt_data.get('date_time', datetime.now().strftime('%d.%m.%Y %H:%M'))}", normal_style))
    if receipt_data.get('client_name'):
        story.append(Paragraph(f"<b>Mijoz:</b> {receipt_data.get('client_name')}", normal_style))
    story.append(Spacer(1, 2*mm))

    # Mahsulotlar / Xizmatlar jadvali
    table_data = [["Nomi", "Soni", "Narx", "Jami"]]
    for item in receipt_data.get('items', []):
        table_data.append([
            item['name'][:18],
            str(item['qty']),
            f"{int(item['price']):,}".replace(',', ' '),
            f"{int(item['total']):,}".replace(',', ' ')
        ])

    table = Table(table_data, colWidths=[32*mm, 10*mm, 15*mm, 15*mm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('LINEBELOW', (0,0), (-1,0), 0.5, colors.HexColor('#255F38')),
        ('LINEBELOW', (0,-1), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
    ]))
    story.append(table)
    story.append(Spacer(1, 2*mm))

    # Jami hisob-kitob
    summary_data = [
        ["Jami:", f"{int(receipt_data.get('subtotal', 0)):,} so'm".replace(',', ' ')],
        ["Chegirma:", f"{int(receipt_data.get('discount', 0)):,} so'm".replace(',', ' ')],
        ["To'lov:", f"{int(receipt_data.get('total', 0)):,} so'm".replace(',', ' ')],
        ["Usul:", receipt_data.get('payment_method', 'Naqd pul')]
    ]
    sum_table = Table(summary_data, colWidths=[35*mm, 37*mm])
    sum_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
    ]))
    story.append(sum_table)
    story.append(Spacer(1, 4*mm))

    # QR kod
    qr_token = receipt_data.get('qr_token')
    if qr_token:
        qr_temp_path = os.path.join(os.path.dirname(output_path), f"temp_qr_{receipt_data.get('receipt_number')}.png")
        generate_qr_code_image(qr_token, qr_temp_path)
        if os.path.exists(qr_temp_path):
            story.append(RLImage(qr_temp_path, width=22*mm, height=22*mm))
            story.append(Spacer(1, 2*mm))

    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=7,
        leading=9,
        alignment=1,
        textColor=colors.HexColor('#666666')
    )
    story.append(Paragraph("Xaridingiz uchun rahmat!", footer_style))
    story.append(Paragraph("Sog'lom turmush tarzi sari!", footer_style))

    doc.build(story)
    return output_path
