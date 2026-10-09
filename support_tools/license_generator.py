# license_generator.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from license_manager import LicenseManager
from datetime import datetime, timedelta
import os

class LicenseGeneratorApp:
    """برنامه تولید لایسنس برای پشتیبانی"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("تولید کننده لایسنس - سیستم مدیریت پمپ بنزین")
        self.root.geometry("800x600")
        
        self.license_mgr = LicenseManager()
        self.setup_ui()
        self.load_statistics()
    
    def setup_ui(self):
        # عنوان
        title = tk.Label(self.root, text="🔐 تولید لایسنس مشتری", 
                        font=('Tahoma', 16, 'bold'), fg='#2196F3')
        title.pack(pady=10)
        
        # فریم آمار
        stats_frame = ttk.LabelFrame(self.root, text="آمار لایسنس‌ها", padding="10")
        stats_frame.pack(fill='x', padx=20, pady=5)
        
        self.stats_labels = {}
        stats = ["total", "active", "expired", "expiring_soon"]
        stats_fa = {"total": "تعداد کل", "active": "فعال", 
                   "expired": "منقضی شده", "expiring_soon": "در شرف انقضا"}
        
        for i, stat in enumerate(stats):
            tk.Label(stats_frame, text=f"{stats_fa[stat]}:").grid(row=0, column=i*2, padx=5)
            self.stats_labels[stat] = tk.Label(stats_frame, text="0", font=('Tahoma', 10, 'bold'))
            self.stats_labels[stat].grid(row=0, column=i*2+1, padx=5)
        
        # نوت‌بوک برای تب‌ها
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=10)
        
        # تب تولید لایسنس
        self.create_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.create_tab, text="➕ تولید لایسنس جدید")
        self.setup_create_tab()
        
        # تب لیست لایسنس‌ها
        self.list_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.list_tab, text="📋 لیست لایسنس‌ها")
        self.setup_list_tab()
        
        # تب مشتریان
        self.customers_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.customers_tab, text="👥 مشتریان")
        self.setup_customers_tab()
        
        # دکمه بروزرسانی آمار
        refresh_btn = ttk.Button(self.root, text="🔄 بروزرسانی آمار", 
                                command=self.load_statistics)
        refresh_btn.pack(pady=5)
    
    def setup_create_tab(self):
        """تنظیم تب تولید لایسنس"""
        main_frame = ttk.Frame(self.create_tab, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # شناسه سخت‌افزاری
        ttk.Label(main_frame, text="شناسه سخت‌افزاری مشتری:").grid(row=0, column=0, sticky='w', pady=5)
        self.hw_id_entry = ttk.Entry(main_frame, width=60, font=('Courier', 10))
        self.hw_id_entry.grid(row=0, column=1, columnspan=3, sticky='ew', pady=5, padx=5)
        
        # دکمه چسباندن
        ttk.Button(main_frame, text="📋 چسباندن", 
                  command=lambda: self.hw_id_entry.insert(0, self.root.clipboard_get())).grid(row=0, column=4, padx=5)
        
        # نام مشتری
        ttk.Label(main_frame, text="نام مشتری:").grid(row=1, column=0, sticky='w', pady=5)
        self.customer_entry = ttk.Entry(main_frame, width=40)
        self.customer_entry.grid(row=1, column=1, columnspan=3, sticky='ew', pady=5, padx=5)
        
        # اطلاعات تماس
        ttk.Label(main_frame, text="تلفن:").grid(row=2, column=0, sticky='w', pady=5)
        self.phone_entry = ttk.Entry(main_frame, width=20)
        self.phone_entry.grid(row=2, column=1, sticky='ew', pady=5, padx=5)
        
        ttk.Label(main_frame, text="ایمیل:").grid(row=2, column=2, sticky='w', pady=5)
        self.email_entry = ttk.Entry(main_frame, width=20)
        self.email_entry.grid(row=2, column=3, sticky='ew', pady=5, padx=5)
        
        ttk.Label(main_frame, text="شرکت:").grid(row=3, column=0, sticky='w', pady=5)
        self.company_entry = ttk.Entry(main_frame, width=40)
        self.company_entry.grid(row=3, column=1, columnspan=3, sticky='ew', pady=5, padx=5)
        
        # مدت اعتبار
        ttk.Label(main_frame, text="مدت اعتبار (روز):").grid(row=4, column=0, sticky='w', pady=5)
        self.days_var = tk.StringVar(value="365")
        days_spin = ttk.Spinbox(main_frame, from_=1, to=3650, textvariable=self.days_var, width=10)
        days_spin.grid(row=4, column=1, sticky='w', pady=5, padx=5)
        days_spin.bind('<KeyRelease>', lambda e: self.update_expiry())
        
        # نوع لایسنس
        ttk.Label(main_frame, text="نوع لایسنس:").grid(row=5, column=0, sticky='w', pady=5)
        self.license_type = ttk.Combobox(main_frame, 
            values=["آزمایشی (30 روز)", "نیمه‌سال (180 روز)", "سالیانه (365 روز)", "دائمی (3650 روز)"])
        self.license_type.set("سالیانه (365 روز)")
        self.license_type.grid(row=5, column=1, columnspan=3, sticky='w', pady=5, padx=5)
        self.license_type.bind('<<ComboboxSelected>>', self.on_license_type_change)
        
        # تاریخ‌ها
        ttk.Label(main_frame, text="تاریخ صدور:").grid(row=6, column=0, sticky='w', pady=5)
        self.issue_date = ttk.Label(main_frame, text=datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.issue_date.grid(row=6, column=1, sticky='w', pady=5, padx=5)
        
        ttk.Label(main_frame, text="تاریخ انقضا:").grid(row=7, column=0, sticky='w', pady=5)
        self.expiry_label = ttk.Label(main_frame, text="", font=('Tahoma', 10, 'bold'))
        self.expiry_label.grid(row=7, column=1, sticky='w', pady=5, padx=5)
        
        self.update_expiry()
        
        # دکمه‌ها
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=8, column=0, columnspan=4, pady=20)
        
        ttk.Button(btn_frame, text="✅ تولید و ذخیره لایسنس", 
                  command=self.generate_license).pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text="📂 بارگذاری شناسه از فایل", 
                  command=self.load_hw_from_file).pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text="🧹 پاک کردن فرم", 
                  command=self.clear_form).pack(side='left', padx=5)
        
        # تنظیم grid
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(3, weight=1)
    
    def setup_list_tab(self):
        """تنظیم تب لیست لایسنس‌ها"""
        # فریم برای Treeview و Scrollbar
        frame = ttk.Frame(self.list_tab)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Scrollbars
        vsb = ttk.Scrollbar(frame, orient="vertical")
        hsb = ttk.Scrollbar(frame, orient="horizontal")
        
        # Treeview
        columns = ('customer_name', 'hardware_display_id', 'issue_date', 
                  'expiry_date', 'days_left', 'status_display', 'license_type')
        
        self.licenses_tree = ttk.Treeview(frame, columns=columns, show='headings',
                                         yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.config(command=self.licenses_tree.yview)
        hsb.config(command=self.licenses_tree.xview)
        
        # تعریف ستون‌ها
        self.licenses_tree.heading('customer_name', text='نام مشتری')
        self.licenses_tree.heading('hardware_display_id', text='شناسه سخت‌افزار')
        self.licenses_tree.heading('issue_date', text='تاریخ صدور')
        self.licenses_tree.heading('expiry_date', text='تاریخ انقضا')
        self.licenses_tree.heading('days_left', text='روز باقی‌مانده')
        self.licenses_tree.heading('status_display', text='وضعیت')
        self.licenses_tree.heading('license_type', text='نوع')
        
        # تنظیم عرض ستون‌ها
        self.licenses_tree.column('customer_name', width=150)
        self.licenses_tree.column('hardware_display_id', width=250)
        self.licenses_tree.column('issue_date', width=150)
        self.licenses_tree.column('expiry_date', width=150)
        self.licenses_tree.column('days_left', width=100)
        self.licenses_tree.column('status_display', width=120)
        self.licenses_tree.column('license_type', width=100)
        
        # قرار دادن ویجت‌ها
        self.licenses_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # دکمه بروزرسانی
        action_frame = ttk.Frame(self.list_tab)
        action_frame.pack(fill='x', pady=5)
        
        ttk.Button(action_frame, text="🔄 بروزرسانی لیست", 
                command=self.load_licenses).pack(side='left', padx=5)
        
        ttk.Button(action_frame, text="❌ حذف لایسنس انتخاب شده", 
                command=self.delete_selected_license).pack(side='left', padx=5)
        
        # بارگذاری اولیه
        self.load_licenses()
    
    def setup_customers_tab(self):
        """تنظیم تب مشتریان"""
        frame = ttk.Frame(self.customers_tab)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Treeview برای مشتریان
        columns = ('name', 'phone', 'email', 'company', 'license_count', 'registration_date')
        
        self.customers_tree = ttk.Treeview(frame, columns=columns, show='headings')
        
        self.customers_tree.heading('name', text='نام مشتری')
        self.customers_tree.heading('phone', text='تلفن')
        self.customers_tree.heading('email', text='ایمیل')
        self.customers_tree.heading('company', text='شرکت')
        self.customers_tree.heading('license_count', text='تعداد لایسنس')
        self.customers_tree.heading('registration_date', text='تاریخ ثبت')
        
        self.customers_tree.column('name', width=150)
        self.customers_tree.column('phone', width=100)
        self.customers_tree.column('email', width=150)
        self.customers_tree.column('company', width=150)
        self.customers_tree.column('license_count', width=100)
        self.customers_tree.column('registration_date', width=150)
        
        self.customers_tree.pack(fill='both', expand=True)
        
        ttk.Button(self.customers_tab, text="🔄 بروزرسانی لیست مشتریان", 
                  command=self.load_customers).pack(pady=5)
        
        self.load_customers()
    
    def on_license_type_change(self, event=None):
        """بروزرسانی خودکار مدت اعتبار بر اساس نوع لایسنس"""
        type_map = {
            "آزمایشی (30 روز)": 30,
            "نیمه‌سال (180 روز)": 180,
            "سالیانه (365 روز)": 365,
            "دائمی (3650 روز)": 3650
        }
        selected = self.license_type.get()
        if selected in type_map:
            self.days_var.set(str(type_map[selected]))
            self.update_expiry()
            
    def delete_selected_license(self):
        selected = self.licenses_tree.selection()
        if not selected:
            messagebox.showwarning("هشدار", "لطفاً یک لایسنس را انتخاب کنید")
            return
        
        if messagebox.askyesno("تأیید", "آیا از حذف این لایسنس اطمینان دارید؟"):
            # اینجا باید متد حذف رو به LicenseManager اضافه کنید
            messagebox.showinfo("اطلاع", "این قابلیت به زودی اضافه می‌شود")        
    
    def update_expiry(self, event=None):
        """بروزرسانی تاریخ انقضا"""
        try:
            days = int(self.days_var.get())
            expiry = datetime.now() + timedelta(days=days)
            self.expiry_label.config(text=expiry.strftime("%Y-%m-%d %H:%M"))
        except:
            pass
    
    def generate_license(self):
        """تولید فایل لایسنس"""
        hw_id = self.hw_id_entry.get().strip()
        hw_id = hw_id.replace('-', '').replace(' ', '')
        customer = self.customer_entry.get().strip()
        phone = self.phone_entry.get().strip()
        email = self.email_entry.get().strip()
        company = self.company_entry.get().strip()
        
        if not hw_id:
            messagebox.showerror("خطا", "شناسه سخت‌افزاری را وارد کنید")
            return
        
        if len(hw_id) < 64:
            result = messagebox.askyesno("هشدار", 
                "طول شناسه وارد شده کوتاه است. آیا مطمئن هستید؟")
            if not result:
                return
        
        try:
            days = int(self.days_var.get())
        except:
            days = 365
        
        try:
            # تولید لایسنس و ذخیره در دیتابیس
            filename, license_data = self.license_mgr.create_license_file_for_customer(
                hardware_id=hw_id,
                days=days,
                customer_name=customer or "مشتری",
                customer_phone=phone,
                customer_email=email,
                customer_company=company
            )
            
            # نمایش خلاصه
            summary = f"""✅ لایسنس با موفقیت تولید و در دیتابیس ذخیره شد

