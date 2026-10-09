# license_manager.py
import os
import json
import hashlib
import platform
import uuid
import sys
from datetime import datetime, timedelta
import sqlite3


class LicenseManager:
    """مدیریت لایسنس سخت‌افزاری"""
    
    def __init__(self, app_name="GasStation"):
        self.app_name = app_name
        self.license_file = f"{app_name}.license"
        self.key_file = f"{app_name}.key"
        self.db_file = "licenses_database.db"
        
        # تعیین مسیر بر اساس حالت اجرایی
        if getattr(sys, 'frozen', False):
            self.base_path = os.path.dirname(sys.executable)
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))
        
        self.license_path = os.path.join(self.base_path, self.license_file)
        self.db_path = os.path.join(self.base_path, self.db_file)
        
        # ایجاد دیتابیس
        self.init_database()
        
    def init_database(self):
        """ایجاد دیتابیس و جداول مورد نیاز"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # جدول مشتریان
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    company TEXT,
                    address TEXT,
                    registration_date TEXT,
                    notes TEXT
                )
            ''')
            
            # جدول لایسنس‌ها
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS licenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER,
                    hardware_id TEXT NOT NULL,
                    hardware_display_id TEXT,
                    activation_code TEXT UNIQUE,
                    issue_date TEXT NOT NULL,
                    expiry_date TEXT NOT NULL,
                    days_valid INTEGER,
                    license_type TEXT,
                    license_file TEXT,
                    status TEXT DEFAULT 'active',
                    last_check TEXT,
                    notes TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers (id)
                )
            ''')
            
            # جدول تاریخچه بررسی لایسنس
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS license_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_id INTEGER,
                    check_date TEXT,
                    check_result TEXT,
                    ip_address TEXT,
                    FOREIGN KEY (license_id) REFERENCES licenses (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✅ دیتابیس با موفقیت ایجاد شد")
        except Exception as e:
            print(f"❌ خطا در ایجاد دیتابیس: {e}")
    
    def get_hardware_id(self):
        try:
            identifiers = []
            # 1. نام کامپیوتر
            identifiers.append(platform.node() or "unknown")
            # 2. آدرس MAC (به صورت اعشاری)
            mac = str(uuid.getnode())
            identifiers.append(mac)
            # 3. پردازنده
            identifiers.append(platform.processor() or "unknown")
            # 4. معماری
            identifiers.append(platform.machine() or "unknown")
            # 5. تعداد هسته‌ها
            identifiers.append(str(os.cpu_count() or 1))
            # 6. سریال هارد دیسک (ویندوز)
            try:
                if platform.system() == 'Windows':
                    import subprocess
                    result = subprocess.run(
                        ['wmic', 'diskdrive', 'get', 'serialnumber'],
                        capture_output=True, text=True, timeout=3
                    )
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        identifiers.append(lines[1].strip())
            except:
                pass

            # فیلتر مقادیر خالی یا "unknown"
            filtered = [i for i in identifiers if i and i != "unknown"]
            if not filtered:
                filtered.append(str(datetime.now().timestamp()))

            # ایجاد هش نهایی
            combined = "|".join(filtered)
            full_hash = hashlib.sha512(combined.encode()).hexdigest().upper()

            # ایجاد شناسه قابل نمایش با خط تیره
            display_id = f"{full_hash[:16]}-{full_hash[16:32]}-{full_hash[32:48]}-{full_hash[48:64]}"

            return {
                'raw_hash': full_hash,          # 64 کاراکتر بدون خط تیره
                'display_id': display_id,       # همراه با خط تیره
                'short_id': full_hash[:16],
                'components': filtered
            }
        except Exception as e:
            fallback = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()
            return {
                'raw_hash': fallback,
                'display_id': f"{fallback[:16]}-{fallback[16:32]}",
                'short_id': fallback[:16]
            }
    
    def _get_disk_serial(self):
        """دریافت سریال هارد دیسک (مخصوص ویندوز)"""
        try:
            if platform.system() == 'Windows':
                import subprocess
                result = subprocess.run(
                    ['wmic', 'diskdrive', 'get', 'serialnumber'],
                    capture_output=True, text=True, timeout=5
                )
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    return lines[1].strip()
            return "unknown"
        except:
            return "unknown"
    
    def generate_license(self, hardware_id, days_valid=365, customer_info=None):
        """
        تولید لایسنس بر اساس شناسه سخت‌افزاری
        
        Args:
            hardware_id: شناسه سخت‌افزاری (raw_hash)
            days_valid: تعداد روزهای اعتبار
            customer_info: اطلاعات مشتری (اختیاری)
        
        Returns:
            dict: اطلاعات لایسنس
        """
        # تاریخ‌ها
        now = datetime.now()
        expiry = now + timedelta(days=days_valid)
        
        # ایجاد کد فعال‌سازی یکتا
        activation_data = f"{hardware_id}|{now.isoformat()}|{uuid.uuid4()}"
        activation_code = hashlib.sha256(activation_data.encode()).hexdigest()[:16]
        
        # اطلاعات لایسنس
        license_data = {
            'hardware_id': hardware_id,
            'activation_code': activation_code.upper(),
            'issue_date': now.isoformat(),
            'expiry_date': expiry.isoformat(),
            'days_valid': days_valid,
            'customer_info': customer_info or {},
            'version': '1.0',
            'app_name': self.app_name,
            'license_type': 'permanent' if days_valid > 3650 else 'temporary'
        }
        
        # امضای دیجیتال
        license_data['signature'] = self._create_signature(license_data)
        
        return license_data
    
    def _create_signature(self, data):
        """ایجاد امضای دیجیتال برای لایسنس"""
        # حذف signature از داده برای امضا
        data_copy = data.copy()
        data_copy.pop('signature', None)
        
        # تبدیل به JSON و ایجاد هش
        data_str = json.dumps(data_copy, sort_keys=True)
        return hashlib.sha512(data_str.encode()).hexdigest()
    
    def save_license(self, license_data, filepath=None):
        """ذخیره لایسنس در فایل"""
        if filepath is None:
            filepath = self.license_path
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(license_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"خطا در ذخیره لایسنس: {e}")
            return False
    
    def load_license(self, filepath=None):
        """بارگذاری لایسنس از فایل"""
        if filepath is None:
            filepath = self.license_path
        
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"خطا در بارگذاری لایسنس: {e}")
        return None
    
    def verify_license(self, license_data=None):
        """
        بررسی اعتبار لایسنس
        
        Returns:
            tuple: (is_valid, hardware_id, message)
        """
        # بارگذاری لایسنس اگر داده نشده
        if license_data is None:
            license_data = self.load_license()
        
        if not license_data:
            current_hw = self.get_hardware_id()
            return False, current_hw['display_id'], "فایل لایسنس یافت نشد"
        
        # بررسی وجود فیلدهای ضروری
        required_fields = ['hardware_id', 'activation_code', 'expiry_date', 'signature']
        for field in required_fields:
            if field not in license_data:
                current_hw = self.get_hardware_id()
                return False, current_hw['display_id'], f"لایسنس ناقص: {field}"
        
        # بررسی امضای دیجیتال
        if not self._verify_signature(license_data):
            current_hw = self.get_hardware_id()
            return False, current_hw['display_id'], "امضای لایسنس نامعتبر"
        
        # دریافت شناسه فعلی
        current_hw = self.get_hardware_id()
        current_raw = current_hw['raw_hash']
        stored_hw = license_data['hardware_id']
        
        # بررسی مطابقت سخت‌افزار
        if current_raw != stored_hw:
            return False, current_hw['display_id'], "این لایسنس برای سیستم دیگری است"
        
        # بررسی تاریخ انقضا
        try:
            expiry = datetime.fromisoformat(license_data['expiry_date'])
            if datetime.now() > expiry:
                return False, current_hw['display_id'], "لایسنس منقضی شده است"
        except:
            pass
        
        # همه چیز درست است
        return True, current_hw['display_id'], "لایسنس معتبر"
    
    def _verify_signature(self, license_data):
        """بررسی امضای دیجیتال"""
        stored_signature = license_data.get('signature')
        if not stored_signature:
            return False
        
        # محاسبه مجدد امضا
        data_copy = license_data.copy()
        data_copy.pop('signature', None)
        data_str = json.dumps(data_copy, sort_keys=True)
        calculated = hashlib.sha512(data_str.encode()).hexdigest()
        
        return calculated == stored_signature
    
    def add_customer(self, name, phone="", email="", company="", address="", notes=""):
        """اضافه کردن مشتری جدید به دیتابیس"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO customers (name, phone, email, company, address, registration_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, phone, email, company, address, datetime.now().isoformat(), notes))
            
            conn.commit()
            customer_id = cursor.lastrowid
            conn.close()
            return customer_id
        except Exception as e:
            print(f"خطا در افزودن مشتری: {e}")
            return None
    
    def save_license_to_db(self, customer_id, hardware_id, hardware_display_id, 
                          activation_code, issue_date, expiry_date, 
                          days_valid, license_type, license_file):
        """ذخیره اطلاعات لایسنس در دیتابیس"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO licenses 
                (customer_id, hardware_id, hardware_display_id, activation_code, 
                 issue_date, expiry_date, days_valid, license_type, license_file, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (customer_id, hardware_id, hardware_display_id, activation_code,
                  issue_date, expiry_date, days_valid, license_type, license_file, 'active'))
            
            conn.commit()
            license_id = cursor.lastrowid
            conn.close()
            return license_id
        except Exception as e:
            print(f"خطا در ذخیره لایسنس: {e}")
            return None
    
    def get_all_licenses(self):
        """دریافت تمام لایسنس‌ها به همراه اطلاعات مشتریان"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT l.*, c.name as customer_name, c.phone, c.email, c.company
                FROM licenses l
                LEFT JOIN customers c ON l.customer_id = c.id
                ORDER BY l.issue_date DESC
            ''')
            
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                item = dict(zip(columns, row))
                # محاسبه وضعیت
                try:
                    expiry = datetime.fromisoformat(item['expiry_date'])
                    now = datetime.now()
                    if now > expiry:
                        item['status_display'] = 'منقضی شده'
                        item['status_color'] = 'red'
                    else:
                        days_left = (expiry - now).days
                        item['days_left'] = days_left
                        if days_left < 7:
                            item['status_display'] = f'در شرف انقضا ({days_left} روز)'
                            item['status_color'] = 'orange'
                        else:
                            item['status_display'] = 'فعال'
                            item['status_color'] = 'green'
                except:
                    item['status_display'] = 'نامشخص'
                    item['status_color'] = 'gray'
                
                result.append(item)
            
            conn.close()
            return result
        except Exception as e:
            print(f"خطا در دریافت لیست لایسنس‌ها: {e}")
            return []
    
    def get_customers(self):
        """دریافت لیست مشتریان"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT c.*, COUNT(l.id) as license_count
                FROM customers c
                LEFT JOIN licenses l ON c.id = l.customer_id
                GROUP BY c.id
                ORDER BY c.registration_date DESC
            ''')
            
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                result.append(dict(zip(columns, row)))
            
            conn.close()
            return result
        except Exception as e:
            print(f"خطا در دریافت لیست مشتریان: {e}")
            return []
    
    def get_license_statistics(self):
        """گرفتن آمار لایسنس‌ها"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # تعداد کل
            cursor.execute("SELECT COUNT(*) FROM licenses")
            total = cursor.fetchone()[0]
            
            # فعال
            cursor.execute("SELECT COUNT(*) FROM licenses WHERE status='active'")
            active = cursor.fetchone()[0]
            
            # منقضی شده
            cursor.execute("SELECT COUNT(*) FROM licenses WHERE expiry_date < datetime('now')")
            expired = cursor.fetchone()[0]
            
            # در شرف انقضا (کمتر از 7 روز)
            cursor.execute('''
                SELECT COUNT(*) FROM licenses 
                WHERE expiry_date > datetime('now') 
                AND expiry_date < datetime('now', '+7 days')
            ''')
            expiring_soon = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total': total,
                'active': active,
                'expired': expired,
                'expiring_soon': expiring_soon
            }
        except Exception as e:
            print(f"خطا در دریافت آمار: {e}")
            return {'total': 0, 'active': 0, 'expired': 0, 'expiring_soon': 0}
    
    def create_license_file_for_customer(self, hardware_id, days=365, customer_name="", 
                                        customer_phone="", customer_email="", 
                                        customer_company="", customer_address=""):
        """
        ایجاد فایل لایسنس برای مشتری و ذخیره در دیتابیس
        """
        # پاکسازی شناسه
        hardware_id = hardware_id.replace('-', '').replace(' ', '').strip()
        
        # ایجاد شناسه نمایشی
        display_id = f"{hardware_id[:16]}-{hardware_id[16:32]}-{hardware_id[32:48]}-{hardware_id[48:64]}"
        
        # تولید لایسنس
        license_data = self.generate_license(
            hardware_id=hardware_id,
            days_valid=days,
            customer_info={
                'name': customer_name,
                'phone': customer_phone,
                'email': customer_email,
                'company': customer_company,
                'address': customer_address
            }
        )
        
        # اضافه کردن مشتری به دیتابیس
        customer_id = self.add_customer(
            name=customer_name or "مشتری",
            phone=customer_phone,
            email=customer_email,
            company=customer_company,
            address=customer_address
        )
        
        # ایجاد نام فایل
        safe_name = customer_name.replace(' ', '_') if customer_name else "Customer"
        filename = f"LICENSE_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.license"
        filepath = os.path.join(self.base_path, filename)
        
        # ذخیره فایل
        self.save_license(license_data, filepath)
        
        # ذخیره در دیتابیس
        if customer_id:
            license_id = self.save_license_to_db(
                customer_id=customer_id,
                hardware_id=hardware_id,
                hardware_display_id=display_id,
                activation_code=license_data['activation_code'],
                issue_date=license_data['issue_date'],
                expiry_date=license_data['expiry_date'],
                days_valid=days,
                license_type=license_data['license_type'],
                license_file=filename
            )
        
        return filename, license_data


class LicenseDialog:
    """دیالوگ فعال‌سازی لایسنس"""
    
    @staticmethod
    def show_activation_dialog(parent, hardware_info, callback=None):
        """نمایش دیالوگ فعال‌سازی"""
        import tkinter as tk
        from tkinter import ttk, messagebox
        
        dialog = tk.Toplevel(parent)
        dialog.title("فعال‌سازی نرم‌افزار")
        dialog.geometry("600x500")
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.grab_set()
        
        # مرکز کردن پنجره
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f'+{x}+{y}')
        
        # استایل
        style = ttk.Style()
        style.configure('Red.TLabel', foreground='red')
        style.configure('Green.TLabel', foreground='green')
        style.configure('Blue.TLabel', foreground='blue')
        
        # هدر
        header = tk.Label(dialog, text="🔒 فعال‌سازی نرم‌افزار", 
                          font=('Tahoma', 16, 'bold'), fg='#2196F3')
        header.pack(pady=20)
        
        # توضیحات
        info_text = """برای استفاده از این نرم‌افزار نیاز به فعال‌سازی دارید.
