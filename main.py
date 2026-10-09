# main.py - سیستم مدیریت پمپ بنزین با قفل سخت‌افزاری کامل
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from PIL import Image, ImageTk
import time
import json
import os
import hashlib
import sys
import platform
import uuid
import base64
import jdatetime  # اضافه شده از فایل قدیمی

# ==================== DEBUG ====================
DEBUG = True

def debug_print(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")

debug_print("شروع برنامه...")

# ==================== تنظیمات مسیر برای PyInstaller ====================
def get_resource_path(relative_path):
    """مسیر منابع را در حالت exe و اسکریپت برمی‌گرداند"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


# تنظیم مسیر کاری
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    os.chdir(application_path)
    debug_print(f"حالت اجرایی - مسیر: {application_path}")
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
    debug_print(f"حالت اسکریپت - مسیر: {application_path}")

# ==================== سیستم قفل سخت‌افزاری ====================
class HardwareLock:
    """قفل سخت‌افزاری ساده و مؤثر"""
    
    def __init__(self, license_file="gas_station.license"):
        self.license_file = os.path.join(application_path, license_file)
        debug_print(f"مسیر فایل لایسنس: {self.license_file}")
        self.license_info = {}
        
    def get_hardware_id(self):
        """دریافت شناسه سخت‌افزاری منحصربفرد"""
        try:
            identifiers = []
            
            # 1. نام کامپیوتر
            identifiers.append(platform.node() or "unknown")
            
            # 2. آدرس MAC
            mac = str(uuid.getnode())
            identifiers.append(mac)
            
            # 3. پردازنده
            identifiers.append(platform.processor() or "unknown")
            
            # 4. معماری سیستم
            identifiers.append(platform.machine() or "unknown")
            
            # 5. تعداد هسته‌های CPU
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
            
            # فیلتر کردن مقادیر خالی
            filtered = [i for i in identifiers if i and i != "unknown"]
            
            if not filtered:
                filtered.append(str(datetime.now().timestamp()))
            
            # ایجاد هش نهایی
            combined = "|".join(filtered)
            full_hash = hashlib.sha512(combined.encode()).hexdigest().upper()
            
            # ایجاد شناسه قابل نمایش با خط تیره
            display_id = f"{full_hash[:16]}-{full_hash[16:32]}-{full_hash[32:48]}-{full_hash[48:64]}"
            
            return {
                'raw_hash': full_hash,
                'display_id': display_id,
                'short_id': full_hash[:16],
                'components': filtered
            }
                
        except Exception as e:
            debug_print(f"خطا در دریافت شناسه سخت‌افزاری: {e}")
            fallback = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()
            return {
                'raw_hash': fallback,
                'display_id': f"{fallback[:16]}-{fallback[16:32]}",
                'short_id': fallback[:16]
            }
    
    def check_license(self):
        """بررسی لایسنس"""
        debug_print("بررسی لایسنس...")
        
        current_hw = self.get_hardware_id()
        current_id = current_hw['raw_hash']
        
        if not os.path.exists(self.license_file):
            debug_print(f"فایل لایسنس یافت نشد")
            return current_hw, False, "فایل لایسنس یافت نشد"
        
        try:
            with open(self.license_file, 'r', encoding='utf-8') as f:
                license_data = json.load(f)
            debug_print("فایل لایسنس با موفقیت خوانده شد")
        except Exception as e:
            debug_print(f"خطا در خواندن لایسنس: {e}")
            return current_hw, False, "خطا در خواندن لایسنس"
        
        # بررسی فیلدهای ضروری
        required_fields = ['hardware_id', 'activation_code', 'expiry_date']
        for field in required_fields:
            if field not in license_data:
                debug_print(f"فیلد {field} در لایسنس وجود ندارد")
                return current_hw, False, f"لایسنس ناقص: {field}"
        
        stored_id = license_data.get('hardware_id')
        if stored_id != current_id:
            debug_print("شناسه سخت‌افزاری مطابقت ندارد!")
            return current_hw, False, "این لایسنس برای سیستم دیگری است"
        
        try:
            expiry_str = license_data.get('expiry_date')
            if expiry_str:
                expiry = datetime.fromisoformat(expiry_str)
                now = datetime.now()
                if now > expiry:
                    return current_hw, False, f"لایسنس منقضی شده است"
        except Exception as e:
            debug_print(f"خطا در بررسی تاریخ انقضا: {e}")
        
        debug_print("✅ لایسنس معتبر است")
        self.license_info = license_data
        return current_hw, True, "لایسنس معتبر"
    
    def get_license_info(self):
        return self.license_info

# ==================== بارگذاری شرطی ماژول‌ها ====================
try:
    import jdatetime
    JDATETIME_AVAILABLE = True
    debug_print("jdatetime موجود است")
except ImportError:
    JDATETIME_AVAILABLE = False
    debug_print("jdatetime در دسترس نیست")

try:
    from components.form1_component import Form1Component
    from components.form2SH_component import Form2SHComponent
    from components.form2_component import Form2Component
    from components.form3_component import Form3Component
    COMPONENTS_AVAILABLE = True
    debug_print("کامپوننت‌ها موجود هستند")
except ImportError as e:
    COMPONENTS_AVAILABLE = False
    debug_print(f"خطا در بارگذاری کامپوننت‌ها: {e}")

try:
    from components.pdf_exporter import PDFExporter
    PDF_AVAILABLE = True
    debug_print("PDF Exporter موجود است")
except ImportError:
    PDF_AVAILABLE = False
    debug_print("PDF Exporter در دسترس نیست")

# ==================== مدیریت ذخیره‌سازی موقت ====================
class TemporaryStorage:
    def __init__(self):
        self.storage_file = "temporary_data.json"
        self.data_dir = "data"
        
        data_path = os.path.join(application_path, self.data_dir)
        if not os.path.exists(data_path):
            try:
                os.makedirs(data_path)
            except:
                pass
    
    def get_storage_path(self):
        return os.path.join(application_path, self.data_dir, self.storage_file)
    
    def save_data(self, shift1_data, shift2_data=None, form2_data=None, current_date=None):
        try:
            data = {
                "current_date": current_date,
                "shift1_data": shift1_data,
                "shift2_data": shift2_data,
                "form2_data" : form2_data,
                "last_saved": datetime.now().isoformat()
            }
            
            with open(self.get_storage_path(), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    def load_data(self):
        try:
            path = self.get_storage_path()
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except:
            return None
    
    def clear_data(self):
        try:
            path = self.get_storage_path()
            if os.path.exists(path):
                os.remove(path)
        except:
            pass

# ==================== تابع اصلی با ====================

import tkinter.font as tkfont

def load_persian_font(root, font_name="Vazir", size=11):
    """بارگذاری فونت فارسی از پوشه fonts"""
    try:
        # مسیر پوشه fonts در کنار برنامه
        fonts_dir = get_resource_path("fonts")
        font_path = os.path.join(fonts_dir, f"{font_name}.ttf") 
        
        if os.path.exists(font_path):
            # ثبت فونت در tkinter
            tkfont.Font(family=font_name, size=size)
            debug_print(f"فونت {font_name} با موفقیت بارگذاری شد")
            return font_name
        else:
            debug_print(f"فایل فونت یافت نشد: {font_path}")
            return "Tahoma"
    except Exception as e:
        debug_print(f"خطا در بارگذاری فونت: {e}")
        return "Tahoma"
    
def show_splash(on_finish):
    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.configure(bg="#f9f9f9")

    w, h = 460, 360 
    x = (splash.winfo_screenwidth() // 2) - (w // 2)
    y = (splash.winfo_screenheight() // 2) - (h // 2)
    splash.geometry(f"{w}x{h}+{x}+{y}")
    
    # --- 1. بارگذاری و نمایش لوگو ---
    
    LOGO_PATH = get_resource_path("asset/logo.png") 
    
    try:
        # باز کردن تصویر با PIL
        img = Image.open(LOGO_PATH)
        # تغییر اندازه (برای اطمینان از مناسب بودن اندازه در اسپلش)
        img = img.resize((200, 200), Image.Resampling.LANCZOS) 
        # تبدیل به فرمت Tkinter
        logo_tk = ImageTk.PhotoImage(img)
        
        # ایجاد Label برای نمایش لوگو
        logo_label = tk.Label(splash, image=logo_tk)
        logo_label.image = logo_tk # نگه‌داشتن رفرنس برای جلوگیری از حذف توسط garbage collector
        logo_label.pack(pady=(30, 15))
        
    except FileNotFoundError:
        # اگر فایل لوگو پیدا نشد، متن قدیمی را نمایش می‌دهیم
        print(f"Error: Logo file not found at {LOGO_PATH}. Displaying text only.")
        try:
            title_font = ("Vazir", 20, "bold") 
        except tk.TclError:
            title_font = ("Arial", 20, "bold")
            
        title = tk.Label(
            splash,
            text="سیستم مدیریت پمپ بنزین",
            font=title_font,
            bg="#f5f7fa",
            fg="#1f3a5f",
        )
        title.pack(pady=30)

    # --- 2. نوار پیشرفت (بدون تغییر نسبت به قبل) ---
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "blue.Horizontal.TProgressbar",
        foreground="#3498db",
        background="#3498db",
        troughcolor="#e0e0e0",
        thickness=10,
    )
    progress = ttk.Progressbar(
        splash,
        orient="horizontal",
        length=350,
        mode="determinate",
        style="blue.Horizontal.TProgressbar",
    )
    progress.pack(pady=25)

    status = tk.Label(splash, text="در حال راه‌اندازی سرویس‌ها...", bg="#f5f7fa", fg="#95a5a6", font=("Tahoma", 10))
    status.pack(pady=(0, 20))

    # --- تابع به‌روزرسانی ---
    max_value = 100
    step = 2
    delay = 30

    def update_progress():
        current_value = progress['value']
        
        if current_value < max_value:
            new_value = min(current_value + step, max_value)
            progress['value'] = new_value
            
            if new_value < 30:
                status.config(text="در حال بارگذاری منابع اولیه...")
            elif new_value < 70:
                status.config(text="اتصال به پایگاه داده...")
            else:
                status.config(text="تکمیل راه‌اندازی...")

            splash.after(delay, update_progress)
        else:
            splash.destroy()
            on_finish()

    splash.after(100, update_progress)
    splash.mainloop()

    def update():
        cur = progress["value"]
        if cur < max_value:
            progress["value"] = cur + step
            splash.after(delay, update)
        else:
            # پایان → بستن splash و فراخوانی تابع اصلی
            splash.destroy()
            on_finish()

    # شروع به‌روزرسانی
    splash.after(500, update)   # کمی تاخیر برای نمایش اولیه
    splash.mainloop()    

def main():
    try:
        # ابتدا لایسنس را بررسی می‌کنیم
        lock = HardwareLock()
        hw_info, is_valid, message = lock.check_license()
        
        if is_valid:
            debug_print(f"✅ {message}")
            root = tk.Tk()
            if getattr(sys, 'frozen', False):  # وقتی به صورت exe اجرا می‌شود
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(__file__)
            icon_path = os.path.join(base_path, "gas_station.ico")
            root.iconbitmap(icon_path) 
            persian_font = load_persian_font(root, "Vazir")
            app = GasStationManagementSystem(root, skip_license_check=True)
            root.mainloop()
        else:
            debug_print(f"❌ {message}")
            debug_print(f"شناسه سیستم: {hw_info['display_id']}")
            
            # ایجاد پنجره فعال‌سازی با ابعاد مناسب
            root = tk.Tk()
            if getattr(sys, 'frozen', False):  # وقتی به صورت exe اجرا می‌شود
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(__file__)
            icon_path = get_resource_path("gas_station.ico")
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path) 
            root.title("فعال‌سازی نرم‌افزار")
            root.geometry("500x600")  # ابعاد جمع و جورتر
            root.resizable(False, False)
            
            # بارگذاری فونت Vazir
            persian_font = load_persian_font(root, "Vazir")
            
            # مرکز کردن پنجره
            root.update_idletasks()
            x = (root.winfo_screenwidth() // 2) - (500 // 2)
            y = (root.winfo_screenheight() // 2) - (550 // 2)
            root.geometry(f'+{x}+{y}')
            
            # پالت رنگی مینیمال
            colors = {
                'primary': '#2980b9',      # آبی
                'primary_dark': '#1f618d',
                'accent': '#f39c12',        # نارنجی
                'success': '#27ae60',        # سبز
                'danger': '#c0392b',          # قرمز
                'background': '#f5f5f5',      # خاکستری روشن
                'card': '#ffffff',             # سفید
                'border': '#d5d8dc',           # حاشیه
                'text': '#2c3e50',              # متن
            }
            
            root.configure(bg=colors['background'])
            
            # ========== هدر ==========
            header = tk.Frame(root, bg=colors['primary'], height=60)
            header.pack(fill='x')
            header.pack_propagate(False)
            
            # خط آکسان
            tk.Frame(header, bg=colors['accent'], height=2).pack(fill='x', side='bottom')
            
            # عنوان هدر
            header_content = tk.Frame(header, bg=colors['primary'])
            header_content.pack(expand=True, fill='both', padx=15)
            
            tk.Label(header_content, text="🔒", font=('Segoe UI', 20),
                    bg=colors['primary'], fg='white').pack(side='right')
            
            tk.Label(header_content, text="فعال‌سازی نرم‌افزار", 
                    font=(persian_font, 14, 'bold'), bg=colors['primary'], 
                    fg='white').pack(side='right', padx=(10, 0))
            
            # ========== محتوای اصلی ==========
            main = tk.Frame(root, bg=colors['background'])
            main.pack(fill='both', expand=True, padx=15, pady=15)
            
            # ========== کارت شناسه ==========
            id_card = tk.Frame(main, bg=colors['card'], relief='flat', bd=1,
                              highlightbackground=colors['border'], highlightthickness=1)
            id_card.pack(fill='x', pady=(0, 10))
            
            # عنوان کارت
            tk.Label(id_card, text="🆔 شناسه سیستم", font=('Vazir', 10, 'bold'),
                    bg=colors['primary'], fg='white', padx=10, pady=4).pack(fill='x')
            
            # محتوای کارت
            id_body = tk.Frame(id_card, bg=colors['card'], padx=12, pady=12)
            id_body.pack(fill='x')
            
            # شناسه نمایشی در یک خط
            display_id = hw_info['display_id']
            
            # نمایش شناسه در یک خط با فونت Courier
            id_display = tk.Frame(id_body, bg='#f8f9fa', relief='solid', bd=1,
                                 highlightbackground=colors['border'])
            id_display.pack(fill='x', pady=(0, 8))
        
            tk.Label(id_display, text=display_id, font=('Arail',8),
                        bg='#f8f9fa', fg=colors['primary'], pady=6).pack()
            
            # فریم کپی
            copy_frame = tk.Frame(id_body, bg=colors['card'])
            copy_frame.pack(fill='x')
            
            raw_id = hw_info['raw_hash']
            
            # فیلد خلاصه شناسه
            summary_entry = tk.Entry(copy_frame, font=('Courier New', 8), 
                                    bg='#f8f9fa', fg=colors['text'],
                                    relief='solid', bd=1, highlightbackground=colors['border'],
                                    width=40)
            summary_entry.insert(0, raw_id[:25] + "..." + raw_id[-10:])
            summary_entry.config(state='readonly')
            summary_entry.pack(side='right', padx=(0, 8), ipady=3)
            
            def copy_full_id():
                root.clipboard_clear()
                root.clipboard_append(raw_id)
                status_label.config(text="✅ شناسه کپی شد")
                copy_btn.config(bg=colors['success'], text="✓ کپی شد")
                root.after(1000, lambda: copy_btn.config(bg=colors['accent'], text="📋 کپی"))
            
            copy_btn = tk.Button(copy_frame, text="📋 کپی", command=copy_full_id,
                                bg=colors['accent'], fg='white', 
                                font=(persian_font, 9, 'bold'),
                                relief='flat', padx=12, pady=2, cursor='hand2',
                                width=7)
            copy_btn.pack(side='left')
            
            # ========== کارت مراحل ==========
            steps_card = tk.Frame(main, bg=colors['card'], relief='flat', bd=1,
                                 highlightbackground=colors['border'], highlightthickness=1)
            steps_card.pack(fill='x', pady=(0, 10))
            
            # عنوان کارت
            tk.Label(steps_card, text="📋 مراحل فعال‌سازی", font=('Vazir', 10, 'bold'),
                    bg=colors['primary'], fg='white', padx=10, pady=4).pack(fill='x')
            
            # محتوای کارت
            steps_body = tk.Frame(steps_card, bg=colors['card'], padx=12, pady=8)
            steps_body.pack(fill='x')
            
            steps = [
                ("1", "کپی شناسه سیستم"),
                ("2", "ارسال به پشتیبانی"),
                ("3", "دریافت فایل لایسنس"),
                ("4", "قرار دادن در پوشه برنامه"),
                ("5", "اجرای مجدد برنامه")
            ]
            
            for num, text in steps:
                step_frame = tk.Frame(steps_body, bg=colors['card'])
                step_frame.pack(fill='x', pady=2)
                
                tk.Label(step_frame, text=f"{num}️⃣", font=('Segoe UI', 11),
                        bg=colors['card'], fg=colors['primary']).pack(side='right', padx=(0, 5))
                
                tk.Label(step_frame, text=text, font=(persian_font, 10),
                        bg=colors['card'], fg=colors['text']).pack(side='right')
            
            # ========== کارت پشتیبانی ==========
            support_card = tk.Frame(main, bg=colors['card'], relief='flat', bd=1,
                                   highlightbackground=colors['border'], highlightthickness=1)
            support_card.pack(fill='x', pady=(0, 10))
            
            # عنوان کارت
            tk.Label(support_card, text="📞 پشتیبانی", font=(persian_font, 10, 'bold'),
                    bg=colors['primary'], fg='white', padx=10, pady=4).pack(fill='x')
            
            # محتوای کارت
            support_body = tk.Frame(support_card, bg=colors['card'], padx=12, pady=10)
            support_body.pack(fill='x')
            
            # اطلاعات تماس در یک خط
            contact_frame = tk.Frame(support_body, bg=colors['card'])
            contact_frame.pack(fill='x', pady=2)
            
            tk.Label(contact_frame, text="📱 09364019466", font=('Segoe UI', 10, 'bold'),
                    bg=colors['card'], fg=colors['primary']).pack(side='bottom', padx=(0, 10))
            
            tk.Label(contact_frame, text="h8968a@gmail.com", font=('Segoe UI', 9,'bold'),
                    bg=colors['card'], fg=colors['text']).pack(side='bottom')
            
            # ========== وضعیت و دکمه خروج ==========
            status_label = tk.Label(main, text="", font=('Vazir', 9),
                                   bg=colors['background'], fg=colors['success'])
            status_label.pack(pady=5)
            
            # دکمه خروج
            def exit_app():
                if messagebox.askyesno("خروج", "آیا می‌خواهید خارج شوید؟"):
                    root.quit()
                    root.destroy()
                    sys.exit(0)
            
            btn_frame = tk.Frame(main, bg=colors['background'])
            btn_frame.pack(fill='x', pady=5)
            
            
            # فوتر
            footer = tk.Label(root, text="© ۱۳۹۸ سیستم مدیریت پمپ بنزین", 
                             font=(persian_font, 7),
                             bg=colors['background'], fg='#95a5a6')
            footer.pack(side='bottom', pady=3)
            
            root.protocol("WM_DELETE_WINDOW", exit_app)
            root.mainloop()
            
    except Exception as e:
        debug_print(f"خطا: {e}")
        try:
            messagebox.showerror("خطا", f"خطا در اجرای برنامه: {e}")
        except:
            pass
# ==================== کلاس اصلی برنامه (بخش تغییر یافته) ====================
class GasStationManagementSystem:
    def __init__(self, root, skip_license_check=False):
        self.root = root
        
        if not skip_license_check:
            # اگر بررسی لایسنس انجام نشده بود، اینجا انجام بده
            if not self.check_license():
                return
        
        self.temporary_storage = TemporaryStorage()
        
        saved_data = self.temporary_storage.load_data()
        if JDATETIME_AVAILABLE:
            if saved_data and 'current_date' in saved_data:
                self.current_date = saved_data['current_date']
            else:
                self.current_date = jdatetime.date.today().strftime("%Y%m%d")
        else:
            if saved_data and 'current_date' in saved_data:
                self.current_date = saved_data['current_date']
            else:
                self.current_date = datetime.now().strftime("%Y%m%d")
        
        self.setup_ui()
        self.load_saved_data()  # بارگذاری داده‌های ذخیره‌شده
        debug_print("برنامه با موفقیت راه‌اندازی شد")
    
    def check_license(self):
        # این متد دیگر استفاده نمی‌شود چون بررسی در main انجام می‌شود
        return True
    
    def setup_ui(self):
        try:
            self.root.title("سیستم مدیریت پمپ بنزین v1.0")
            self.root.geometry("1350x768")
            self.root.grid_rowconfigure(0, weight=1)
            self.root.grid_columnconfigure(0, weight=1)
            
            if COMPONENTS_AVAILABLE:
                self.notebook = ttk.Notebook(self.root)
                self.notebook.grid(row=0, column=0, padx=10, pady=5, sticky='nsew')
                
                # ساخت کامپوننت‌ها
                self.form1 = Form1Component(self.notebook, shift_id=f"{self.current_date}01")
                self.form2sh = Form2SHComponent(self.notebook, self.form1, shift_id=f"{self.current_date}02")
                self.form2 = Form2Component(self.notebook, self.form1, self.form2sh)
                self.form3 = Form3Component(self.notebook, self.form1, self.form2, self.form2sh)
                
                # اضافه کردن تب‌ها
                self.notebook.add(self.form1.frame, text='شیفت اول')
                self.notebook.add(self.form2sh.frame, text='شیفت دوم')
                self.notebook.add(self.form2.frame, text='مالی')
                self.notebook.add(self.form3.frame, text='شمارنده‌ها')
                
                # دکمه‌ها
                btn_frame = ttk.Frame(self.root)
                btn_frame.grid(row=1, column=0, pady=5, sticky='ew')
                
                tk.Button(btn_frame, text="محاسبه همه", command=self.calculate_all, bg='green', fg='white').pack(side='left', padx=5)
                tk.Button(btn_frame, text="ذخیره موقت", command=self.save_temporary_data, bg='blue', fg='white').pack(side='left', padx=5)
                tk.Button(btn_frame, text="چاپ PDF", command=self.print_forms_pdf, bg='orange', fg='white').pack(side='left', padx=5)
                tk.Button(btn_frame, text="پایان روز (پاک کردن)", command=self.finalize_day, bg='red', fg='white').pack(side='left', padx=5)
                
                self.result_text = tk.Text(self.root, height=5)
                self.result_text.grid(row=2, column=0, sticky='ew', padx=10)
                
                hw_info = HardwareLock().get_hardware_id()
                short_id = hw_info['short_id']    

                self.root.title(f"مدیریت پمپ بنزین v1.0 - ID: {short_id}")

                # PDF Exporter
                self.pdf_exporter = PDFExporter(self.form1, self.form2sh, self.form2, self.form3, self.result_text)
                
                # نمایش شناسه
                # info = tk.Label(self.root, text=f"شناسه: {hw_info['short_id']}", font=('Courier', 8), fg='gray')
                # info.grid(row=3, column=0, pady=5, sticky='s')
                
            else:
                label = tk.Label(self.root, text="سیستم مدیریت پمپ بنزین\n(نسخه آزمایشی)", 
                               font=('Tahoma', 24, 'bold'))
                label.pack(expand=True)
            
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در راه‌اندازی: {e}")
            import traceback
            traceback.print_exc()
    
    def calculate_all(self):
        try:
            f1_data = self.form1.get_data()
            for nozzle_num, nozzle_data in f1_data['nozzles'].items():
                if nozzle_num in self.form2sh.entries:
                    end_value_f1 = nozzle_data['end']
                    
                    start_entry_f2sh = self.form2sh.entries[nozzle_num]['آغاز']
                    start_entry_f2sh.config(state='normal')
                    start_entry_f2sh.delete(0, tk.END)
                    start_entry_f2sh.insert(0, end_value_f1)
                    start_entry_f2sh.config(state='readonly')
            self.root.update()
            self.form1.calculate()
            self.form2sh.calculate()
            self.form2.calculate()
            self.form3.calculate()
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, "محاسبات تمام فرم‌ها انجام شد.")
        except Exception as e:
            messagebox.showerror("خطا", str(e))
    
    def save_temporary_data(self):
        try:
            s1 = self.form1.get_data()
            s2 = self.form2sh.get_data()
            form2_data = self.get_form2_data()
            if self.temporary_storage.save_data(s1, s2, form2_data, self.current_date):
                self.result_text.insert(tk.END, "\nذخیره موقت انجام شد.")
            else:
                messagebox.showerror("خطا", "ذخیره نشد.")
        except Exception as e:
            messagebox.showerror("خطا", str(e))
            
    def get_form2_data(self):
        """دریافت داده‌های فرم مالی برای ذخیره‌سازی"""
        try:
            if not hasattr(self, 'form2'):
                return None
                
            data = {}
            
            # ذخیره فیلدهای خلاصه روزانه
            for key, entry in self.form2.entries.items():
                try:
                    data[key] = entry.get()
                except:
                    data[key] = ""
            
            # ذخیره فیلدهای جدول جزئیات
            for key, entry in self.form2.detail_entries.items():
                try:
                    data[f"detail_{key}"] = entry.get()
                except:
                    data[f"detail_{key}"] = ""
            
            return data
        except Exception as e:
            debug_print(f"خطا در دریافت داده‌های فرم مالی: {e}")
            return None
    
    def load_saved_data(self):
        data = self.temporary_storage.load_data()
        if not data: return
        
        try:
        # بازیابی داده‌های شیفت اول
            if 'shift1_data' in data and data['shift1_data']:
                self._populate_form(self.form1, data['shift1_data'])
            
            # بازیابی داده‌های شیفت دوم
            if 'shift2_data' in data and data['shift2_data']:
                self._populate_form(self.form2sh, data['shift2_data'])
            
            # بازیابی داده‌های فرم مالی
            if 'form2_data' in data and data['form2_data'] and hasattr(self, 'form2'):
                self._populate_form2(data['form2_data'])
                self.result_text.insert(tk.END, "داده‌های قبلی بازیابی شدند.\n")
        except Exception as e:
            debug_print(f"Load error: {e}")
            
    def _populate_form2(self, form2_data):
        """پر کردن فرم مالی با داده‌های ذخیره شده"""
        try:
            if not hasattr(self, 'form2'):
                return
            
            # پر کردن فیلدهای خلاصه روزانه
            for key, entry in self.form2.entries.items():
                if key in form2_data:
                    try:
                        entry.config(state='normal')
                        entry.delete(0, tk.END)
                        entry.insert(0, form2_data[key])
                        if key not in ['start_inv', 'end_inv', 'mech_diff', 'received', 'bank_exit', 'safe_box']:
                            entry.config(state='readonly')
                    except:
                        pass
            
            # پر کردن فیلدهای جدول جزئیات
            for key, entry in self.form2.detail_entries.items():
                data_key = f"detail_{key}"
                if data_key in form2_data:
                    try:
                        current_state = entry.cget('state')
                        entry.config(state='normal')
                        entry.delete(0, tk.END)
                        entry.insert(0, form2_data[data_key])
                        entry.config(state=current_state)
                    except:
                        pass
                        
        except Exception as e:
            debug_print(f"خطا در پر کردن فرم مالی: {e}")        
        
    def _populate_form(self, form, data):
        try:
            # نازل‌ها
            if 'nozzles' in data:
                for n_str, vals in data['nozzles'].items():
                    n = int(n_str)
                    if n in form.entries:
                        if 'end' in vals: form.entries[n]['پایان'].delete(0, tk.END); form.entries[n]['پایان'].insert(0, vals['end'])
                        if 'start' in vals: form.entries[n]['آغاز'].delete(0, tk.END); form.entries[n]['آغاز'].insert(0, vals['start'])
            
            # جدول مالی
            if 'financial' in data:
                fin = data['financial']
                if 'total_elec' in fin: 
                    form.total_elec_entry.delete(0, tk.END)
                    form.total_elec_entry.insert(0, fin['total_elec'])
                if 'total_subsidy' in fin:
                    form.total_subsidy_entry.delete(0, tk.END)
                    form.total_subsidy_entry.insert(0, fin['total_subsidy'])
                if 'total_semi' in fin:
                    form.total_semi_entry.delete(0, tk.END)
                    form.total_semi_entry.insert(0, fin['total_semi'])
                if 'total_azad_1' in fin:  # ✅ First AZAD
                    form.total_azad_entry_1.delete(0, tk.END)
                    form.total_azad_entry_1.insert(0, fin['total_azad_1'])
                if 'total_azad_2' in fin:  # ✅ Second AZAD
                    form.total_azad_entry_2.delete(0, tk.END)
                    form.total_azad_entry_2.insert(0, fin['total_azad_2'])
            
            # متصدی‌ها
            if 'operator1' in data and hasattr(form, 'operator_entry_1'):
                form.operator_entry_1.delete(0, tk.END)
                form.operator_entry_1.insert(0, data['operator1'])
            if 'operator2' in data and hasattr(form, 'operator_entry_2'):
                form.operator_entry_2.delete(0, tk.END)
                form.operator_entry_2.insert(0, data['operator2'])
            
            # کارتخوان‌ها
            if 'card_readers' in data:
                for i, val in enumerate(data['card_readers']):
                    if i < len(form.card_reader_entries):
                        form.card_reader_entries[i].delete(0, tk.END)
                        form.card_reader_entries[i].insert(0, val)
        except Exception as e:
            debug_print(f"Error populating: {e}")
    
    def finalize_day(self):
        if messagebox.askyesno("تایید", "آیا مطمئن هستید؟ داده‌های امروز پاک می‌شوند."):
            self.temporary_storage.clear_data()
            # ریست کردن فرم‌ها (می‌توانید متد clear برای هر کامپوننت اضافه کنید)
            self.root.destroy()
            python = sys.executable
            os.execl(python, python, *sys.argv)
    
    def print_forms_pdf(self):
        self.calculate_all()
        self.pdf_exporter.print_forms_pdf()

if __name__ == "__main__":
    show_splash(main)