📁 فایل: {filename}
👤 مشتری: {customer or 'مشتری'}
📞 تلفن: {phone or 'ندارد'}
📧 ایمیل: {email or 'ندارد'}
🏢 شرکت: {company or 'ندارد'}
📅 اعتبار: {days} روز
🔑 کد فعال‌سازی: {license_data['activation_code']}

فایل در پوشه جاری ذخیره شد.
"""
            messagebox.showinfo("نتیجه", summary)
            
            # بروزرسانی آمار و لیست‌ها
            self.load_statistics()
            self.load_licenses()
            self.load_customers()
            
            # باز کردن پوشه
            if os.name == 'nt':  # ویندوز
                os.startfile(os.path.dirname(os.path.abspath(filename)))
            
            # پاک کردن فرم
            self.clear_form()
            
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در تولید لایسنس: {e}")
    
    def load_statistics(self):
        """بارگذاری آمار"""
        stats = self.license_mgr.get_license_statistics()
        colors = {'total': 'black', 'active': 'green', 
                 'expired': 'red', 'expiring_soon': 'orange'}
        
        for key, value in stats.items():
            if key in self.stats_labels:
                self.stats_labels[key].config(text=str(value), fg=colors.get(key, 'black'))
    
    def load_licenses(self):
        """بارگذاری لیست لایسنس‌ها"""
        # پاک کردن موارد قبلی
        for item in self.licenses_tree.get_children():
            self.licenses_tree.delete(item)
        
        licenses = self.license_mgr.get_all_licenses()
        
        for lic in licenses:
            # محاسبه روزهای باقی‌مانده
            try:
                expiry = datetime.fromisoformat(lic['expiry_date'])
                now = datetime.now()
                if now > expiry:
                    days_left = "منقضی شده"
                else:
                    days_left = str((expiry - now).days)
            except:
                days_left = "نامشخص"
            
            self.licenses_tree.insert('', 'end', values=(
                lic.get('customer_name', ''),
                lic.get('hardware_display_id', '')[:30] + '...',
                lic.get('issue_date', '')[:10],
                lic.get('expiry_date', '')[:10],
                days_left,
                lic.get('status_display', ''),
                lic.get('license_type', '')
            ))
    
    def load_customers(self):
        """بارگذاری لیست مشتریان"""
        # پاک کردن موارد قبلی
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        
        customers = self.license_mgr.get_customers()
        
        for cust in customers:
            self.customers_tree.insert('', 'end', values=(
                cust.get('name', ''),
                cust.get('phone', ''),
                cust.get('email', ''),
                cust.get('company', ''),
                cust.get('license_count', 0),
                cust.get('registration_date', '')[:10]
            ))
    
    def load_hw_from_file(self):
        """بارگذاری شناسه از فایل متنی"""
        filename = filedialog.askopenfilename(
            title="انتخاب فایل شناسه",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    lines = content.split('\n')
                    for line in lines:
                        if len(line.strip()) > 50:
                            self.hw_id_entry.delete(0, tk.END)
                            self.hw_id_entry.insert(0, line.strip())
                            break
            except Exception as e:
                messagebox.showerror("خطا", f"خطا در خواندن فایل: {e}")
    
    def clear_form(self):
        """پاک کردن فرم"""
        self.hw_id_entry.delete(0, tk.END)
        self.customer_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)
        self.company_entry.delete(0, tk.END)
        self.days_var.set("365")
        self.license_type.set("سالیانه (365 روز)")
        self.update_expiry()

def main():
    root = tk.Tk()
    app = LicenseGeneratorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()