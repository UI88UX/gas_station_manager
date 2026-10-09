import tkinter as tk
from tkinter import ttk, messagebox

class Form1Component:
    PRICE_SUBSIDY = 15000      
    PRICE_SEMI_SUBSIDY = 30000 
    PRICE_FREE = 100000         

    HEADERS = ["نازل", "پایان", "آغاز", "کارکرد"]

    def __init__(self, notebook, shift_id):
        self.frame = ttk.Frame(notebook)
        self.shift_id = shift_id
        self.warning_shown = False
        self.entries = {}
        self.total_azad_entry_1 = None  # یا مقداردهی اولیه
        self.total_azad_entry_2 = None
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.font_header = ('Tahoma', 10, 'bold')
        self.font_normal = ('Tahoma', 10)
        self.font_bold = ('Tahoma', 10, 'bold')
        self.bg_readonly = '#f0f4f8'  
        self.bg_editable = '#ffffff'  
        
        self.validate_cmd = self.frame.register(self._validate_numeric)
        self.create_widgets()
        self._setup_auto_calculate()

    def _validate_numeric(self, P):
        if P == "":
            return True
        if "-" in P:
            return False
        clean_P = P.replace(',', '')
        try:
            float(clean_P)
            return float(clean_P) >= 0
        except ValueError:
            return False

    def _format_number(self, event):
        entry = event.widget
        value = entry.get().replace(',', '')
        if value:
            try:
                if '.' in value:
                    formatted = f"{float(value):,.2f}"
                    if formatted.endswith('.00'): formatted = formatted[:-3]
                else:
                    formatted = f"{int(float(value)):,}"
                entry.delete(0, tk.END)
                entry.insert(0, formatted)
            except ValueError:
                pass  
            
    def _format_mech_value(self, value):
        try:
            float_value = float(value)
            if float_value.is_integer():
                return f"{int(float_value)}"
            else:
                return f"{float_value:.2f}"
        except (ValueError, TypeError):
            return value
        
    def _format_card_entry(self, entry):
        try:
            val = self._convert_to_float(entry.get())
            entry.delete(0, tk.END)
            entry.insert(0, f"{int(val):,}")
        except Exception:
            pass

    def create_widgets(self):
        self.financial_entries = []
        self.frame.pack(fill='both', expand=True)
        main_container = ttk.Frame(self.frame, padding=5)
        main_container.pack(fill='both', expand=True)

        # 1. Main Header
        header_lbl = tk.Label(main_container, text=f"📋 فرم ثبت اطلاعات پمپ بنزین - شیفت: {self.shift_id}", 
                              font=('Tahoma', 12, 'bold'), bg='#37474f', fg='white', pady=10)
        header_lbl.pack(fill='x', pady=(0, 5))

        # 2. Content Area (Split 50/50)
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill='both', expand=True)
        
        content_frame.columnconfigure(0, weight=1, uniform="cols")
        content_frame.columnconfigure(1, weight=1, uniform="cols")
        content_frame.rowconfigure(0, weight=1)

        # ===========================
        # LEFT PANEL: Nozzles
        # ===========================
        left_panel = ttk.Frame(content_frame)
        left_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        left_panel.rowconfigure(0, weight=1)
        left_panel.columnconfigure(0, weight=1)

        nozzle_frame = ttk.LabelFrame(left_panel, text=" وضعیت نازل‌ها ", padding=5)
        nozzle_frame.grid(row=0, column=0, sticky='nsew')
        
        active_nozzles = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
        
        for i in range(4): 
            nozzle_frame.columnconfigure(i, weight=1)

        for col, header in enumerate(self.HEADERS):
            tk.Label(nozzle_frame, text=header, font=self.font_header, bg='#cfd8dc', 
                     borderwidth=1, relief="solid").grid(row=0, column=col, sticky='nsew', padx=1, pady=1)

        for row_idx, nozzle_num in enumerate(active_nozzles, start=1):
            nozzle_frame.rowconfigure(row_idx, weight=1)

            tk.Label(nozzle_frame, text=str(nozzle_num), font=self.font_bold, borderwidth=1, relief="solid",
                     bg='#eceff1').grid(row=row_idx, column=0, sticky='nsew', padx=1, pady=1)
            
            entry_row = {}
            for col_idx, key in enumerate(["پایان", "آغاز"], 1):
                ent = tk.Entry(nozzle_frame, justify='center', font=self.font_normal, borderwidth=1, relief="solid")
                ent.config(validate='key', validatecommand=(self.validate_cmd, '%P'))
                ent.grid(row=row_idx, column=col_idx, sticky='nsew', padx=1, pady=1)
                entry_row[key] = ent
                ent.bind("<Key>", lambda e, r=nozzle_num, k=key: self._on_arrow_key(e, r, k))

            mech_ent = tk.Entry(nozzle_frame, justify='center', font=self.font_normal, borderwidth=1, relief="solid", 
                                state='readonly', bg=self.bg_readonly, fg='#2e7d32')
            mech_ent.grid(row=row_idx, column=3, sticky='nsew', padx=1, pady=1)
            entry_row["کارکرد"] = mech_ent
            self.entries[nozzle_num] = entry_row

        nozzle_frame.rowconfigure(13, weight=1)
        tk.Label(nozzle_frame, text="جمع کل مکانیکی:", font=self.font_bold, bg='#b0bec5', borderwidth=1, relief="solid").grid(row=13, column=0, columnspan=3, sticky='nsew', padx=1, pady=1)
        self.total_mech_display = tk.Entry(nozzle_frame, justify='center', font=self.font_bold, state='readonly', bg='#fff9c4', borderwidth=1, relief="solid")
        self.total_mech_display.grid(row=13, column=3, sticky='nsew', padx=1, pady=1)

        # ===========================
        # RIGHT PANEL: Financials + Ops + Cards
        # ===========================
        right_panel = ttk.Frame(content_frame)
        right_panel.grid(row=0, column=1, sticky='nsew', padx=(5, 0))
        right_panel.columnconfigure(0, weight=1)
        
        right_panel.rowconfigure(0, weight=4)
        right_panel.rowconfigure(1, weight=1)
        right_panel.rowconfigure(2, weight=3)

        # --- 1. Financial Calculations ---
        calc_frame = ttk.LabelFrame(right_panel, text=" محاسبات سهمیه و فروش ", padding=5)
        calc_frame.grid(row=0, column=0, sticky='nsew', pady=(0, 5))
        for i in range(4): calc_frame.columnconfigure(i, weight=1)

        fin_headers = ["عنوان", "لیتر ورودی", "قیمت واحد", "مبلغ کل"]
        for i, h in enumerate(fin_headers):
            tk.Label(calc_frame, text=h, font=self.font_header, bg='#cfd8dc', borderwidth=1, relief="solid").grid(row=0, column=i, sticky='nsew', padx=1, pady=1)

        rows_cfg = [
            ("مجموع الکتریکی", "#fff3e0", "total_elec_entry", None, None),
            ("یارانه", "#e1f5fe", "total_subsidy_entry", f"{self.PRICE_SUBSIDY:,}", "price_subsidy_total"),
            ("نیمه یارانه", "#e1f5fe", "total_semi_entry", f"{self.PRICE_SEMI_SUBSIDY:,}", "price_semi_total"),
            ("آزاد (ویژه)", "#ffebee", "total_azad_entry_1", f"{self.PRICE_FREE:,}", "price_azad_total_1"),
            ("آزاد (جایگاه)", "#ffebee", "total_azad_entry_2", f"{self.PRICE_FREE:,}", "price_azad_total_2")
        ]
        
        calc_frame.rowconfigure(0, weight=1)
        for i, (lbl, clr, attr, prc, t_attr) in enumerate(rows_cfg, 1):
            calc_frame.rowconfigure(i, weight=1)
            tk.Label(calc_frame, text=lbl, font=self.font_normal, bg=clr, borderwidth=1, relief="solid").grid(row=i, column=0, sticky='nsew', padx=1, pady=1)
            ent = tk.Entry(calc_frame, justify='center', font=self.font_normal, bg=self.bg_editable, borderwidth=1, relief="solid")
            ent.bind('<FocusOut>', self._format_number)
            ent.grid(row=i, column=1, sticky='nsew', padx=1, pady=1)
            self.financial_entries.append(ent)
            ent.bind("<Key>", lambda e, idx=i-1: self._on_financial_arrow(e, idx))
            setattr(self, attr, ent)
            tk.Label(calc_frame, text=prc if prc else "-", bg=self.bg_readonly, borderwidth=1, relief="solid").grid(row=i, column=2, sticky='nsew', padx=1, pady=1)
            t_ent = tk.Entry(calc_frame, justify='center', font=self.font_normal, state='readonly', bg=self.bg_readonly, borderwidth=1, relief="solid")
            t_ent.grid(row=i, column=3, sticky='nsew', padx=1, pady=1)
            if t_attr: setattr(self, t_attr, t_ent)

        # Total Sales Row
        calc_frame.rowconfigure(6, weight=1)
        tk.Label(calc_frame, text="جمع کل مبلغ فروش", font=self.font_bold, bg='#c8e6c9', borderwidth=1, relief="solid").grid(row=6, column=0, columnspan=3, sticky='nsew', padx=1, pady=1)
        self.total_sales_entry = tk.Entry(calc_frame, justify='center', font=('Tahoma', 11, 'bold'), state='readonly', bg='#a5d6a7', fg='#1b5e20', borderwidth=1, relief="solid")
        self.total_sales_entry.grid(row=6, column=3, sticky='nsew', padx=1, pady=1)

        # --- 2. Operators ---
        op_frame = ttk.LabelFrame(right_panel, text=" اطلاعات متصدیان ", padding=5)
        op_frame.grid(row=1, column=0, sticky='nsew', pady=5)
        op_frame.rowconfigure(0, weight=1)
        for i in [1, 3]: op_frame.columnconfigure(i, weight=1)
        
        tk.Label(op_frame, text="متصدی ۱:").grid(row=0, column=0, padx=5, sticky='e')
        self.operator_entry_1 = tk.Entry(op_frame, font=self.font_normal, borderwidth=1, relief="solid")
        self.operator_entry_1.grid(row=0, column=1, sticky='ew', padx=5)
        tk.Label(op_frame, text="متصدی ۲:").grid(row=0, column=2, padx=5, sticky='e')
        self.operator_entry_2 = tk.Entry(op_frame, font=self.font_normal, borderwidth=1, relief="solid")
        self.operator_entry_2.grid(row=0, column=3, sticky='ew', padx=5)
        self.operator_entry_1.bind("<Key>", lambda e: self._on_arrow_key(e, "op_1", "name"))
        self.operator_entry_2.bind("<Key>", lambda e: self._on_arrow_key(e, "op_2", "name"))

        # --- 3. Card Readers ---
