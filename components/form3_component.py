import tkinter as tk
from tkinter import ttk, messagebox

class Form3Component:
    def __init__(self, notebook, form1, form2, form2sh):
        self.frame = ttk.Frame(notebook)
        self.form1 = form1
        self.form2 = form2
        self.form2sh = form2sh
        
        # Get the active nozzles from form1
        self.active_nozzles = self.form1.entries.keys() if hasattr(self.form1, 'entries') else []
        # Sort the nozzles for display
        self.active_nozzles_sorted = sorted(list(self.active_nozzles))
        
        self.entries = {"آغاز": {}, "پایان": {}, "حاصل": {}}
        self.new_table_entries = {}
        
        # UI Styling Configuration
        self.header_bg = "#e3f2fd"
        self.row_header_bg = "#e8f5e9"
        self.font_header = ('Tahoma', 9, 'bold')
        self.font_cell = ('Tahoma', 9)

        self.create_widgets()

    def create_widgets(self):
        self.frame.pack(fill="both", expand=True)
        
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        main_frame.grid_rowconfigure(0, weight=2)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # ========== 1. COUNTERS TABLE ==========
        counters_frame = ttk.LabelFrame(
            main_frame, 
            text=f"شمارنده‌ها (نازل‌های فعال: {', '.join(map(str, self.active_nozzles_sorted))})", 
            padding=5
        )
        counters_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        headers = ["وضعیت"] + [str(i) for i in self.active_nozzles_sorted]

        for i in range(len(headers)):
            counters_frame.grid_columnconfigure(i, weight=1, uniform="counter_cols")

        for i in range(4):
            counters_frame.grid_rowconfigure(i, weight=1)

        # Headers
        for col, header_text in enumerate(headers):
            lbl = tk.Label(
                counters_frame, text=header_text, bg=self.header_bg, 
                font=self.font_header, relief="flat", bd=1
            )
            lbl.grid(row=0, column=col, sticky='nsew', padx=1, pady=1, ipady=5)

        # Data Rows
        row_labels = ["آغاز", "پایان", "حاصل"]
        for row_idx, row_label in enumerate(row_labels, start=1):
            lbl = tk.Label(
                counters_frame, text=row_label, bg=self.row_header_bg, 
                font=self.font_header, relief="flat", anchor='center'
            )
            lbl.grid(row=row_idx, column=0, sticky='nsew', padx=1, pady=1)
            
            for col_idx, pump_num in enumerate(self.active_nozzles_sorted, start=1):
                entry = tk.Entry(
                    counters_frame, justify='center', font=self.font_cell, 
                    state='readonly', bg='#ffffff', relief="flat",
                    highlightthickness=1, highlightbackground="#cccccc"
                )
                entry.grid(row=row_idx, column=col_idx, sticky='nsew', padx=2, pady=2)
                self.entries[row_label][pump_num] = entry

        # ========== 2. SUMMARY TABLE ==========
        new_table_frame = ttk.LabelFrame(main_frame, text="خلاصه عملکرد کل روز", padding=5)
        new_table_frame.grid(row=1, column=0, sticky="nsew")

        new_headers = ["شیفت ۱", "شیفت ۲", "روزانه", "مجموع الکتریکی", "یارانه کل", "نیمه یارانه کل", "آزاد کل", "مخزن کل"]
        
        for i in range(len(new_headers)):
            new_table_frame.grid_columnconfigure(i, weight=1, uniform="summary_cols")
        
        new_table_frame.grid_rowconfigure(0, weight=1)
        new_table_frame.grid_rowconfigure(1, weight=1)

        # Summary Headers
        for col, text in enumerate(new_headers):
            lbl = tk.Label(
                new_table_frame, text=text, bg=self.header_bg, 
                font=self.font_header, relief="flat"
            )
            lbl.grid(row=0, column=col, sticky='nsew', padx=1, pady=1)

        # Summary Entries
        for col, key in enumerate(new_headers):
            if key == "مخزن کل":
                entry = tk.Entry(
                    new_table_frame, justify='center', font=('Tahoma', 11, 'bold'),
                    state='normal', bg='#ffffcc', relief="solid",
                    highlightthickness=1, highlightbackground="#666666"
                )
                entry.insert(0, "0")
            else:
                entry = tk.Entry(
                    new_table_frame, justify='center', font=('Tahoma', 11, 'bold'),
                    state='readonly', bg='#f9f9f9', relief="flat",
                    highlightthickness=1, highlightbackground="#aaaaaa"
                )
            
            entry.grid(row=1, column=col, sticky='nsew', padx=5, pady=(5, 10))
            self.new_table_entries[key] = entry

    # ========== Helper Methods ==========
    def _get_value(self, widget):
        if widget and hasattr(widget, 'get'):
            val_str = widget.get().replace(",", "")
            try:
                return float(val_str) if val_str else 0.0
            except ValueError:
                return 0.0
        return 0.0

    def _get_azad_total(self, form):
        """دریافت مجموع لیترهای آزاد از فرم (هر دو نوع)"""
        total = 0.0
        
        # روش جدید: دو فیلد آزاد جداگانه
        if hasattr(form, 'total_azad_entry_1') and hasattr(form, 'total_azad_entry_2'):
            total += self._get_value(form.total_azad_entry_1)
            total += self._get_value(form.total_azad_entry_2)
        # روش قدیمی: یک فیلد آزاد
        elif hasattr(form, 'total_azad_entry'):
            total += self._get_value(form.total_azad_entry)
        
        return total

    def _update_entry(self, widget, value):
        if not widget:
            return
        
        # فقط برای "مخزن کل" state رو عوض نکن
        is_tank = (widget == self.new_table_entries.get("مخزن کل"))
        
        if not is_tank:
            widget.config(state='normal')
        
        widget.delete(0, tk.END)
        
        # قالب‌بندی عدد
        try:
            if isinstance(value, (int, float)):
                if value == int(value):
                    widget.insert(0, f"{int(value):,}")
                else:
                    widget.insert(0, f"{value:,.2f}")
            else:
                widget.insert(0, str(value))
        except:
            widget.insert(0, str(value))
        
        if not is_tank:
            widget.config(state='readonly')

    def calculate(self):
        """محاسبه اصلی فرم شمارنده‌ها"""
        try:
            # ===== 1. محاسبه شمارنده‌های نازل =====
            for pump_num in self.active_nozzles_sorted:
                # دریافت مقدار "آغاز" از شیفت اول
                if pump_num in self.form1.entries:
                    start_val = self._get_value(self.form1.entries[pump_num]["آغاز"])
                else:
                    start_val = 0

                # دریافت مقدار "پایان" از شیفت دوم
                if pump_num in self.form2sh.entries:
                    end_val = self._get_value(self.form2sh.entries[pump_num]["پایان"])
                else:
                    end_val = 0
                
                # محاسبه حاصل
                result = end_val - start_val if end_val >= start_val else 0

                # به‌روزرسانی جدول
                self._update_entry(self.entries["آغاز"][pump_num], start_val)
                self._update_entry(self.entries["پایان"][pump_num], end_val)
                self._update_entry(self.entries["حاصل"][pump_num], result)

            # ===== 2. محاسبه جمع مکانیکی شیفت‌ها =====
            mech1 = 0
            for n in self.form1.entries:
                mech1 += self._get_value(self.form1.entries[n]["کارکرد"])
            
            mech2 = 0
            for n in self.form2sh.entries:
                mech2 += self._get_value(self.form2sh.entries[n]["کارکرد"])
            
            daily_total = mech1 + mech2

            # ===== 3. محاسبه مقادیر سهمیه =====
            sub1 = self._get_value(self.form1.total_subsidy_entry)
            sub2 = self._get_value(self.form2sh.total_subsidy_entry)
            
            semi1 = self._get_value(self.form1.total_semi_entry)
            semi2 = self._get_value(self.form2sh.total_semi_entry)
            
            # دریافت مجموع آزاد (هر دو نوع) از هر فرم
            azad1 = self._get_azad_total(self.form1)
            azad2 = self._get_azad_total(self.form2sh)
            
            elec_total_1 = sub1 + semi1 + azad1  # مجموع الکتریکی شیفت اول
            elec_total_2 = sub2 + semi2 + azad2  # مجموع الکتریکی شیفت دوم
            elec_total_both = elec_total_1 + elec_total_2  # مجموع الکتریکی هر دو شیفت

            # ===== 4. به‌روزرسانی جدول خلاصه =====
            self._update_entry(self.new_table_entries["شیفت ۱"], mech1)
            self._update_entry(self.new_table_entries["شیفت ۲"], mech2)
            self._update_entry(self.new_table_entries["روزانه"], daily_total)
            self._update_entry(self.new_table_entries["مجموع الکتریکی"], elec_total_both) 
            self._update_entry(self.new_table_entries["یارانه کل"], sub1 + sub2)
            self._update_entry(self.new_table_entries["نیمه یارانه کل"], semi1 + semi2)
            self._update_entry(self.new_table_entries["آزاد کل"], azad1 + azad2)
            
            # ===== 5. انتقال موجودی پایانی به مخزن کل =====
            if hasattr(self, 'form2') and self.form2:
                # بررسی روش‌های مختلف دسترسی به end_inv
                end_inv_value = 0
                
                if 'end_inv' in self.form2.entries:
                    end_inv_value = self._get_value(self.form2.entries['end_inv'])
                elif hasattr(self.form2, 'entries') and self.form2.entries.get("end_inv"):
                    end_inv_value = self._get_value(self.form2.entries["end_inv"])
                
                tank_total_entry = self.new_table_entries.get("مخزن کل")
                if tank_total_entry:
                    tank_total_entry.config(state='normal')
                    tank_total_entry.delete(0, tk.END)
                    
                    # قالب‌بندی عدد
                    if end_inv_value == int(end_inv_value):
                        tank_total_entry.insert(0, f"{int(end_inv_value):,}")
                    else:
                        tank_total_entry.insert(0, f"{end_inv_value:,.2f}")
                    
                    # "مخزن کل" باید قابل ویرایش بماند (طبق درخواست)
                    # پس state رو به readonly تغییر نمی‌دهیم
                    
        except Exception as e:
            messagebox.showerror("خطا در فرم شمارنده‌ها", f"خطا در محاسبه:\n{str(e)}")

    def get_data(self):
        return {
            'counters': {
                'start': {p: self.entries['آغاز'][p].get() for p in self.active_nozzles_sorted},
                'end': {p: self.entries['پایان'][p].get() for p in self.active_nozzles_sorted},
            },
            'summary': {k: v.get() for k, v in self.new_table_entries.items()}
        }