لطفاً مراحل زیر را دنبال کنید:"""
        
        tk.Label(dialog, text=info_text, font=('Tahoma', 11),
                justify='center', wraplength=500).pack(pady=10)
        
        # فریم شناسه سیستم
        id_frame = tk.LabelFrame(dialog, text="🔑 شناسه سیستم شما", 
                                 font=('Tahoma', 11, 'bold'),
                                 padx=10, pady=10)
        id_frame.pack(fill='x', padx=30, pady=10)
        
        # شناسه کامل
        hw_id = hardware_info['display_id']
        tk.Label(id_frame, text=hw_id, font=('Courier', 12, 'bold'),
                bg='#f0f0f0', relief='solid', padx=10, pady=5).pack(pady=5)
        
        # شناسه خام (برای کپی)
        raw_id = hardware_info['raw_hash']
        raw_frame = tk.Frame(id_frame)
        raw_frame.pack(fill='x', pady=5)
        
        tk.Label(raw_frame, text="شناسه خام:", font=('Tahoma', 9)).pack(side='left')
        
        raw_entry = tk.Entry(raw_frame, font=('Courier', 9), width=50)
        raw_entry.insert(0, raw_id)
        raw_entry.config(state='readonly')
        raw_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        # دکمه کپی
        def copy_raw():
            dialog.clipboard_clear()
            dialog.clipboard_append(raw_id)
            status_label.config(text="✅ شناسه کپی شد", fg='green')
        
        tk.Button(raw_frame, text="📋 کپی", command=copy_raw,
                 bg='#4CAF50', fg='white', font=('Tahoma', 9)).pack(side='left')
        
        # مراحل
        steps_frame = tk.LabelFrame(dialog, text="📋 مراحل فعال‌سازی",
                                    font=('Tahoma', 11, 'bold'),
                                    padx=10, pady=10)
        steps_frame.pack(fill='both', padx=30, pady=10, expand=True)
        
        steps_text = """