# --- 3. Card Readers (Updated for 8 card readers) ---
        pay_frame = ttk.LabelFrame(right_panel, text=" وضعیت دریافتی‌ها (کارت‌خوان) ", padding=5)
        pay_frame.grid(row=2, column=0, sticky='nsew', pady=(5, 0))
        for i in [1, 3]: pay_frame.columnconfigure(i, weight=1)

        self.card_reader_entries = []

        # Create 8 card readers (4 rows × 2 columns = 8)
        for i in range(8):  # Changed from 5 to 8
            row_num = i // 2  # Integer division to get row (0,1,2,3)
            col_num = (i % 2) * 2  # Column position (0 or 2)
            
            # Configure rows dynamically
            pay_frame.rowconfigure(row_num, weight=1)
            
            tk.Label(pay_frame, text=f"کارت‌خوان {i+1}:", font=self.font_normal).grid(
                row=row_num, column=col_num, sticky='e', padx=5
            )
            ent = tk.Entry(pay_frame, justify='center', font=self.font_normal, 
                        bg=self.bg_editable, borderwidth=1, relief="solid")
            ent.config(validate='key', validatecommand=(self.validate_cmd, '%P'))
            ent.bind("<Key>", lambda e, idx=i: self._on_arrow_key(e, f"card_{idx}", "value"))
            ent.grid(row=row_num, column=col_num + 1, sticky='ew', padx=5, pady=2)
            self.card_reader_entries.append(ent)

        # For rows without card readers, ensure they have weight
        for r in range(4):  # 4 rows total for 8 card readers
            pay_frame.rowconfigure(r, weight=1)

        # Row for summary (row 4)
        pay_frame.rowconfigure(4, weight=1)
        summary_f = ttk.Frame(pay_frame)
        summary_f.grid(row=4, column=0, columnspan=4, sticky='nsew', pady=(5, 0))
        summary_f.rowconfigure(0, weight=1)
        for i in [1, 3]: summary_f.columnconfigure(i, weight=1)

        tk.Label(summary_f, text="جمع کارت‌خوان:", font=self.font_bold).grid(
            row=0, column=0, padx=5, sticky='e'
        )
        self.card_reader_total_entry = tk.Entry(
            summary_f, state='readonly', font=self.font_bold, 
            bg='#eee', justify='center', borderwidth=1, relief="solid"
        )
        self.card_reader_total_entry.grid(row=0, column=1, sticky='ew', padx=5)

        tk.Label(summary_f, text="وجه نقد:", font=self.font_bold, fg='#d32f2f').grid(
            row=0, column=2, padx=5, sticky='e'
        )
        self.cash_entry = tk.Entry(
            summary_f, state='readonly', font=self.font_bold, 
            bg='#ffebee', fg='#c62828', justify='center', 
            borderwidth=1, relief="solid"
        )
        self.cash_entry.grid(row=0, column=3, sticky='ew', padx=5)

    def calculate(self):
        try:
            # 1. Nozzle calculations
            for nozzle_num, row in self.entries.items():
                end_val = self._convert_to_float(row["پایان"].get())
                start_val = self._convert_to_float(row["آغاز"].get())
                mech_val = max(0, end_val - start_val)
                
                formatted_mech = self._format_mech_value(mech_val)
                
                row["کارکرد"].config(state='normal')
                row["کارکرد"].delete(0, tk.END)
                row["کارکرد"].insert(0, formatted_mech)
                row["کارکرد"].config(state='readonly')
            
            t_mech = sum(self._convert_to_float(r["کارکرد"].get()) for r in self.entries.values())
            self._set_readonly_value_plain(self.total_mech_display, t_mech)

            # 2. Financial calculations
            t_sub = self._convert_to_float(self.total_subsidy_entry.get())
            t_semi = self._convert_to_float(self.total_semi_entry.get())
            t_azad_1 = self._convert_to_float(self.total_azad_entry_1.get())
            t_azad_2 = self._convert_to_float(self.total_azad_entry_2.get())
            
            # Total Electrical = Sum of all three liter inputs
            total_elec = t_sub + t_semi + t_azad_1 + t_azad_2
            
            self._set_readonly_value_plain(self.total_elec_entry, total_elec)
            
            # Calculate totals for each type
            p_sub = t_sub * self.PRICE_SUBSIDY
            p_semi = t_semi * self.PRICE_SEMI_SUBSIDY
            p_azad_1 = t_azad_1 * self.PRICE_FREE
            p_azad_2 = t_azad_2 * self.PRICE_FREE
            
            self._set_readonly_value(self.price_subsidy_total, p_sub)
            self._set_readonly_value(self.price_semi_total, p_semi)
            self._set_readonly_value(self.price_azad_total_1, p_azad_1)
            self._set_readonly_value(self.price_azad_total_2, p_azad_2)
            
            # Total Sales = Sum of all price totals
            total_s = p_sub + p_semi + p_azad_1 + p_azad_2
            self._set_readonly_value(self.total_sales_entry, total_s)

            # 3. Card reader calculations
            c_sum = 0
            for e in self.card_reader_entries:
                val = self._convert_to_float(e.get())
                c_sum += val
                self._format_card_entry(e)

            self._set_readonly_value(self.card_reader_total_entry, c_sum)

            if c_sum > total_s:
                # Only show warning if not already shown
                if not self.warning_shown:
                    messagebox.showwarning(
                        "اخطار: مبلغ دریافتی بیشتر از فروش",
                        "⚠️ جمع مبالغ کارت‌خوان بیشتر از جمع کل مبلغ فروش است.\n"
                        "وجه نقد به صورت منفی محاسبه خواهد شد."
                    )
                    self.warning_shown = True
            else:
                # Reset the flag when the issue is resolved
                self.warning_shown = False

            cash_val = total_s - c_sum
            self._set_readonly_value(self.cash_entry, cash_val)
            
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    def _setup_auto_calculate(self):
        self.total_subsidy_entry.bind('<FocusOut>', lambda e: self.calculate())
        self.total_semi_entry.bind('<FocusOut>', lambda e: self.calculate())
        self.total_azad_entry_1.bind('<FocusOut>', lambda e: self.calculate())
        self.total_azad_entry_2.bind('<FocusOut>', lambda e: self.calculate())
        
        for row in self.entries.values():
            row["پایان"].bind('<FocusOut>', lambda e: self.calculate())
            row["آغاز"].bind('<FocusOut>', lambda e: self.calculate())
        
        for entry in self.card_reader_entries:
            entry.bind('<FocusOut>', lambda e: self.calculate())
        
    def _convert_to_float(self, v):
        if not v: return 0.0
        return float(str(v).replace(',', ''))

    def _set_readonly_value(self, entry_widget, value):
        entry_widget.config(state='normal')
        entry_widget.delete(0, tk.END)
        
        try:
            float_val = float(value)
            if float_val.is_integer():
                formatted_value = f"{int(float_val):,}"
            else:
                formatted_value = f"{float_val:,.2f}"
        except (ValueError, TypeError):
            formatted_value = str(value)
        
        entry_widget.insert(0, formatted_value)
        entry_widget.config(state='readonly')

    def get_data(self):
        return {
            'shift_id': self.shift_id, 
            'operator1': self.operator_entry_1.get(), 
            'operator2': self.operator_entry_2.get(),
            'nozzles': {n: {'start': r['آغاز'].get(), 'end': r['پایان'].get(), 'mech': r['کارکرد'].get()} for n, r in self.entries.items()},
            'financial': {
                'total_elec': self.total_elec_entry.get(), 
                'total_subsidy': self.total_subsidy_entry.get(), 
                'total_semi': self.total_semi_entry.get(), 
                'total_azad_1': self.total_azad_entry_1.get(),
                'total_azad_2': self.total_azad_entry_2.get(), 
                'total_sales': self.total_sales_entry.get()
            },
            'card_readers': [e.get() for e in self.card_reader_entries], 
            'card_total': self.card_reader_total_entry.get(), 
            'cash': self.cash_entry.get()
        }

    def _on_arrow_key(self, event, row, col_name):
        if event.keysym not in ["Up", "Down", "Left", "Right"]:
            return

        if isinstance(row, int):
            active_nozzles = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
            
            try:
                current_index = active_nozzles.index(row)
                
                if event.keysym == "Up" and current_index > 0:
                    prev_nozzle = active_nozzles[current_index - 1]
                    self.entries[prev_nozzle][col_name].focus_set()
                elif event.keysym == "Down" and current_index < len(active_nozzles) - 1:
                    next_nozzle = active_nozzles[current_index + 1]
                    self.entries[next_nozzle][col_name].focus_set()
                elif event.keysym == "Left" and col_name == "آغاز":
                    self.entries[row]["پایان"].focus_set()
                elif event.keysym == "Right" and col_name == "پایان":
                    self.entries[row]["آغاز"].focus_set()
            except ValueError:
                pass

        elif str(row).startswith("card_"):
            idx = int(str(row).split("_")[1])
            if event.keysym == "Up" and idx > 0:
                self.card_reader_entries[idx-1].focus_set()
            elif event.keysym == "Down" and idx < 8:
                self.card_reader_entries[idx+1].focus_set()
                
        elif str(row).startswith("op_"):
            if event.keysym == "Right":
                self.operator_entry_2.focus_set()
            elif event.keysym == "Left":
                self.operator_entry_1.focus_set()

        return "break"
    
    def _on_financial_arrow(self, event, idx):
        if event.keysym == "Up" and idx > 0:
            self.financial_entries[idx - 1].focus_set()
        elif event.keysym == "Down" and idx < len(self.financial_entries) - 1:
            self.financial_entries[idx + 1].focus_set()
        else:
            return

        return "break"
    
    def _set_readonly_value_plain(self, entry_widget, value):
        entry_widget.config(state='normal')
        entry_widget.delete(0, tk.END)

        try:
            float_val = float(value)
            if float_val.is_integer():
                formatted_value = str(int(float_val))
            else:
                formatted_value = f"{float_val:.2f}"
        except (ValueError, TypeError):
            formatted_value = str(value)

        entry_widget.insert(0, formatted_value)
        entry_widget.config(state='readonly')