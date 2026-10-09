# license_management_system.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from license_manager import LicenseManager
from datetime import datetime, timedelta
import os
import webbrowser

class LicenseManagementSystem:
    """سیستم مدیریت کامل لایسنس‌های مشتریان"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🏢 سیستم مدیریت لایسنس - پمپ بنزین")
        self.root.geometry("1200x700")
        
        # مرکز کردن پنجره
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.root.winfo_screenheight() // 2) - (700 // 2)
        self.root.geometry(f'+{x}+{y}')
        
        self.license_mgr = LicenseManager()
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """ایجاد رابط کاربری"""
        
        # رنگ‌بندی
        self.colors = {
            'primary': '#1976D2',
            'success': '#388E3C',
            'warning': '#F57C00',
            'danger': '#D32F2F',
            'info': '#0288D1',
            'bg': '#F5F5F5',
            'card': '#FFFFFF'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # ========== منو ==========
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # منوی فایل
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="📁 فایل", menu=file_menu)
        file_menu.add_command(label="📂 پشتیبان‌گیری از دیتابیس", command=self.backup_database)
        file_menu.add_command(label="📥 بازیابی دیتابیس", command=self.restore_database)
        file_menu.add_separator()
        file_menu.add_command(label="🚪 خروج", command=self.root.quit)
        
        # منوی ابزارها
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="🔧 ابزارها", menu=tools_menu)
        tools_menu.add_command(label="🔍 جستجوی پیشرفته", command=self.show_search)
        tools_menu.add_command(label="📊 گزارش‌گیری", command=self.show_reports)
        tools_menu.add_command(label="📧 ارسال ایمیل یادآوری", command=self.send_reminders)
        
        # منوی راهنما
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="❓ راهنما", menu=help_menu)
        help_menu.add_command(label="📖 راهنما", command=self.show_help)
        help_menu.add_command(label="ℹ️ درباره", command=self.show_about)
        
        # ========== نوار ابزار ==========
        toolbar = tk.Frame(self.root, bg=self.colors['primary'], height=50)
        toolbar.pack(fill='x')
        toolbar.pack_propagate(False)
        
        # دکمه‌های نوار ابزار
        buttons = [
            ("➕ مشتری جدید", self.add_customer_dialog, self.colors['success']),
            ("🔑 لایسنس جدید", self.add_license_dialog, self.colors['info']),
            ("🔄 بروزرسانی", self.load_data, self.colors['warning']),
            ("📊 آمار", self.show_statistics, self.colors['primary']),
            ("📤 خروجی اکسل", self.export_to_excel, self.colors['primary']),
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(toolbar, text=text, command=command,
                          bg=color, fg='white', font=('Tahoma', 9, 'bold'),
                          relief='flat', padx=15, cursor='hand2')
            btn.pack(side='left', padx=5, pady=8)
        
        # ========== نوار جستجو ==========
        search_frame = tk.Frame(self.root, bg=self.colors['bg'], height=40)
        search_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(search_frame, text="🔍 جستجو:", bg=self.colors['bg'],
                font=('Tahoma', 9)).pack(side='left', padx=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_data())
        
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                               font=('Tahoma', 9), width=40,
                               relief='solid', bd=1)
        search_entry.pack(side='left', padx=5)
        search_entry.bind('<KeyRelease>', lambda e: self.filter_data())
        
        # فیلتر وضعیت
        tk.Label(search_frame, text="وضعیت:", bg=self.colors['bg'],
                font=('Tahoma', 9)).pack(side='left', padx=(20,5))
        
        self.status_filter = ttk.Combobox(search_frame, 
                                         values=["همه", "فعال", "منقضی شده", "در شرف انقضا"],
                                         state="readonly", width=15)
        self.status_filter.set("همه")
        self.status_filter.pack(side='left', padx=5)
        self.status_filter.bind('<<ComboboxSelected>>', lambda e: self.filter_data())
        
        # ========== تب‌ها ==========
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # تب لایسنس‌ها
        self.licenses_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.licenses_frame, text="📋 لیست لایسنس‌ها")
        self.setup_licenses_tab()
        
        # تب مشتریان
        self.customers_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.customers_frame, text="👥 لیست مشتریان")
        self.setup_customers_tab()
        
        # تب آمار
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="📊 آمار و نمودارها")
        self.setup_stats_tab()
        
        # ========== نوار وضعیت ==========
        self.status_bar = tk.Label(self.root, text="آماده", 
                                   bd=1, relief='sunken', anchor='w',
                                   bg=self.colors['bg'])
        self.status_bar.pack(side='bottom', fill='x')
    
    def setup_licenses_tab(self):
        """تنظیم تب لایسنس‌ها"""
        # فریم اصلی
        main_frame = ttk.Frame(self.licenses_frame)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Treeview برای نمایش لایسنس‌ها
        columns = ('id', 'customer', 'hardware_id', 'activation_code', 
                  'issue_date', 'expiry_date', 'days_left', 'status', 'actions')
        
        self.licenses_tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=20)
        
        # تعریف ستون‌ها
        self.licenses_tree.heading('id', text='ID')
        self.licenses_tree.heading('customer', text='مشتری')
        self.licenses_tree.heading('hardware_id', text='شناسه سخت‌افزار')
        self.licenses_tree.heading('activation_code', text='کد فعال‌سازی')
        self.licenses_tree.heading('issue_date', text='تاریخ صدور')
        self.licenses_tree.heading('expiry_date', text='تاریخ انقضا')
        self.licenses_tree.heading('days_left', text='روز باقیمانده')
        self.licenses_tree.heading('status', text='وضعیت')
        self.licenses_tree.heading('actions', text='عملیات')
        
        # تنظیم عرض ستون‌ها
        self.licenses_tree.column('id', width=50)
        self.licenses_tree.column('customer', width=120)
        self.licenses_tree.column('hardware_id', width=150)
        self.licenses_tree.column('activation_code', width=100)
        self.licenses_tree.column('issue_date', width=120)
        self.licenses_tree.column('expiry_date', width=120)
        self.licenses_tree.column('days_left', width=80)
        self.licenses_tree.column('status', width=100)
        self.licenses_tree.column('actions', width=100)
        
        # اسکرول بار
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=self.licenses_tree.yview)
        self.licenses_tree.configure(yscrollcommand=scrollbar.set)
        
        self.licenses_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # کلیک راست
        self.licenses_tree.bind('<Button-3>', self.show_license_popup)
        self.licenses_tree.bind('<Double-Button-1>', self.view_license_details)
    
    def setup_customers_tab(self):
        """تنظیم تب مشتریان"""
        main_frame = ttk.Frame(self.customers_frame)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        columns = ('id', 'name', 'phone', 'email', 'company', 
                  'license_count', 'registration_date', 'actions')
        
        self.customers_tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=20)
        
        self.customers_tree.heading('id', text='ID')
        self.customers_tree.heading('name', text='نام مشتری')
        self.customers_tree.heading('phone', text='تلفن')
        self.customers_tree.heading('email', text='ایمیل')
        self.customers_tree.heading('company', text='شرکت')
        self.customers_tree.heading('license_count', text='تعداد لایسنس')
        self.customers_tree.heading('registration_date', text='تاریخ ثبت')
        self.customers_tree.heading('actions', text='عملیات')
        
        self.customers_tree.column('id', width=50)
        self.customers_tree.column('name', width=150)
        self.customers_tree.column('phone', width=100)
        self.customers_tree.column('email', width=150)
        self.customers_tree.column('company', width=120)
        self.customers_tree.column('license_count', width=80)
        self.customers_tree.column('registration_date', width=120)
        self.customers_tree.column('actions', width=100)
        
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=self.customers_tree.yview)
        self.customers_tree.configure(yscrollcommand=scrollbar.set)
        
        self.customers_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.customers_tree.bind('<Button-3>', self.show_customer_popup)
        self.customers_tree.bind('<Double-Button-1>', self.view_customer_details)
    
    def setup_stats_tab(self):
        """تنظیم تب آمار"""
        # آمار کلی
        stats_frame = tk.Frame(self.stats_frame, bg=self.colors['card'], relief='solid', bd=1)
        stats_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(stats_frame, text="📊 آمار کلی", font=('Tahoma', 12, 'bold'),
                bg=self.colors['card']).pack(pady=10)
        
        # فریم کارت‌های آمار
        cards_frame = tk.Frame(stats_frame, bg=self.colors['card'])
        cards_frame.pack(pady=10)
        
        self.stats_labels = {}
        stats_items = [
            ('total', 'کل لایسنس‌ها', self.colors['primary']),
            ('active', 'فعال', self.colors['success']),
            ('expired', 'منقضی شده', self.colors['danger']),
            ('expiring_soon', 'در شرف انقضا', self.colors['warning']),
        ]
        
        for i, (key, title, color) in enumerate(stats_items):
            card = tk.Frame(cards_frame, bg=color, width=150, height=100)
            card.grid(row=0, column=i, padx=10)
            card.grid_propagate(False)
            
            tk.Label(card, text=title, font=('Tahoma', 10),
                    bg=color, fg='white').pack(pady=10)
            
            self.stats_labels[key] = tk.Label(card, text="0", font=('Tahoma', 18, 'bold'),
                                             bg=color, fg='white')
            self.stats_labels[key].pack()
        
        # نمودارها (placeholder)
        charts_frame = tk.Frame(self.stats_frame)
        charts_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # می‌توانید از matplotlib برای نمودارهای واقعی استفاده کنید
    
    def load_data(self):
        """بارگذاری اطلاعات از دیتابیس"""
        try:
            # پاک کردن داده‌های قبلی
            for item in self.licenses_tree.get_children():
                self.licenses_tree.delete(item)
            
            # دریافت لایسنس‌ها
            licenses = self.license_mgr.get_all_licenses()
            
            for lic in licenses:
                # تعیین رنگ وضعیت
                if lic['status_display'] == 'فعال':
                    tags = ('active',)
                elif 'انقضا' in lic['status_display']:
                    tags = ('expiring',)
                else:
                    tags = ('expired',)
                
                self.licenses_tree.insert('', 'end', values=(
                    lic['id'],
                    lic.get('customer_name', 'نامشخص'),
                    lic['hardware_id'][:20] + '...',
                    lic['activation_code'],
                    lic['issue_date'][:10],
                    lic['expiry_date'][:10],
                    lic.get('days_left', ''),
                    lic['status_display'],
                    '🔍 مشاهده'
                ), tags=tags)
            
            # تنظیم رنگ‌ها
            self.licenses_tree.tag_configure('active', background='#e8f5e8')
            self.licenses_tree.tag_configure('expiring', background='#fff3e0')
            self.licenses_tree.tag_configure('expired', background='#ffebee')
            
            # بارگذاری مشتریان
            for item in self.customers_tree.get_children():
                self.customers_tree.delete(item)
            
            customers = self.license_mgr.get_customers()
            for cust in customers:
                self.customers_tree.insert('', 'end', values=(
                    cust['id'],
                    cust['name'],
                    cust.get('phone', ''),
                    cust.get('email', ''),
                    cust.get('company', ''),
                    cust['license_count'],
                    cust['registration_date'][:10],
                    '🔍 مشاهده'
                ))
            
            # بروزرسانی آمار
            self.update_statistics()
            
            self.status_bar.config(text=f"✅ آخرین بروزرسانی: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در بارگذاری داده‌ها: {e}")
    
    def update_statistics(self):
        """بروزرسانی آمار"""
        stats = self.license_mgr.get_license_statistics()
        for key, label in self.stats_labels.items():
            label.config(text=str(stats.get(key, 0)))
    
    def filter_data(self):
        """فیلتر کردن داده‌ها بر اساس جستجو و وضعیت"""
        search_text = self.search_var.get().lower()
        status = self.status_filter.get()
        
        for item in self.licenses_tree.get_children():
            self.licenses_tree.delete(item)
        
        licenses = self.license_mgr.get_all_licenses()
        
        for lic in licenses:
            # فیلتر بر اساس وضعیت
            if status != "همه":
                if status == "فعال" and lic['status_display'] != "فعال":
                    continue
                elif status == "منقضی شده" and lic['status_display'] != "منقضی شده":
                    continue
                elif status == "در شرف انقضا" and "انقضا" not in lic['status_display']:
                    continue
            
            # فیلتر بر اساس جستجو
            if search_text:
                customer = lic.get('customer_name', '').lower()
                hw_id = lic['hardware_id'].lower()
                code = lic['activation_code'].lower()
                
                if not (search_text in customer or search_text in hw_id or search_text in code):
                    continue
            
            self.licenses_tree.insert('', 'end', values=(
                lic['id'],
                lic.get('customer_name', 'نامشخص'),
                lic['hardware_id'][:20] + '...',
                lic['activation_code'],
                lic['issue_date'][:10],
                lic['expiry_date'][:10],
                lic.get('days_left', ''),
                lic['status_display'],
                '🔍 مشاهده'
            ))
    
    def add_customer_dialog(self):
        """دیالوگ افزودن مشتری جدید"""
        dialog = tk.Toplevel(self.root)
        dialog.title("➕ مشتری جدید")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # مرکز کردن
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f'+{x}+{y}')
        
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # فیلدها
        fields = [
            ('نام مشتری*', 'entry'),
            ('تلفن', 'entry'),
            ('ایمیل', 'entry'),
            ('شرکت', 'entry'),
            ('آدرس', 'text'),
            ('توضیحات', 'text')
        ]
        
        entries = {}
        row = 0
        for label, field_type in fields:
            ttk.Label(main_frame, text=label).grid(row=row, column=0, sticky='w', pady=5)
            
            if field_type == 'entry':
                entry = ttk.Entry(main_frame, width=40)
                entry.grid(row=row, column=1, sticky='ew', pady=5, padx=5)
                entries[label] = entry
            else:
                text = tk.Text(main_frame, height=3, width=40)
                text.grid(row=row, column=1, sticky='ew', pady=5, padx=5)
                entries[label] = text
            
            row += 1
        
        main_frame.columnconfigure(1, weight=1)
        
        def save_customer():
            name = entries['نام مشتری*'].get().strip()
            if not name:
                messagebox.showerror("خطا", "نام مشتری الزامی است")
                return
            
            customer_id = self.license_mgr.add_customer(
                name=name,
                phone=entries['تلفن'].get().strip(),
                email=entries['ایمیل'].get().strip(),
                company=entries['شرکت'].get().strip(),
                address=entries['آدرس'].get('1.0', tk.END).strip(),
                notes=entries['توضیحات'].get('1.0', tk.END).strip()
            )
            
            if customer_id:
                messagebox.showinfo("موفق", "مشتری با موفقیت اضافه شد")
                dialog.destroy()
                self.load_data()
            else:
                messagebox.showerror("خطا", "خطا در ذخیره مشتری")
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="💾 ذخیره", command=save_customer).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="❌ انصراف", command=dialog.destroy).pack(side='left', padx=5)
    
    def add_license_dialog(self):
        """دیالوگ افزودن لایسنس جدید"""
        from license_generator import LicenseGeneratorApp
        
        # باز کردن پنجره تولید لایسنس
        generator_window = tk.Toplevel(self.root)
        app = LicenseGeneratorApp(generator_window)
        
        # بعد از بسته شدن، داده‌ها را بروزرسانی کن
        generator_window.wait_window()
        self.load_data()
    
    def show_license_popup(self, event):
        """منوی کلیک راست برای لایسنس"""
        item = self.licenses_tree.identify_row(event.y)
        if item:
            self.licenses_tree.selection_set(item)
            
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="🔍 مشاهده جزئیات", command=self.view_license_details)
            menu.add_command(label="📁 باز کردن فایل لایسنس", command=self.open_license_file)
            menu.add_command(label="✏️ ویرایش", command=self.edit_license)
            menu.add_command(label="🔄 تمدید", command=self.renew_license)
            menu.add_command(label="📧 ارسال ایمیل", command=self.email_license)
            menu.add_separator()
            menu.add_command(label="❌ غیرفعال کردن", command=self.deactivate_license)
            
            menu.post(event.x_root, event.y_root)
    
    def view_license_details(self, event=None):
        """نمایش جزئیات لایسنس"""
        selected = self.licenses_tree.selection()
        if not selected:
            return
        
        item = self.licenses_tree.item(selected[0])
        license_id = item['values'][0]
        
        # دریافت اطلاعات کامل از دیتابیس
        licenses = self.license_mgr.get_all_licenses()
        license_info = next((l for l in licenses if l['id'] == license_id), None)
        
        if not license_info:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"🔍 جزئیات لایسنس #{license_id}")
        dialog.geometry("600x500")
        
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # نمایش اطلاعات
        info_text = f"""
        📋 اطلاعات لایسنس
        ====================
        
        🆔 شناسه لایسنس: {license_info['id']}
        👤 مشتری: {license_info.get('customer_name', 'نامشخص')}
        📞 تلفن: {license_info.get('phone', '')}
        📧 ایمیل: {license_info.get('email', '')}
        🏢 شرکت: {license_info.get('company', '')}
        
        🔑 شناسه سخت‌افزار: 
        {license_info['hardware_id']}
        
        🔐 کد فعال‌سازی: {license_info['activation_code']}
        
        📅 تاریخ صدور: {license_info['issue_date']}
        📅 تاریخ انقضا: {license_info['expiry_date']}
        📊 وضعیت: {license_info['status_display']}
        
        📁 فایل لایسنس: {license_info.get('license_file', 'نامشخص')}
        """
        
        text_widget = tk.Text(main_frame, height=20, font=('Courier New', 10))
        text_widget.insert('1.0', info_text)
        text_widget.config(state='disabled')
        text_widget.pack(fill='both', expand=True)
        
        # دکمه‌ها
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="📁 باز کردن فایل", 
                  command=lambda: self.open_license_file(license_info)).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="📋 کپی شناسه", 
                  command=lambda: self.copy_to_clipboard(license_info['hardware_id'])).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="❌ بستن", command=dialog.destroy).pack(side='left', padx=5)
    
    def show_statistics(self):
        """نمایش آمار کامل"""
        stats = self.license_mgr.get_license_statistics()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("📊 آمار لایسنس‌ها")
        dialog.geometry("400x300")
        
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        stats_text = f"""
        📊 آمار کلی لایسنس‌ها
        ====================
        
        ✅ کل لایسنس‌ها: {stats['total']}
        
        🟢 فعال: {stats['active']}
        🟡 در شرف انقضا: {stats['expiring_soon']}
        🔴 منقضی شده: {stats['expired']}
        
        ====================
        
        💡 نکته: لایسنس‌های در شرف انقضا
        کمتر از 7 روز تا اتمام زمان دارند.
        """
        
        tk.Label(main_frame, text=stats_text, font=('Tahoma', 11),
                justify='left').pack()
        
        ttk.Button(main_frame, text="بستن", command=dialog.destroy).pack(pady=20)
    
    def export_to_excel(self):
        """خروجی اکسل"""
        try:
            import csv
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename:
                licenses = self.license_mgr.get_all_licenses()
                
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(['ID', 'مشتری', 'شناسه سخت‌افزار', 'کد فعال‌سازی',
                                   'تاریخ صدور', 'تاریخ انقضا', 'وضعیت'])
                    
                    for lic in licenses:
                        writer.writerow([
                            lic['id'],
                            lic.get('customer_name', ''),
                            lic['hardware_id'],
                            lic['activation_code'],
                            lic['issue_date'][:10],
                            lic['expiry_date'][:10],
                            lic['status_display']
                        ])
                
                messagebox.showinfo("موفق", f"خروجی با موفقیت ذخیره شد: {filename}")
                os.startfile(os.path.dirname(filename))
                
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در خروجی گرفتن: {e}")
    
    def backup_database(self):
        """پشتیبان‌گیری از دیتابیس"""
        try:
            backup_dir = os.path.join(self.license_mgr.base_path, "backups")
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            backup_path = os.path.join(backup_dir, backup_name)
            
            import shutil
            shutil.copy2(self.license_mgr.db_path, backup_path)
            
            messagebox.showinfo("موفق", f"پشتیبان با موفقیت ایجاد شد:\n{backup_path}")
            
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در پشتیبان‌گیری: {e}")
    
    def send_reminders(self):
        """ارسال یادآوری به مشتریان"""
        # اینجا می‌توانید از کتابخانه smtplib برای ارسال ایمیل استفاده کنید
        messagebox.showinfo("یادآوری", "این قابلیت به زودی اضافه می‌شود")
    
    def show_help(self):
        """نمایش راهنما"""
        help_text = """
        📖 راهنمای استفاده از سیستم مدیریت لایسنس
        
        1️⃣ مشتریان:
        - برای افزودن مشتری جدید از دکمه "مشتری جدید" استفاده کنید
        - با دوبار کلیک روی هر مشتری می‌توانید جزئیات را مشاهده کنید
        
        2️⃣ لایسنس‌ها:
        - با دکمه "لایسنس جدید" می‌توانید لایسنس جدید تولید کنید
        - وضعیت لایسنس‌ها با رنگ‌های مختلف نمایش داده می‌شود:
          * سبز: فعال
          * نارنجی: در شرف انقضا
          * قرمز: منقضی شده
        
        3️⃣ جستجو:
        - در کادر جستجو می‌توانید بر اساس نام مشتری یا شناسه جستجو کنید
        - با فیلتر وضعیت می‌توانید لایسنس‌ها را بر اساس وضعیت فیلتر کنید
        
        4️⃣ گزارش‌گیری:
        - از دکمه "خروجی اکسل" برای دریافت گزارش استفاده کنید
        """
        
        messagebox.showinfo("📖 راهنما", help_text)
    
    def show_about(self):
        """نمایش درباره"""
        about_text = """
        🏢 سیستم مدیریت لایسنس
        📌 نسخه: 2.0
        📅 تاریخ: 2024
        
        این نرم‌افزار برای مدیریت لایسنس‌های مشتریان
        سیستم مدیریت پمپ بنزین طراحی شده است.
        
        امکانات:
        ✓ مدیریت مشتریان
        ✓ تولید لایسنس
        ✓ پیگیری وضعیت لایسنس‌ها
        ✓ گزارش‌گیری
        ✓ یادآوری انقضا
        """
        
        messagebox.showinfo("ℹ️ درباره", about_text)
    
    # متدهای کمکی
    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_bar.config(text="✅ کپی شد")
    
    def show_customer_popup(self, event):
        pass
    
    def view_customer_details(self, event):
        pass
    
    def open_license_file(self, license_info=None):
        pass
    
    def edit_license(self):
        pass
    
    def renew_license(self):
        pass
    
    def email_license(self):
        pass
    
    def deactivate_license(self):
        pass
    
    def show_search(self):
        pass
    
    def show_reports(self):
        pass
    
    def restore_database(self):
        pass

def main():
    root = tk.Tk()
    app = LicenseManagementSystem(root)
    root.mainloop()

if __name__ == "__main__":
    main()