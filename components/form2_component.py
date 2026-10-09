import tkinter as tk
from tkinter import ttk, messagebox
import jdatetime

class Form2Component:
    def __init__(self, notebook, form1, form2sh):
        self.frame = ttk.Frame(notebook, padding="5")
        self.frame.pack(fill='both', expand=True)
        self.form1 = form1
        self.form2sh = form2sh
        self.entries = {}
        self.detail_entries = {}
        
        # Create main container
        main_container = ttk.Frame(self.frame)
        main_container.pack(fill='both', expand=True, padx=5, pady=2)
        
        self.focusable_entries = []
        self.create_widgets(main_container)

    def _create_entry(self, parent, is_readonly=False, width=12):
        state = 'readonly' if is_readonly else 'normal'
        bg = '#f0f0f0' if is_readonly else 'white'
        relief = 'sunken' if is_readonly else 'solid'
        return tk.Entry(parent, justify='center', state=state, 
                       bg=bg, font=('Tahoma', 10), bd=1, 
                       relief=relief, width=width)

    def create_widgets(self, parent):
        
        parent.rowconfigure(0, weight=1) # Give top section some weight
        parent.rowconfigure(1, weight=3) # Give bottom table more weight
        parent.columnconfigure(0, weight=1,minsize=10)
        # --- بخش ۱: خلاصه روزانه (بالای صفحه) ---
        summary_lf = ttk.LabelFrame(parent, text="خلاصه روزانه", padding=0)
        summary_lf.grid(row=0, column=0, sticky='nsew', pady=(0, 0))
        
        # Create 3 columns frame
        cols_frame = ttk.Frame(summary_lf)
        cols_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Configure 3 equal columns
        for i in range(3):
            cols_frame.grid_columnconfigure(i, weight=1, uniform="col")
        
        # تعریف فیلدها در ۳ ستون مطابق تصویر شما
        summary_fields = [
            [  # ستون اول
                (":موجودی آغازین", "start_inv"),
                (":موجودی پایانی", "end_inv"),
                (":اختلاف مکانیکی", "mech_diff"),
                (":رسیده", "received")
            ],
            [  # ستون دوم (وسط)
                (":فروش کل", "فروش کل"),
                (":مجموع کارتخوانها", "مجموع کارتخوان"),
                (" :کل نقدینگی", "مجموع نقد"),
                (":حواله", "هزینه/حواله")
            ],
            [  # ستون سوم
                (":مساعده و خرج", "expenses"),
                (":وجه موجود", "cash_available"),
                (":خروج به بانک", "bank_exit"),
                (":صندوق", "safe_box")
            ]
        ]
        
        # Create columns from right to left (Persian layout)
        for col_idx, col_data in enumerate(summary_fields):
            col_frame = ttk.Frame(cols_frame)
            col_frame.grid(row=0, column=col_idx, padx=10, sticky="nsew")
            col_frame.rowconfigure(list(range(4)), weight=1)
            
            for row_idx, (label_text, key) in enumerate(col_data):
                # Create a frame for each row
                row_frame = ttk.Frame(col_frame)
                row_frame.pack(fill='x', pady=2)
                
                
                # Label on right side
                lbl = tk.Label(row_frame, text=label_text, 
                              font=('Tahoma', 10),
                              anchor='e', width=18)
                lbl.pack(side='right', padx=(0, 8))
                
                # Entry on left side
                is_manual = key in ["start_inv", "end_inv", "mech_diff", 
                                   "received", "bank_exit", "safe_box"]
                entry = self._create_entry(row_frame, is_readonly=not is_manual, width=15)
                entry.pack(side='left', fill='x', expand=True)
                self.entries[key] = entry
                
                if is_manual:   # only editable fields
                    self.focusable_entries.append(entry)
                    self._bind_arrow_keys(entry)
                
                
        # --- بخش ۲: جزئیات شیفت‌ها (پایین صفحه) ---
        details_lf = ttk.LabelFrame(parent, text="جزئیات شیفت‌ها", padding=10)
        details_lf.grid(row=1, column=0, sticky='nsew', pady=(2, 0))
        
        # Configure 4 columns for the table
        for i in range(4):  # 4 columns as shown in your image
            details_lf.grid_columnconfigure(i, weight=1)
        
        # هدرهای جدول - 4 ستون مطابق تصویر
        headers = ["جمع کل / روز", "شیفت ۲", "شیفت ۱", "عنوان"]
        for i, h in enumerate(headers):
            header_label = tk.Label(details_lf, text=h, 
                                   font=('Tahoma', 9, 'bold'),
                                   bg='#e0e0e0', relief='ridge',
                                   padx=10, pady=5)
            header_label.grid(row=0, column=i, sticky="nsew", padx=1, pady=(0, 3))
        
        # ردیف‌های جدول دقیقاً مطابق تصویر شما
        rows = [
            ("شماره شیفت", "shift_id"),
            ("متصدیان", "operators"),
            ("فروش کل", "sales"),
            ("مجموع استعلام کارتخوان", "card_total"),
            ("فروش نقدی", "cash"),
            ("حواله های دولتی", "gov_vouchers"),
            ("کسری", "shortage"),
            ("مساعده و خرج", "expenses_det"),
            ("وجه موجود", "cash_on_hand"),
            ("توضیحات", "description")
        ]
        
        
        # ایجاد ردیف‌های جدول
        for r_idx, (label_text, key) in enumerate(rows, 1):  # Start from row 1
            details_lf.rowconfigure(r_idx, weight=1)
            # ستون عنوان (سمت راست - ستون 3)
            title_label = tk.Label(details_lf, text=f":{label_text}", 
                                font=('Tahoma', 10),
                                anchor='e', padx=10)
            title_label.grid(row=r_idx, column=3, sticky="e", padx=10, pady=3)

            # فیلدهای داده برای 3 ستون اول
            for c_idx, suffix in enumerate(["_sum", "_2", "_1"]):  # 0=جمع کل, 1=شیفت2, 2=شیفت1
                entry_frame = ttk.Frame(details_lf)
                entry_frame.grid(row=r_idx, column=c_idx, sticky="nsew", padx=2, pady=2)
                
                # تعیین اینکه فیلد فقط خواندنی باشد یا نه
                if key == "shift_id":
                    # شماره شیفت‌ها باید توسط کاربر وارد شوند (غیرفعال نیستند)
                    is_readonly = False
                    bg_color = '#fff8e1'  # رنگ متمایز برای فیلدهای اجباری
                    # تنظیم placeholder برای هر ستون
                    if suffix == "_1":
                        placeholder = "مثال: 1404/10/09/01"
                    elif suffix == "_2":
                        placeholder = "مثال: 1404/10/09/02"
                    else:  # _sum
                        placeholder = "تاریخ روز را وارد کنید"  # یا متن مناسب دیگر
                elif key in ["operators", "description"]:
                    is_readonly = False
                    bg_color = 'white'
                    placeholder = ""
                    if key == "description":
                        placeholder = "توضیحات را وارد کنید..."
                else:
                    is_readonly = True
                    bg_color = '#f5f5f5'
                    placeholder = ""
                
                entry_width = 20 if key == "description" else 15
                
                entry = tk.Entry(entry_frame, justify='center', state='normal' if not is_readonly else 'readonly',
                            bg=bg_color, font=('Tahoma', 10), bd=1, 
                            relief='solid', width=entry_width)
                entry.pack(fill='both', expand=True, ipady=5)
                
                if not is_readonly:
                    self.focusable_entries.append(entry)
                    self._bind_arrow_keys(entry)

                
                # تنظیم placeholder برای فیلدهای شماره شیفت
                if placeholder and key == "shift_id":
                    entry.config(fg='#999999')
                    entry.insert(0, placeholder)
                    
                    # تعریف توابع برای مدیریت placeholder
                    def on_focus_in(event, widget=entry, text=placeholder):
                        if widget.get() == text:
                            widget.delete(0, tk.END)
                            widget.config(fg='black')
                    
                    def on_focus_out(event, widget=entry, text=placeholder):
                        if widget.get() == "":
                            widget.insert(0, text)
                            widget.config(fg='#999999')
                        elif widget.get() != text:
                            widget.config(fg='black')
                    
                    entry.bind('<FocusIn>', on_focus_in)
                    entry.bind('<FocusOut>', on_focus_out)
                    
                    # برای فیلد شماره شیفت، اعتبارسنجی اضافه کنید
                    if suffix in ["_1", "_2"]:
                        # استفاده از lambda برای انتقال صحیح پارامترها
                        entry.bind('<FocusOut>', lambda e, s=suffix: self._validate_shift_id(s))
                
                self.detail_entries[f"{key}{suffix}"] = entry

    def _validate_shift_id(self, suffix, entry):
        """اعتبارسنجی شماره شیفت"""
        entry = self.detail_entries.get(f"shift_id{suffix}")
        if entry:
            value = entry.get().strip()
            placeholder = "مثال: 1404/10/09/01" if suffix == "_1" else "مثال: 1404/10/09/02"
            
            # اگر مقدار برابر placeholder است، خالی در نظر بگیر
            if value == placeholder:
                return True  # یا False بسته به اینکه می‌خواهید اجباری باشد یا نه
                
            if not value:
                messagebox.showwarning("هشدار", f"لطفاً شماره شیفت {suffix.replace('_', '')} را وارد کنید.")
                entry.focus_set()
                return False
        return True

    def _get_val(self, widget):
        if not widget: return 0.0
        s = widget.get().replace(',', '')
        return float(s) if s else 0.0

    def _set_val(self, widget, val):
        if widget:
            current_state = widget.cget('state')
            widget.config(state='normal')
            widget.delete(0, tk.END)
            widget.insert(0, f"{val:,.0f}")
            widget.config(state=current_state)
    
    def validate_shift_ids(self):
        """بررسی اینکه شماره شیفت‌ها وارد شده‌اند (نه placeholder)"""
        shift1_entry = self.detail_entries.get("shift_id_1")
        shift2_entry = self.detail_entries.get("shift_id_2")
        
        shift1 = shift1_entry.get().strip() if shift1_entry else ""
        shift2 = shift2_entry.get().strip() if shift2_entry else ""
        
        placeholder1 = "مثال: 1404/10/09/01"
        placeholder2 = "مثال: 1404/10/09/02"
        
        # اگر مقدار برابر placeholder است، خالی در نظر بگیر
        if shift1 == placeholder1:
            shift1 = ""
        if shift2 == placeholder2:
            shift2 = ""
        
        if not shift1:
            if shift1_entry:
                shift1_entry.focus_set()
            return False
            
        if not shift2:
            if shift2_entry:
                shift2_entry.focus_set()
            return False
        
        # ذخیره مقادیر واقعی (نه placeholder)
        self.shift_id_1 = shift1
        self.shift_id_2 = shift2
        
        return True

    def get_shift_ids(self):
        """دریافت شماره شیفت‌ها (بدون placeholder)"""
        shift1_entry = self.detail_entries.get("shift_id_1")
        shift2_entry = self.detail_entries.get("shift_id_2")
        
        shift1 = shift1_entry.get().strip() if shift1_entry else ""
        shift2 = shift2_entry.get().strip() if shift2_entry else ""
        
        placeholder1 = "مثال: 1404/10/09/01"
        placeholder2 = "مثال: 1404/10/09/02"
        
        # اگر مقدار برابر placeholder است، خالی برگردان
        if shift1 == placeholder1:
            shift1 = ""
        if shift2 == placeholder2:
            shift2 = ""
        
        return {
            'shift_id_1': shift1,
            'shift_id_2': shift2
        }
    
    def calculate(self):
        try:
            # # ۱. بررسی اینکه شماره شیفت‌ها وارد شده‌اند
            # if not self.validate_shift_ids():
            #     return
                
            # دریافت شماره شیفت‌ها
            shift_ids = self.get_shift_ids()
            
            # ۲. دریافت و ترکیب نام متصدیان
            ops1_list = []
            if hasattr(self.form1, 'operator_entry_1'): 
                op1_val = self.form1.operator_entry_1.get()
                if op1_val: ops1_list.append(op1_val)
            if hasattr(self.form1, 'operator_entry_2'): 
                op2_val = self.form1.operator_entry_2.get()
                if op2_val: ops1_list.append(op2_val)
            op1_combined = " - ".join(filter(None, ops1_list))

            ops2_list = []
            if hasattr(self.form2sh, 'operator_entry_1'): 
                op1_val = self.form2sh.operator_entry_1.get()
                if op1_val: ops2_list.append(op1_val)
            if hasattr(self.form2sh, 'operator_entry_2'): 
                op2_val = self.form2sh.operator_entry_2.get()
                if op2_val: ops2_list.append(op2_val)
            op2_combined = " - ".join(filter(None, ops2_list))

            # ۳. انتقال نام متصدیان
            operators_data = [
                ("operators_1", op1_combined),
                ("operators_2", op2_combined), 
                ("operators_sum", "حسابرس  : سهیل رباطی")
            ]
            
            for key, val in operators_data:
                ent = self.detail_entries.get(key)
                if ent:
                    ent.config(state='normal')
                    ent.delete(0, tk.END)
                    ent.insert(0, val)
                    # Keep operators as editable
                    if "_sum" not in key:
                        ent.config(state='normal')

            # ۴. دریافت مقادیر عددی
            sales1 = self._get_val(self.form1.total_sales_entry)
            card1 = self._get_val(self.form1.card_reader_total_entry)
            cash1 = self._get_val(self.form1.cash_entry)
            
            sales2 = self._get_val(self.form2sh.total_sales_entry)
            card2 = self._get_val(self.form2sh.card_reader_total_entry)
            cash2 = self._get_val(self.form2sh.cash_entry)

            # ۵. بروزرسانی ردیف‌های عددی
            # فروش کل
            if self.detail_entries.get("sales_1"):
                self._set_val(self.detail_entries.get("sales_1"), sales1)
            if self.detail_entries.get("sales_2"):
                self._set_val(self.detail_entries.get("sales_2"), sales2)
            if self.detail_entries.get("sales_sum"):
                self._set_val(self.detail_entries.get("sales_sum"), sales1 + sales2)

            # مجموع استعلام کارتخوان
            if self.detail_entries.get("card_total_1"):
                self._set_val(self.detail_entries.get("card_total_1"), card1)
            if self.detail_entries.get("card_total_2"):
                self._set_val(self.detail_entries.get("card_total_2"), card2)
            if self.detail_entries.get("card_total_sum"):
                self._set_val(self.detail_entries.get("card_total_sum"), card1 + card2)

            # فروش نقدی
            if self.detail_entries.get("cash_1"):
                self._set_val(self.detail_entries.get("cash_1"), cash1)
            if self.detail_entries.get("cash_2"):
                self._set_val(self.detail_entries.get("cash_2"), cash2)
            if self.detail_entries.get("cash_sum"):
                self._set_val(self.detail_entries.get("cash_sum"), cash1 + cash2)

            # وجه موجود
            if self.detail_entries.get("cash_on_hand_1"):
                self._set_val(self.detail_entries.get("cash_on_hand_1"), cash1)
            if self.detail_entries.get("cash_on_hand_2"):
                self._set_val(self.detail_entries.get("cash_on_hand_2"), cash2)
            if self.detail_entries.get("cash_on_hand_sum"):
                self._set_val(self.detail_entries.get("cash_on_hand_sum"), cash1 + cash2)

            # ۶. بروزرسانی خلاصه روزانه
            total_sales_day = sales1 + sales2
            total_card_day = card1 + card2
            total_cash_day = cash1 + cash2
            
            if self.entries.get("فروش کل"):
                self._set_val(self.entries.get("فروش کل"), total_sales_day)
            if self.entries.get("مجموع کارتخوان"):
                self._set_val(self.entries.get("مجموع کارتخوان"), total_card_day)
            if self.entries.get("مجموع نقد"):
                self._set_val(self.entries.get("مجموع نقد"), total_cash_day)
            
            # ۷. محاسبه وجه موجود
            cash_available = total_cash_day
            if self.entries.get("cash_available"):
                self._set_val(self.entries.get("cash_available"), cash_available)

            print("تمامی محاسبات مالی و انتقال متصدیان با موفقیت انجام شد.")

        except Exception as e:
            messagebox.showerror("خطای محاسباتی", 
                               f"مشکلی در بروزرسانی فرم مالی رخ داد:\n{str(e)}")
            
    def _bind_arrow_keys(self, widget):
        widget.bind("<Up>", self._focus_prev)
        widget.bind("<Down>", self._focus_next)
        widget.bind("<Left>", self._focus_prev)
        widget.bind("<Right>", self._focus_next)

    def get_shift_id_sum(self):
        entry = self.detail_entries.get("shift_id_sum")
        if entry:
            val = entry.get().strip()
            if val and val != "تاریخ روز را وارد کنید": 
                return val
        return None

    def _focus_next(self, event):
        try:
            idx = self.focusable_entries.index(event.widget)
            next_widget = self.focusable_entries[(idx + 1) % len(self.focusable_entries)]
            next_widget.focus_set()
        except ValueError:
            pass
        return "break"

    def _focus_prev(self, event):
        try:
            idx = self.focusable_entries.index(event.widget)
            prev_widget = self.focusable_entries[(idx - 1) % len(self.focusable_entries)]
            prev_widget.focus_set()
        except ValueError:
            pass
        return "break"