1️⃣  شناسه بالا را کپی کنید (با دکمه کپی)
2️⃣  برای پشتیبانی ارسال کنید
    📧 Email: your-email@example.com
    📱 Telegram: @yourusername
    📞 Phone: 0912XXXXXXX

3️⃣  پس از پرداخت، فایل لایسنس برای شما ارسال می‌شود
4️⃣  فایل دریافتی را در پوشه برنامه قرار دهید
5️⃣  برنامه را مجدداً اجرا کنید
        """
        
        tk.Label(steps_frame, text=steps_text, font=('Tahoma', 10),
                justify='left', wraplength=500).pack()
        
        # وضعیت
        status_label = tk.Label(dialog, text="", font=('Tahoma', 10))
        status_label.pack(pady=10)
        
        # دکمه‌ها
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        def check_license():
            """بررسی مجدد لایسنس"""
            if callback:
                result = callback()
                if result:
                    dialog.destroy()
                else:
                    status_label.config(text="❌ لایسنس هنوز معتبر نیست", fg='red')
        
        def exit_app():
            if messagebox.askyesno("خروج", "آیا می‌خواهید از برنامه خارج شوید؟"):
                dialog.destroy()
                parent.quit()
        
        tk.Button(btn_frame, text="🔄 بررسی مجدد", command=check_license,
                 bg='#2196F3', fg='white', font=('Tahoma', 11),
                 padx=20, pady=5).pack(side='left', padx=10)
        
        tk.Button(btn_frame, text="❌ خروج", command=exit_app,
                 bg='#f44336', fg='white', font=('Tahoma', 11),
                 padx=20, pady=5).pack(side='left', padx=10)
        
        dialog.protocol("WM_DELETE_WINDOW", exit_app)
        return dialog