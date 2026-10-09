import os
import tkinter as tk
from tkinter import filedialog, messagebox
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit
from utils.persian_utils import reshape_persian_text, get_bidi_text
import sys

def get_resource_path(relative_path):
    """مسیر منابع را در حالت exe و اسکریپت برمی‌گرداند"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class PDFExporter:
    def __init__(self, form1, form2sh, form2, form3, result_text):
        self.form1 = form1
        self.form2sh = form2sh
        self.form2 = form2
        self.form3 = form3
        self.result_text = result_text
        self.has_persian_font = self.load_persian_font()
          

    def load_persian_font(self):
        font_paths = [
            get_resource_path("fonts/Vazir.ttf"),
            get_resource_path("fonts/Vazir-Bold.ttf"),
            "C:/Windows/Fonts/Tahoma.ttf",
            "C:/Windows/Fonts/Arial.ttf",
        ]
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    pdfmetrics.registerFont(TTFont('Persian', fp))
                    return True
                except Exception:
                    continue
        return False

    def _prepare_text(self, text):
        if not text: return ""
        text = str(text).replace('0','۰').replace('1','۱').replace('2','۲').replace('3','۳').replace('4','۴').replace('5','۵').replace('6','۶').replace('7','۷').replace('8','۸').replace('9','۹')
        return get_bidi_text(reshape_persian_text(text))

    def _draw_persian_text(self, c, text, x, y, size=10, align='right'):
        if not self.has_persian_font: return
        c.setFont("Persian", size)
        txt = self._prepare_text(text)
        if align == 'right': c.drawRightString(x, y, txt)
        elif align == 'center': c.drawCentredString(x, y, txt)
        else: c.drawString(x, y, txt)
        
    def _draw_centered_text(self, c, text, x, y, w, h, size=9):
        center_x = x + w / 2
        center_y = y + (h / 2) - (size / 4)
        self._draw_persian_text(c, text, center_x, center_y, size, align='center')    

    def validate_shift_ids(self):
        """بررسی اینکه شماره شیفت‌ها وارد شده‌اند"""
        if not hasattr(self.form2, 'validate_shift_ids'):
            return True
            
        return self.form2.validate_shift_ids()
    
    def get_shift_titles(self):
        """دریافت عنوان‌ها با شماره شیفت"""
        shift_ids = self.form2.get_shift_ids() if hasattr(self.form2, 'get_shift_ids') else {'shift_id_1': '', 'shift_id_2': ''}
        
        title1 = f"فرم شماره ۱ - شیفت اول: {shift_ids['shift_id_1']}" if shift_ids['shift_id_1'] else "فرم شماره ۱ - شیفت اول"
        title2 = f"فرم شماره ۱.۲ - شیفت دوم: {shift_ids['shift_id_2']}" if shift_ids['shift_id_2'] else "فرم شماره ۱.۲ - شیفت دوم"
        
        return title1, title2
    
    def get_shift1_value(self):
        """
        دریافت مقدار شماره شیفت ۱ از فرم مالی (Form2)
        برای استفاده به عنوان نام فایل PDF
        """
        if hasattr(self.form2, 'detail_entries'):
            shift1_entry = self.form2.detail_entries.get("shift_id_1")
            if shift1_entry:
                value = shift1_entry.get().strip()
                # حذف placeholder اگر بود
                placeholder = "مثال: 1404/10/09/01"
                if value and value != placeholder:
                    return value
        return None

    def print_forms_pdf(self):
        default_filename = self.get_default_filename()
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=default_filename   # <-- اینجا مقدار پیش‌فرض رو می‌ذاره
        )
        if not filename:
            return
        
        try:
            # ۱. بررسی اجباری بودن شماره شیفت‌ها
            if not self.validate_shift_ids():
                messagebox.showerror("خطا", "لطفاً قبل از چاپ، شماره شیفت‌ها را در فرم مالی وارد کنید.")
                return
            
            # ۲. دریافت عنوان‌ها با شماره شیفت
            title1, title2 = self.get_shift_titles()
            
            # دریافت عبارت "جمع کل / روز" از فرم 2
            total_day_value = ""
            if hasattr(self.form2, 'detail_entries'):
                # دریافت مقدار از فیلد shift_id_sum (مطابق فرم 2 شما)
                shift_id_sum_entry = self.form2.detail_entries.get("shift_id_sum")
                if shift_id_sum_entry:
                    total_day_value = shift_id_sum_entry.get()
            
            c = canvas.Canvas(filename, pagesize=landscape(A4))
            width, height = landscape(A4)
            margin = 10 * mm
            page_width = width - 2 * margin
            
            # صفحه ۱: شیفت اول - با عبارت جمع کل / روز و شماره شیفت
            self.draw_shift_form(c, self.form1, title1, width, height, total_day_value)
            c.showPage()
            
            # صفحه ۲: شیفت دوم - با عبارت جمع کل / روز و شماره شیفت
            c.setPageSize(landscape(A4))
            width, height = landscape(A4)
            self.draw_shift_form(c, self.form2sh, title2, width, height, total_day_value)
            c.showPage()
            
            # صفحه ۳: فرم مالی (عمودی) - با عبارت جمع کل / روز
            c.setPageSize(A4)
            width, height = A4
            margin = 10 * mm
            page_width = width - 2 * margin
            self.draw_form2_page(c, width, height, margin, page_width, total_day_value)
            c.showPage()
            
            # صفحه ۴: شمارنده‌ها (در حالت افقی) - با عبارت جمع کل / روز
            self.draw_form3_page(c, width, height, margin, page_width, total_day_value)
            
            c.save()
            messagebox.showinfo("موفقیت", "گزارش PDF کامل با موفقیت ذخیره شد.")
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در تولید PDF: {str(e)}")
            
    def _draw_page_header(self, c, width, height, total_day_value):
        """رسم هدر در بالای هر صفحه با عبارت جمع کل / روز"""
        if not total_day_value:
            return
        
        margin = 10 * mm
        
        # ایجاد یک نوار هدر در بالای صفحه
        header_height = 8 * mm
        header_y = height - header_height
        
        # رنگ پس‌زمینه هدر (سبز کمرنگ)
        c.setFillColorRGB(0.9, 0.95, 0.9)
        c.rect(0, header_y, width, header_height, fill=1, stroke=0)
        
        # متن هدر
        c.setFillColorRGB(0, 0, 0)
        header_text = f"تاریخ روز: {total_day_value}"
        
        # استفاده از فونت فارسی
        if self.has_persian_font:
            c.setFont("Persian", 10)
            prepared_text = self._prepare_text(header_text)
            c.drawCentredString(width / 2, header_y + 2*mm, prepared_text)
        else:
            c.setFont("Helvetica", 10)
            c.drawCentredString(width / 2, header_y + 2*mm, header_text)
        
        # خط جداکننده
        c.setLineWidth(0.5)
        c.line(margin, header_y - 1*mm, width - margin, header_y - 1*mm)

    def draw_shift_form(self, c, form, title, w, h, total_day_value=None):
        # رسم هدر
        if total_day_value:
            self._draw_page_header(c, w, h, total_day_value)
        
        margin = 10 * mm
        
        # تنظیم موقعیت Y با در نظر گرفتن هدر
        header_offset = 15 * mm if total_day_value else 0
        
        # عنوان اصلی با فاصله از هدر (با شماره شیفت)
        self._draw_persian_text(c, title, w/2, h - 20*mm - header_offset, 14, 'center')
        active_nozzles = sorted(list(form.entries.keys()))
        
        # محاسبه عرض برای جداول کنار هم
        available_width = w - 2 * margin
        table_gap = 20 * mm  # فاصله بین دو جدول
        nozzle_table_width = available_width * 0.45  # 45% برای جدول نازل‌ها
        finance_table_width = available_width * 0.55 - table_gap  # 55% برای جدول مالی
        
        # موقعیت‌های X برای جداول
        finance_x = margin  # جدول مالی از سمت چپ شروع می‌شود (اولین جدول)
        nozzle_x = finance_x + finance_table_width + table_gap  # جدول نازل‌ها در سمت راست
        
        # ارتفاع شروع برای هر دو جدول - با در نظر گرفتن هدر
        y_start = h - 40*mm - header_offset
        
        # 1. جدول محاسبات مالی (سمت چپ) - اولین جدول در چیدمان فارسی
        y_fin = y_start
        w_fin = finance_table_width
        
        # Calculate total azad (sum of both azad entries)
        if hasattr(form, 'total_azad_entry_1') and hasattr(form, 'total_azad_entry_2'):
            azad_liters = self._get_value(form.total_azad_entry_1) + self._get_value(form.total_azad_entry_2)
            azad_price = self._get_value(form.price_azad_total_1) + self._get_value(form.price_azad_total_2)
        else:
            azad_liters = self._get_value(getattr(form, 'total_azad_entry', 0))
            azad_price = self._get_value(getattr(form, 'price_azad_total', 0))

        fin_data = [
            ("الکتریکی کل", form.total_elec_entry.get(), "-", "-"),
            ("یارانه", form.total_subsidy_entry.get(), "15,000", form.price_subsidy_total.get()),
            ("نیمه یارانه", form.total_semi_entry.get(), "30,000", form.price_semi_total.get()),
            ("آزاد", str(int(azad_liters)), "50,000", str(int(azad_price))),
        ]
   
        
        # هدر مالی - ترتیب ستون‌ها از راست به چپ: عنوان، لیتر، فی، مبلغ
        fin_headers = ["عنوان", "لیتر", "فی", "مبلغ"]
        col_fw = w_fin / 4
        
        # هدر جدول مالی (ستون‌ها از راست به چپ)
        c.setFillColorRGB(0.95, 0.95, 0.95)
        for i, h_txt in enumerate(fin_headers):
            x_rect = finance_x + i * col_fw  # تغییر: از چپ به راست می‌رود
            c.rect(x_rect, y_fin-2*mm, col_fw, 8*mm, fill=1, stroke=1)
        
        c.setFillColorRGB(0, 0, 0)
        for i, h_txt in enumerate(fin_headers):
            # متن در مرکز هر ستون
            self._draw_persian_text(c, h_txt, finance_x + i * col_fw + col_fw/2, y_fin, 9, 'center')
            
        y_fin -= 8*mm
        
        # ردیف‌های جدول مالی - ترتیب: عنوان، لیتر، فی، مبلغ (از راست به چپ)
        for row in fin_data:
            for i, val in enumerate(row):
                self._draw_persian_text(c, str(val), finance_x + i * col_fw + col_fw/2, y_fin, 9, 'center')
                c.rect(finance_x + i * col_fw, y_fin-2*mm, col_fw, 8*mm)
            y_fin -= 8*mm
            
        
        # 2. جدول نازل‌ها (سمت راست) - دومین جدول در چیدمان فارسی
        y = y_start
        col_w = nozzle_table_width / 4  # 4 ستون
        headers = ["نازل", "پایان", "آغاز", "کارکرد"]
        
        # هدر جدول نازل‌ها - ترتیب ستون‌ها از راست به چپ: نازل، پایان، آغاز، کارکرد
        c.setFillColorRGB(0.95, 0.95, 0.95)
        for i, head in enumerate(headers):
            x = nozzle_x + i * col_w  # تغییر: از چپ به راست می‌رود
            c.rect(x, y-2*mm, col_w, 8*mm, fill=1, stroke=1)
        
        c.setFillColorRGB(0, 0, 0)
        for i, head in enumerate(headers):
            x = nozzle_x + i * col_w
            self._draw_persian_text(c, head, x + col_w/2, y, 10, 'center')
        
        y -= 8*mm
        
        # ردیف‌های جدول نازل‌ها - ترتیب: نازل، پایان، آغاز، کارکرد (از راست به چپ)
        for nozzle in active_nozzles:
            row = form.entries.get(nozzle)
            if not row: continue
            vals = [str(nozzle), row['پایان'].get(), row['آغاز'].get(), row['کارکرد'].get()]
            for i, val in enumerate(vals):
                x = nozzle_x + i * col_w + col_w/2
                self._draw_persian_text(c, val, x, y, 9, 'center')
                c.rect(nozzle_x + i * col_w, y-2*mm, col_w, 8*mm)
            y -= 8*mm
            
        # ردیف "جمع کل مکانیکی" - این بخش جدید است
        c.setFillColorRGB(0.95, 0.95, 0.95)  # رنگ خاکستری تیره‌تر برای ردیف جمع
        
        # ستون‌های 0-2 (نازل و متن "جمع کل مکانیکی:")
        c.rect(nozzle_x, y-2*mm, col_w * 3, 8*mm, fill=1, stroke=1)
        
        # ستون آخر (مقدار جمع کل)
        c.rect(nozzle_x + 3*col_w, y-2*mm, col_w, 8*mm, fill=1, stroke=1)
        
        c.setFillColorRGB(0, 0, 0)
        
        # متن "جمع کل مکانیکی:" در مرکز سه ستون اول
        self._draw_persian_text(c, "جمع کل مکانیکی", 
                               nozzle_x + (col_w * 3) / 2, y, 10, 'center')
        
        # مقدار جمع کل در ستون آخر
        total_mech_value = form.total_mech_display.get() if hasattr(form, 'total_mech_display') else "0"
        self._draw_persian_text(c, total_mech_value, 
                               nozzle_x + 3*col_w + col_w/2, y, 10, 'center')
        
        y -= 8*mm
        
        # جمع فروش - کمی پایین‌تر از جدول مالی
        # تنظیم موقعیت جمع فروش با در نظر گرفتن هدر
        y_fin_adj = y_fin - 10*mm
        self._draw_persian_text(c, "جمع کل فروش:", finance_x + w_fin - 10*mm, y_fin_adj, 10, 'right')
        self._draw_persian_text(c, form.total_sales_entry.get(), finance_x + 20*mm, y_fin_adj, 10, 'left')
        
        # کارتخوان و نقد - زیر جمع فروش
        y_fin_adj -= 10*mm
        self._draw_persian_text(c, "جمع کارتخوان:", finance_x + w_fin - 10*mm, y_fin_adj, 10, 'right')
        self._draw_persian_text(c, form.card_reader_total_entry.get(), finance_x + 20*mm, y_fin_adj, 10, 'left')
        
        y_fin_adj -= 10*mm
        self._draw_persian_text(c, "وجه نقد:", finance_x + w_fin - 10*mm, y_fin_adj, 10, 'right')
        self._draw_persian_text(c, form.cash_entry.get(), finance_x + 20*mm, y_fin_adj, 10, 'left')
        
    def draw_form2_page(self, c, width, height, margin, page_width, total_day_value=None):
        # رسم هدر
        if total_day_value:
            self._draw_page_header(c, width, height, total_day_value)
        
        # تنظیم موقعیت Y با در نظر گرفتن هدر
        header_offset = 15 * mm if total_day_value else 0
        
        # ۱. تنظیمات اولیه و عنوان
        self._draw_persian_text(c, "فرم شماره ۲ - اطلاعات مالی", width / 2, height - 15*mm - header_offset, 14, align='center')
        
        # ۲. بخش خلاصه روزانه (استفاده از حداکثر فضا)
        # تنظیم موقعیت Y با در نظر گرفتن هدر
        y_summary = height - 25*mm - header_offset
        summary_height = 45*mm 
        inner_margin = 5*mm
        c.setLineWidth(1)
        c.rect(margin, y_summary - summary_height, page_width, summary_height)
        
        self._draw_persian_text(c, "خلاصه روزانه (واحد: ریال / لیتر):", width - margin - 5*mm, y_summary - 5*mm, 11)
        
        # دریافت مقادیر از entries (بخش خلاصه روزانه)
        total_sales = self.form2.entries.get("فروش کل").get() if self.form2.entries.get("فروش کل") else "0"
        total_card = self.form2.entries.get("مجموع کارتخوان").get() if self.form2.entries.get("مجموع کارتخوان") else "0"
        total_cash = self.form2.entries.get("مجموع نقد").get() if self.form2.entries.get("مجموع نقد") else "0"
        
        # وجه موجود (که همان مجموع نقدی است)
        cash_available = self.form2.entries.get("cash_available").get() if self.form2.entries.get("cash_available") else "0"
        
        # سایر فیلدها (اگر کاربر پر کرده)
        expenses = self.form2.entries.get("هزینه/حواله").get() if self.form2.entries.get("هزینه/حواله") else "...................."
        start_inv = self.form2.entries.get("start_inv").get() if self.form2.entries.get("start_inv") else "...................."
        end_inv = self.form2.entries.get("end_inv").get() if self.form2.entries.get("end_inv") else "...................."
        mech_diff = self.form2.entries.get("mech_diff").get() if self.form2.entries.get("mech_diff") else "...................."
        expenses_det = self.form2.entries.get("expenses").get() if self.form2.entries.get("expenses") else "...................."
        received = self.form2.entries.get("received").get() if self.form2.entries.get("received") else "...................."
        bank_exit = self.form2.entries.get("bank_exit").get() if self.form2.entries.get("bank_exit") else "...................."
        safe_box = self.form2.entries.get("safe_box").get() if self.form2.entries.get("safe_box") else "...................."

        # چیدمان خلاصه در ردیف‌های عریض
        line_x1, line_x2, line_x3 = margin + 5*mm, width/2, width - margin - 5*mm
        curr_y = y_summary - 15*mm
        
        # ردیف ۱
        self._draw_persian_text(c, f"فروش کل: {total_sales}", line_x3, curr_y)
        self._draw_persian_text(c, f"مجموع کارتخوان‌ها: {total_card}", line_x2, curr_y, align='center')
        self._draw_persian_text(c, f"نقد دو شیفت: {total_cash}", line_x1, curr_y, align='left')
        
        # ردیف ۲
        curr_y -= 8*mm
        self._draw_persian_text(c, f"حواله: {expenses}", line_x3, curr_y)
        self._draw_persian_text(c, f"موجودی آغازین: {start_inv}", line_x2, curr_y, align='center')
        self._draw_persian_text(c, f"موجودی پایانی: {end_inv}", line_x1, curr_y, align='left')
        
        # ردیف ۳
        curr_y -= 8*mm
        self._draw_persian_text(c, f"اختلاف مکانیکی: {mech_diff}", line_x3, curr_y)
        self._draw_persian_text(c, f"مساعده و خرج: {expenses_det}", line_x2, curr_y, align='center')
        self._draw_persian_text(c, f"وجه موجود: {cash_available}", line_x1, curr_y, align='left')  # وجه موجود
        
        # ردیف ۴
        curr_y -= 8*mm
        self._draw_persian_text(c, f"رسیده: {received}", line_x3, curr_y)
        self._draw_persian_text(c, f"خروج به بانک: {bank_exit}", line_x2, curr_y, align='center')
        self._draw_persian_text(c, f"صندوق: {safe_box}", line_x1, curr_y, align='left')

        # ۳. جدول جزئیات شیفت‌ها (بخش پایین)
        y_pos = y_summary - summary_height - 10*mm
        row_height = 9*mm
        col_width = page_width / 4
        col_pos = [margin + i * col_width for i in range(4)]

        # هدر جدول
        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(margin, y_pos, page_width, row_height, fill=1)
        c.setFillColorRGB(0, 0, 0)
        headers = ["جمع کل / روز", "شیفت ۲", "شیفت ۱", "عنوان"]
        for i, txt in enumerate(headers):
            self._draw_centered_text(c, txt, col_pos[i], y_pos, col_width, row_height, 10)
        
        y_pos -= row_height

        # ردیف‌های جدول - تطبیق نام کلیدها با فایل form2_component.py
        rows_cfg = [
            ("شماره شیفت", "shift_id"),
            ("متصدیان", "operators"),
            ("فروش کل", "sales"),
            ("مجموع استعلام کارتخوان", "card_total"),
            ("فروش نقدی", "cash"),
            ("حواله‌های دولتی", "gov_vouchers"),
            ("کسری", "shortage"),
            ("مساعده و خرج", "expenses_det"),
            ("وجه موجود", "cash_on_hand"),
            ("توضیحات", "description")
        ]

        for label, key in rows_cfg:
            # دریافت مقادیر از detail_entries (مطابق فایل ارسالی شما)
            v1 = self.form2.detail_entries.get(f"{key}_1").get() if self.form2.detail_entries.get(f"{key}_1") else ""
            v2 = self.form2.detail_entries.get(f"{key}_2").get() if self.form2.detail_entries.get(f"{key}_2") else ""
            v_sum = self.form2.detail_entries.get(f"{key}_sum").get() if self.form2.detail_entries.get(f"{key}_sum") else ""
            
            row_data = [v_sum, v2, v1, label]
            for i, val in enumerate(row_data):
                self._draw_centered_text(c, str(val), col_pos[i], y_pos, col_width, row_height, 9)
            
            c.grid(col_pos + [width - margin], [y_pos, y_pos + row_height])
            y_pos -= row_height

        # ۴. امضا
        self._draw_persian_text(c, "محل تایید و امضاء مدیریت:", margin + 50*mm, y_pos - 10*mm, 10)
            
    def draw_form3_page(self, c, width, height, margin, page_width, total_day_value=None):
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import mm

        c.setPageSize(landscape(A4))
        width, height = c._pagesize
        
        if total_day_value:
            self._draw_page_header(c, width, height, total_day_value)

        margin = 10 * mm
        page_width = width - 2 * margin

        header_offset = 15 * mm if total_day_value else 0
        
        self._draw_persian_text(
            c, "فرم شماره ۳ - شمارنده‌ها و خلاصه مکانیکی",
            width / 2, height - (15 * mm) - header_offset, 14, align='center'
        )

        # دریافت لیست نازل‌های فعال از form3
        active_nozzles = sorted(list(self.form3.active_nozzles_sorted))
        
        # تقسیم نازل‌ها به دو گروه
        mid_point = len(active_nozzles) // 2
        first_group = active_nozzles[:mid_point]
        second_group = active_nozzles[mid_point:]

        # --- بخش اول: شمارنده‌ها (دو جدول زیر هم) ---
        y_pos = height - (30 * mm) - header_offset
        self._draw_persian_text(c, "شمارنده‌ها", width / 2, y_pos, 12, align='center')
        y_pos -= (10 * mm)

        table_width = page_width
        col_width = table_width / (len(first_group) + 1)  # +1 برای ستون عنوان
        row_height = 8 * mm
        table_x = margin

        # تابع کمکی برای رسم جدول شمارنده‌ها
        def draw_counter_table(nozzle_list, y_start):
            if not nozzle_list:  # اگر لیست خالی بود
                return y_start - (10 * mm)
                
            headers = ["شمارنده"] + [str(n) for n in nozzle_list]
            col_pos = [table_x + i * col_width for i in range(len(headers))]

            # ۱. هدر - خاکستری
            c.setFillColorRGB(0.95, 0.95, 0.95)
            for i, header in enumerate(headers):
                c.rect(col_pos[i], y_start, col_width, row_height, fill=1, stroke=1)
            
            # متن هدر
            c.setFillColorRGB(0, 0, 0)
            for i, header in enumerate(headers):
                self._draw_centered_text(c, header, col_pos[i], y_start, col_width, row_height, 9)
            
            c.grid(col_pos + [table_x + table_width], [y_start, y_start + row_height])
            y = y_start - row_height

            # ۲. ردیف آغاز
            c.setFillColorRGB(0.95, 0.95, 0.95)
            c.rect(col_pos[0], y, col_width, row_height, fill=1, stroke=1)
            c.setFillColorRGB(1, 1, 1)
            for i in range(1, len(nozzle_list) + 1):
                c.rect(col_pos[i], y, col_width, row_height, fill=1, stroke=1)
            
            c.setFillColorRGB(0, 0, 0)
            self._draw_centered_text(c, "آغاز", col_pos[0], y, col_width, row_height, 9)
            for i, pump_num in enumerate(nozzle_list):
                entry = self.form3.entries.get("آغاز", {}).get(pump_num)
                val = entry.get() if entry else ""
                self._draw_centered_text(c, val, col_pos[i + 1], y, col_width, row_height, 8)
            c.grid(col_pos + [table_x + table_width], [y, y + row_height])
            y -= row_height

            # ۳. ردیف پایان
            c.setFillColorRGB(0.95, 0.95, 0.95)
            c.rect(col_pos[0], y, col_width, row_height, fill=1, stroke=1)
            c.setFillColorRGB(1, 1, 1)
            for i in range(1, len(nozzle_list) + 1):
                c.rect(col_pos[i], y, col_width, row_height, fill=1, stroke=1)
            
            c.setFillColorRGB(0, 0, 0)
            self._draw_centered_text(c, "پایان", col_pos[0], y, col_width, row_height, 9)
            for i, pump_num in enumerate(nozzle_list):
                entry = self.form3.entries.get("پایان", {}).get(pump_num)
                val = entry.get() if entry else ""
                self._draw_centered_text(c, val, col_pos[i + 1], y, col_width, row_height, 8)
            c.grid(col_pos + [table_x + table_width], [y, y + row_height])
            y -= row_height

            # ۴. ردیف حاصل
            c.setFillColorRGB(0.95, 0.95, 0.95)
            c.rect(col_pos[0], y, col_width, row_height, fill=1, stroke=1)
            c.setFillColorRGB(1, 1, 1)
            for i in range(1, len(nozzle_list) + 1):
                c.rect(col_pos[i], y, col_width, row_height, fill=1, stroke=1)
            
            c.setFillColorRGB(0, 0, 0)
            self._draw_centered_text(c, "حاصل", col_pos[0], y, col_width, row_height, 9)
            for i, pump_num in enumerate(nozzle_list):
                entry = self.form3.entries.get("حاصل", {}).get(pump_num)
                val = entry.get() if entry else ""
                self._draw_centered_text(c, val, col_pos[i + 1], y, col_width, row_height, 8)
            c.grid(col_pos + [table_x + table_width], [y, y + row_height])

            return y - (15 * mm)  # فاصله بین جداول
        
        # رسم جدول اول با گروه اول نازل‌ها
        if first_group:
            y_pos = draw_counter_table(first_group, y_pos)
        
        # رسم جدول دوم با گروه دوم نازل‌ها
        if second_group:
            y_pos = draw_counter_table(second_group, y_pos)

        # --- بخش دوم: خلاصه مکانیکی ---
        y_summary = y_pos - (20 * mm)

        self._draw_persian_text(c, "جدول محاسبات نهایی (لیتر)", width / 2, y_summary, 12, align='center')
        y_summary -= (10 * mm)

        summary_headers = ["شیفت ۱", "شیفت ۲", "روزانه", "مجموع الکتریکی", "یارانه کل", "نیمه یارانه کل", "آزاد کل", "مخزن کل"]
        summary_table_width = page_width
        summary_col_width = summary_table_width / len(summary_headers)
        summary_col_pos = [margin + i * summary_col_width for i in range(len(summary_headers))]
        row_height = 8 * mm

        # هدر جدول خلاصه
        for i, header in enumerate(summary_headers):
            c.setFillColorRGB(0.95, 0.95, 0.95)
            c.rect(summary_col_pos[i], y_summary, summary_col_width, row_height, fill=1)
            c.setFillColorRGB(0, 0, 0)
            self._draw_centered_text(c, header, summary_col_pos[i], y_summary, summary_col_width, row_height, 9)
        c.grid(summary_col_pos + [width - margin], [y_summary, y_summary + row_height])
        y_summary -= row_height

        # مقادیر جدول خلاصه
        for i, key in enumerate(summary_headers):
            entry = self.form3.new_table_entries.get(key)
            val = entry.get() if entry else "0"
            self._draw_centered_text(c, val, summary_col_pos[i], y_summary, summary_col_width, row_height, 9)
        c.grid(summary_col_pos + [width - margin], [y_summary, y_summary + row_height])
        
    def _get_value(self, widget):
        if not widget:
            return 0.0
        s = widget.get().replace(',', '')
        try:
            return float(s) if s else 0.0
        except ValueError:
            return 0.0  
        
    def get_default_filename(self):
        """
        ساخت نام پیش‌فرض فایل بر اساس شماره شیفت ۱
        """
        shift1 = self.get_shift1_value()
        if shift1:
            # حذف کاراکترهای غیرمجاز در نام فایل
            safe_name = shift1.replace('/', '-').replace('\\', '-').replace(':', '-').replace('*', '-').replace('?', '-')
            return f"{safe_name}.pdf"
        return "گزارش_پمپ_بنزین.pdf" 