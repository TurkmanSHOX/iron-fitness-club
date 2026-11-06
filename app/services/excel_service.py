import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def export_to_excel(title, headers, rows, output_path, summary_rows=None):
    """
    Professional Excel hisobotini yaratadi.
    title: Hisobot sarlavhasi
    headers: ['Ustun 1', 'Ustun 2', ...]
    rows: [[val1, val2, ...], ...]
    summary_rows: [('Jami tushum:', '1 500 000 so\'m'), ...]
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Hisobot"

    # Stillar
    title_font = Font(name="Arial", size=14, bold=True, color="255F38")
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="255F38", end_color="255F38", fill_type="solid")
    regular_font = Font(name="Arial", size=10)
    summary_font = Font(name="Arial", size=11, bold=True)
    
    thin_border = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )

    # 1. Sarlavha
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
    title_cell = ws.cell(row=1, column=1, value=title)
    title_cell.font = title_font
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    # 2. Ustun sarlavhalari
    header_row_idx = 3
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=header_row_idx, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws.row_dimensions[header_row_idx].height = 25

    # 3. Ma'lumot qatorlari
    current_row = header_row_idx + 1
    for row_data in rows:
        for col_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=current_row, column=col_idx, value=val)
            cell.font = regular_font
            cell.border = thin_border
            # Pul yoki son bo'lsa o'ngga surish
            if isinstance(val, (int, float)):
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")
        current_row += 1

    # 4. Yakuniy xulosa qatorlari
    if summary_rows:
        current_row += 1
        for s_title, s_val in summary_rows:
            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=len(headers)-1)
            cell_lbl = ws.cell(row=current_row, column=1, value=s_title)
            cell_lbl.font = summary_font
            cell_lbl.alignment = Alignment(horizontal="right", vertical="center")

            cell_val = ws.cell(row=current_row, column=len(headers), value=s_val)
            cell_val.font = summary_font
            cell_val.alignment = Alignment(horizontal="right", vertical="center")
            current_row += 1

    # Ustun kengliklarini avtomatik moslash
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or '')
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    wb.save(output_path)
    return output_path
