# main.py
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import logging
from pathlib import Path
import os
from datetime import datetime
import queue
import threading
import json
import time
import shutil
import subprocess
import re
import sys
import webbrowser

# --- Import các module của dự án ---
try:
    import ttkbootstrap as ttkb
    from ttkbootstrap.constants import *
except ImportError:
    # Fallback cho trường hợp không có ttkbootstrap
    import tkinter.ttk as ttkb
    PRIMARY, SECONDARY, SUCCESS, INFO, WARNING, DANGER, LIGHT, DARK, OUTLINE = ("primary", "secondary", "success", "info", "warning", "danger", "light", "dark", "outline")

try:
    import config
    from utils.logger_setup import setup_logging, log_error_details, log_session_end
    from report_processor import ReportProcessor
    from utils.file_utils import is_file_locked, setup_project_directories
    from utils.watcher import Watcher
    from utils.scheduler import TaskScheduler
    from utils.email_notifier import send_notification_email
    from utils.input_validator import validate_email, validate_excel_file, validate_file_path
    from utils.credential_manager import (
        save_smtp_credentials, get_smtp_credentials, delete_smtp_credentials,
        has_stored_credentials, get_credential_storage_info, test_smtp_connection
    )
except ImportError as e:
    messagebox.showerror("Lỗi Khởi Tạo Nghiêm Trọng", f"Không thể import các module cần thiết:\n{e}\n\nVui lòng kiểm tra cấu trúc thư mục và cài đặt.")
    sys.exit()

# --- Load Environment Configuration (Phase 3.1D) ---
# Load sensitive settings from environment variables before application initialization
config.load_environment_config()

# --- Các hằng số ---
SETTINGS_FILE = Path("app_settings.json")
REQUIRED_DIRS = ["data_input", "backup", "outputs", "templates"]

class TextHandler(logging.Handler):
    def __init__(self, text_queue):
        super().__init__()
        self.text_queue = text_queue

    def emit(self, record):
        msg = self.format(record)
        self.text_queue.put(msg)

class App(ttkb.Window):
    def __init__(self):
        super().__init__(themename="litera")
        self.title(f"📦 {config.APP_TITLE} v{config.APP_VERSION}")
        self.geometry("800x600")
        self.protocol("WM_DELETE_WINDOW", self.on_closing) # Sửa lỗi: Gọi đến hàm on_closing đã được định nghĩa

        self.output_dir = Path.cwd()
        self.log_queue = queue.Queue()
        self.processor_thread = None
        self.watcher = None
        self.watcher_queue = queue.Queue()
        self.scheduler = None
        self.settings_window = None

        if not setup_project_directories(Path.cwd(), REQUIRED_DIRS):
            self.destroy()
            return

        self.load_settings()
        self.create_widgets()
        self.setup_logging()
        self.after(100, self.process_log_queue)
        self.after(2000, self.check_watcher_queue)
        self.init_scheduler()

    def load_settings(self):
        # Đặt giá trị mặc định trước
        self.schedule_time_var = tk.StringVar(value="08:00")
        self.schedule_enabled_var = tk.BooleanVar(value=False)
        self.email_enabled_var = tk.BooleanVar(value=False)
        self.recipient_email_var = tk.StringVar(value="")
        self.smtp_server_var = tk.StringVar(value="smtp.gmail.com")
        self.smtp_port_var = tk.StringVar(value="587")
        # SMTP credentials are NOT stored in settings - use credential_manager
        self.smtp_user_var = tk.StringVar(value="")  # Session only, not saved
        self.smtp_pass_var = tk.StringVar(value="")  # Session only, not saved
        self._credentials_configured = has_stored_credentials()

        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    last_dir = settings.get('last_output_dir')
                    if last_dir and Path(last_dir).exists():
                        self.output_dir = Path(last_dir)
                    
                    self.schedule_time_var.set(settings.get("schedule_time", "08:00"))
                    self.schedule_enabled_var.set(settings.get("schedule_enabled", False))
                    self.email_enabled_var.set(settings.get("email_enabled", False))
                    self.recipient_email_var.set(settings.get("recipient_email", ""))
                    self.smtp_server_var.set(settings.get("smtp_server", "smtp.gmail.com"))
                    self.smtp_port_var.set(settings.get("smtp_port", "587"))
                    # NOTE: smtp_user and smtp_pass are NOT loaded from file
                    # They are retrieved from secure storage (keyring/env vars) when needed
            except Exception as e:
                logging.error(f"Lỗi đọc file settings: {e}")

    def save_settings(self):
        # NOTE: SMTP credentials are NOT saved here - use credential_manager for secure storage
        settings = {
            'last_output_dir': str(self.output_dir),
            'schedule_time': self.schedule_time_var.get(),
            'schedule_enabled': self.schedule_enabled_var.get(),
            'email_enabled': self.email_enabled_var.get(),
            'recipient_email': self.recipient_email_var.get(),
            'smtp_server': self.smtp_server_var.get(),
            'smtp_port': self.smtp_port_var.get()
            # smtp_user and smtp_pass are stored securely via credential_manager
        }
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            logging.error(f"Lỗi ghi file settings: {e}")

    def init_scheduler(self):
        self.scheduler = TaskScheduler(job_func=self.run_scheduled_task)
        if self.schedule_enabled_var.get():
            time_str = self.schedule_time_var.get()
            self.scheduler.set_schedule(time_str)
            self.scheduler.start()

    def run_scheduled_task(self):
        logging.info("[Scheduler] Bắt đầu tác vụ đã lên lịch...")
        self.status_label.config(text="⏰ Đang chạy tác vụ đã lên lịch...")
        input_path = Path("data_input")
        if not input_path.exists() or not any(input_path.iterdir()):
            logging.info("[Scheduler] Thư mục 'data_input' trống. Không có gì để xử lý.")
            return
        
        files_to_process = list(input_path.glob("*.xlsx")) + list(input_path.glob("*.xls"))
        if files_to_process:
            self.start_processing(input_files=files_to_process, from_scheduler=True)
        else:
            logging.info("[Scheduler] Không tìm thấy file Excel nào trong 'data_input'.")

    def setup_logging(self):
        setup_logging()
        text_handler = TextHandler(self.log_queue)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s', datefmt='%H:%M:%S')
        text_handler.setFormatter(formatter)
        text_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(text_handler)
        logging.info(f"Ứng dụng {config.APP_TITLE} đã khởi động.")

    def process_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_text_widget.config(state=tk.NORMAL)
                self.log_text_widget.insert(tk.END, msg + "\n")
                self.log_text_widget.see(tk.END)
                self.log_text_widget.config(state=tk.DISABLED)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_log_queue)

    def create_widgets(self):
        main_frame = ttkb.Frame(self, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        status_progress_frame = ttkb.Frame(main_frame)
        status_progress_frame.grid(row=0, column=0, sticky="ew", pady=(5, 10), padx=5)
        status_progress_frame.columnconfigure(0, weight=1)

        self.status_label = ttkb.Label(status_progress_frame, text="✅ Ready...", font=("Segoe UI", 11, "bold"), anchor="w")
        self.status_label.grid(row=0, column=0, columnspan=2, sticky="ew")

        self.progress_bar = ttkb.Progressbar(status_progress_frame, orient="horizontal", length=300, mode="determinate", bootstyle=SUCCESS)
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(5, 0), padx=(0, 5))

        self.progress_label = ttkb.Label(status_progress_frame, text="0%", font=("Segoe UI", 10), width=5, anchor="e")
        self.progress_label.grid(row=1, column=1, sticky="e", pady=(5, 0))

        button_frame = ttkb.Frame(main_frame)
        button_frame.grid(row=1, column=0, pady=(15, 15))

        self.process_button = ttkb.Button(button_frame, text="📁 Select files", command=self.start_processing, width=15, bootstyle=PRIMARY)
        self.process_button.pack(side=tk.LEFT, padx=5)

        self.pbi_button = ttkb.Button(button_frame, text="📊 Open Power BI Report", command=self.open_powerbi_report, width=25, bootstyle=SUCCESS)
        self.pbi_button.pack(side=tk.LEFT, padx=5)
        
        self.dashboard_button = ttkb.Button(button_frame, text="📈 Open Web Dashboard", command=self.open_web_dashboard, width=25, bootstyle="info")
        self.dashboard_button.pack(side=tk.LEFT, padx=5)

        self.open_folder_button = ttkb.Button(button_frame, text="📂 Open Output folder", command=self.open_output_folder, width=25, bootstyle=SECONDARY)
        self.open_folder_button.pack(side=tk.LEFT, padx=5)

        options_frame = ttkb.Frame(main_frame)
        options_frame.grid(row=2, column=0, pady=5)

        self.overwrite_var = tk.BooleanVar(value=False)
        self.overwrite_check = ttkb.Checkbutton(options_frame, text="Process previously processed files", variable=self.overwrite_var, bootstyle="round-toggle")
        self.overwrite_check.pack(side=tk.LEFT, padx=10)

        self.auto_mode_var = tk.BooleanVar(value=False)
        self.auto_mode_check = ttkb.Checkbutton(options_frame, text="Auto-process new files", variable=self.auto_mode_var, bootstyle="success-round-toggle", command=self.toggle_auto_mode)
        self.auto_mode_check.pack(side=tk.LEFT, padx=10)

        self.settings_button = ttkb.Button(options_frame, text="⚙️ Settings", command=self.open_settings_window, width=15, bootstyle=(DARK, OUTLINE))
        self.settings_button.pack(side=tk.LEFT, padx=10)

        self.toggle_log_button = ttkb.Button(options_frame, text="🔽 Show Log", command=self.toggle_log_visibility, width=15, bootstyle=(INFO, OUTLINE))
        self.toggle_log_button.pack(side=tk.LEFT, padx=10)
        
        self.log_frame = ttkb.LabelFrame(main_frame, text="📝 Activity Log", padding=(10, 5))
        self.log_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 5), padx=5)
        self.log_frame.columnconfigure(0, weight=1)
        self.log_frame.rowconfigure(0, weight=1)

        self.log_text_widget = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, font=("Consolas", 9), height=10)
        self.log_text_widget.grid(row=0, column=0, sticky="nsew")
        self.log_text_widget.config(state=tk.DISABLED)
        self.log_frame.grid_remove()

        footer_frame = ttkb.Frame(main_frame, bootstyle=LIGHT)
        footer_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0), padx=5)
        footer_frame.columnconfigure(0, weight=1) 

        current_year = datetime.now().year
        footer_text = f"Developed by: Tien-Tan Thuan Port | Version {config.APP_VERSION} | © {current_year}"
        
        developed_by_label = ttkb.Label(footer_frame, text=footer_text, font=("Segoe UI", 8), anchor="e")
        developed_by_label.grid(row=0, column=1, sticky="e", padx=10, pady=3)

    def toggle_log_visibility(self):
        if self.log_frame.winfo_viewable():
            self.log_frame.grid_remove()
            self.toggle_log_button.config(text="🔽 Show Log")
        else:
            self.log_frame.grid()
            self.toggle_log_button.config(text="🔼 Hide Log")

    def toggle_auto_mode(self):
        if self.auto_mode_var.get():
            input_path = Path("data_input")
            if not self.watcher:
                self.watcher = Watcher(input_path, self.watcher_queue)
            self.watcher.start()
            self.status_label.config(text="👀 Auto-mode ON. Watching 'data_input' folder...")
        else:
            if self.watcher:
                self.watcher.stop()
            self.status_label.config(text="✅ Ready (Auto-mode OFF).")

    def check_watcher_queue(self):
        files_to_process = []
        try:
            while not self.watcher_queue.empty():
                filepath = self.watcher_queue.get_nowait()
                files_to_process.append(filepath)
        except queue.Empty:
            pass

        if files_to_process:
            unique_files = list(set(files_to_process))
            logging.info(f"Watcher queue sent {len(unique_files)} new file(s) to process.")
            self.start_processing(input_files=unique_files)

        self.after(2000, self.check_watcher_queue)

    def open_powerbi_report(self):
        template_path = Path("templates/tdr_dashboard_template.pbit")
        output_dir = Path("outputs")
        
        if not template_path.exists():
            messagebox.showerror("Lỗi", f"Không tìm thấy file template Power BI tại:\n{template_path.resolve()}")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = f"TDR_Dashboard_{timestamp}.pbit"
        new_report_path = output_dir / report_name

        try:
            shutil.copy(template_path, new_report_path)
            logging.info(f"Đã tạo file báo cáo mới: {new_report_path}")
            messagebox.showinfo("Mở Power BI",
                                "Một file báo cáo Power BI mới đã được tạo.\n\n"
                                "Khi Power BI mở ra, nó sẽ hỏi bạn đường dẫn đến các file CSV. "
                                f"Vui lòng trỏ đến thư mục:\n\n{Path('outputs/data_csv').resolve()}",
                                parent=self)
            os.startfile(new_report_path)
        except Exception as e:
            logging.error(f"Lỗi khi xử lý file Power BI: {e}", exc_info=True)
            messagebox.showerror("Lỗi", f"Không thể tạo hoặc mở file báo cáo Power BI.\nLỗi: {e}")

    def _open_browser_after_delay(self):
        """Hàm phụ để chờ và mở trình duyệt."""
        time.sleep(3)
        webbrowser.open("http://localhost:8501")

    def open_web_dashboard(self):
        dashboard_script = "dashboard.py"
        if not Path(dashboard_script).exists():
            messagebox.showerror("Lỗi", f"Không tìm thấy file dashboard: {dashboard_script}")
            return

        logging.info("[Dashboard] Đang khởi chạy Web Dashboard...")
        try:
            if hasattr(sys, '_MEIPASS'):
                streamlit_executable = "streamlit"
            else:
                streamlit_executable = os.path.join(sys.prefix, 'Scripts', 'streamlit.exe')
                if not os.path.exists(streamlit_executable):
                    streamlit_executable = os.path.join(sys.prefix, 'bin', 'streamlit')

            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            command = [
                streamlit_executable, "run", dashboard_script,
                "--server.headless", "true", "--server.enableCORS", "false"
            ]

            subprocess.Popen(command, startupinfo=startupinfo)
            self.status_label.config(text="📈 Web Dashboard is running in the browser...")
            
            threading.Thread(target=self._open_browser_after_delay, daemon=True).start()

        except FileNotFoundError:
            logging.error("Lỗi không tìm thấy lệnh 'streamlit'.")
            messagebox.showerror("Lỗi", "Không tìm thấy lệnh 'streamlit'.\nVui lòng đảm bảo Streamlit đã được cài đặt đúng cách.")
        except Exception as e:
            logging.error(f"Lỗi khi khởi chạy dashboard: {e}", exc_info=True)
            messagebox.showerror("Lỗi", f"Không thể khởi chạy Web Dashboard.\nLỗi: {e}")

    def open_settings_window(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return

        self.settings_window = ttkb.Toplevel(master=self, title="Settings")
        self.settings_window.geometry("450x500")

        schedule_frame = ttkb.LabelFrame(self.settings_window, text="⏰ Daily Schedule", padding=10)
        schedule_frame.pack(pady=10, padx=10, fill="x")
        ttkb.Checkbutton(schedule_frame, text="Enable daily schedule", variable=self.schedule_enabled_var, bootstyle="success-round-toggle").pack(anchor="w")
        
        time_entry_frame = ttkb.Frame(schedule_frame)
        time_entry_frame.pack(pady=5, fill="x")
        ttkb.Label(time_entry_frame, text="Run at (HH:MM):").pack(side="left", padx=5)
        ttkb.Entry(time_entry_frame, textvariable=self.schedule_time_var, width=10).pack(side="left")

        email_frame = ttkb.LabelFrame(self.settings_window, text="📧 Email Notification", padding=10)
        email_frame.pack(pady=10, padx=10, fill="x")
        ttkb.Checkbutton(email_frame, text="Enable email notifications", variable=self.email_enabled_var, bootstyle="success-round-toggle").pack(anchor="w")
        
        grid_frame = ttkb.Frame(email_frame)
        grid_frame.pack(fill="x", padx=5, pady=5)
        grid_frame.columnconfigure(1, weight=1)

        ttkb.Label(grid_frame, text="Recipient Email:").grid(row=0, column=0, sticky="w", pady=2)
        ttkb.Entry(grid_frame, textvariable=self.recipient_email_var).grid(row=0, column=1, sticky="ew", pady=2)
        ttkb.Label(grid_frame, text="SMTP Server:").grid(row=1, column=0, sticky="w", pady=2)
        ttkb.Entry(grid_frame, textvariable=self.smtp_server_var).grid(row=1, column=1, sticky="ew", pady=2)
        ttkb.Label(grid_frame, text="SMTP Port:").grid(row=2, column=0, sticky="w", pady=2)
        ttkb.Entry(grid_frame, textvariable=self.smtp_port_var).grid(row=2, column=1, sticky="ew", pady=2)
        
        # SMTP Credentials section with secure storage
        cred_frame = ttkb.LabelFrame(email_frame, text="🔐 SMTP Credentials (Secure Storage)", padding=5)
        cred_frame.pack(fill="x", padx=5, pady=5)
        cred_frame.columnconfigure(1, weight=1)
        
        # Show credential storage status
        self.cred_status_var = tk.StringVar(value=f"Status: {get_credential_storage_info()}")
        ttkb.Label(cred_frame, textvariable=self.cred_status_var, bootstyle="info").grid(row=0, column=0, columnspan=3, sticky="w", pady=2)
        
        ttkb.Label(cred_frame, text="SMTP User:").grid(row=1, column=0, sticky="w", pady=2)
        ttkb.Entry(cred_frame, textvariable=self.smtp_user_var).grid(row=1, column=1, sticky="ew", pady=2)
        ttkb.Label(cred_frame, text="SMTP Password:").grid(row=2, column=0, sticky="w", pady=2)
        ttkb.Entry(cred_frame, textvariable=self.smtp_pass_var, show="*").grid(row=2, column=1, sticky="ew", pady=2)
        
        # Buttons for credential management
        btn_frame = ttkb.Frame(cred_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=5)
        ttkb.Button(btn_frame, text="🔗 Test Connection", command=self._test_smtp_connection, bootstyle=INFO).pack(side="left", padx=2)
        ttkb.Button(btn_frame, text="💾 Save Credentials", command=self._save_smtp_credentials, bootstyle=SUCCESS).pack(side="left", padx=2)
        ttkb.Button(btn_frame, text="🗑️ Clear Credentials", command=self._clear_smtp_credentials, bootstyle=DANGER+OUTLINE).pack(side="left", padx=2)
        
        # Info label
        ttkb.Label(cred_frame, text="⚠️ Credentials are stored securely (not in config files)", 
                   bootstyle="warning", font=("", 8)).grid(row=4, column=0, columnspan=2, sticky="w")

        save_button = ttkb.Button(self.settings_window, text="Save and Apply Settings", command=self.apply_settings, bootstyle=SUCCESS)
        save_button.pack(pady=20)

    def _test_smtp_connection(self):
        """Test SMTP connection with current credentials."""
        smtp_user = self.smtp_user_var.get().strip()
        smtp_pass = self.smtp_pass_var.get()
        smtp_server = self.smtp_server_var.get().strip()
        
        try:
            smtp_port = int(self.smtp_port_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid SMTP port", parent=self.settings_window)
            return
        
        if not all([smtp_user, smtp_pass, smtp_server]):
            messagebox.showwarning("Warning", "Please fill in SMTP User, Password and Server", parent=self.settings_window)
            return
        
        success, message = test_smtp_connection(smtp_server, smtp_port, smtp_user, smtp_pass)
        if success:
            messagebox.showinfo("Success", message, parent=self.settings_window)
        else:
            messagebox.showerror("Connection Failed", message, parent=self.settings_window)

    def _save_smtp_credentials(self):
        """Save SMTP credentials to secure storage."""
        smtp_user = self.smtp_user_var.get().strip()
        smtp_pass = self.smtp_pass_var.get()
        
        if not smtp_user or not smtp_pass:
            messagebox.showwarning("Warning", "Please enter both SMTP User and Password", parent=self.settings_window)
            return
        
        if save_smtp_credentials(smtp_user, smtp_pass):
            self._credentials_configured = True
            self.cred_status_var.set(f"Status: {get_credential_storage_info()}")
            messagebox.showinfo("Success", "Credentials saved securely!", parent=self.settings_window)
        else:
            messagebox.showerror("Error", "Failed to save credentials", parent=self.settings_window)

    def _clear_smtp_credentials(self):
        """Clear stored SMTP credentials."""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear stored credentials?", parent=self.settings_window):
            delete_smtp_credentials()
            self.smtp_user_var.set("")
            self.smtp_pass_var.set("")
            self._credentials_configured = False
            self.cred_status_var.set("Status: Not Configured")
            messagebox.showinfo("Success", "Credentials cleared", parent=self.settings_window)

    def apply_settings(self):
        try:
            schedule_enabled = self.schedule_enabled_var.get()
            schedule_time = self.schedule_time_var.get()
            email_enabled = self.email_enabled_var.get()
            recipient_email = self.recipient_email_var.get().strip()
            smtp_port_str = self.smtp_port_var.get().strip()

            if schedule_enabled:
                time.strptime(schedule_time, '%H:%M')

            if email_enabled:
                if not smtp_port_str.isdigit() or not (1 <= int(smtp_port_str) <= 65535):
                    raise ValueError("SMTP Port must be a number between 1 and 65535.")
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', recipient_email):
                    raise ValueError(f"Invalid recipient email format: '{recipient_email}'.")
                # Check for credentials in secure storage or session
                creds = get_smtp_credentials()
                has_session_creds = self.smtp_user_var.get() and self.smtp_pass_var.get()
                if not creds and not has_session_creds:
                    raise ValueError("SMTP credentials not configured. Please save credentials first.")

        except ValueError as e:
            messagebox.showerror("Validation Error", str(e), parent=self.settings_window)
            return

        self.save_settings()
        
        if self.schedule_enabled_var.get():
            time_str = self.schedule_time_var.get()
            self.scheduler.set_schedule(time_str)
            if not self.scheduler.is_running():
                self.scheduler.start()
            logging.info(f"[Scheduler] Đã áp dụng lịch chạy hàng ngày vào lúc {time_str}.")
        else:
            if self.scheduler.is_running():
                self.scheduler.stop()
            self.scheduler.clear_schedule()
            logging.info("[Scheduler] Lịch chạy hàng ngày đã được tắt.")
            
        messagebox.showinfo("Saved", "Settings have been saved and applied.", parent=self.settings_window)
        self.settings_window.destroy()

    def start_processing(self, input_files=None, from_scheduler=False):
        if self.processor_thread and self.processor_thread.is_alive():
            messagebox.showwarning("Processing", "Another process is already running. Please wait.")
            return

        files_to_process = []
        if from_scheduler:
            files_to_process = input_files
        elif input_files: # Từ watcher
            files_to_process = input_files
        else: # Từ nút bấm
            files = filedialog.askopenfilenames(title="Select TDR files (.xlsx, .xls)", filetypes=[("Excel files", "*.xlsx *.xls")])
            if not files:
                logging.info("User selected no files.")
                return
            files_to_process = [Path(f) for f in files]

        if not files_to_process:
            logging.warning("No files selected or found to process.")
            return

        self.set_gui_state(processing=True)
        self.processor_thread = threading.Thread(
            target=self.processing_worker,
            args=(files_to_process, self.output_dir, self.overwrite_var.get()),
            daemon=True
        )
        self.processor_thread.start()

    def processing_worker(self, file_paths, output_dir, overwrite):
        start_total_time = time.perf_counter()
        try:
            valid_files = []
            locked_files_log = []
            invalid_files_log = []
            
            for path in file_paths:
                self.update_status(f"Validating file: {path.name}")
                
                # SECURITY: Validate file path to prevent traversal attacks
                is_valid, error = validate_file_path(str(path))
                if not is_valid:
                    logging.error(f"File path validation failed: {error}")
                    invalid_files_log.append(f"{path.name}: {error}")
                    continue
                
                # SECURITY: Validate Excel file type and size
                is_valid, error = validate_excel_file(str(path), max_size_mb=100)
                if not is_valid:
                    logging.error(f"File validation failed: {error}")
                    invalid_files_log.append(f"{path.name}: {error}")
                    continue
                
                if is_file_locked(path):
                    locked_files_log.append(path.name)
                else:
                    valid_files.append(path)
            
            if invalid_files_log:
                self.after(0, lambda: messagebox.showwarning(
                    "Invalid Files",
                    "The following files are invalid and will be skipped:\n\n" + "\n".join(invalid_files_log)
                ))

            if locked_files_log:
                self.after(0, lambda: messagebox.showwarning(
                    "File Locked",
                    "The following files are in use and will be skipped:\n\n" + "\n".join(locked_files_log)
                ))

            if not valid_files:
                self.after(0, self.on_processing_complete, {"message": "No valid files to process."})
                return

            processor = ReportProcessor(output_dir)
            result = processor.process_tdr_files(
                valid_files,
                update_status_callback=self.update_status,
                update_progress_callback=self.update_progress,
                overwrite=overwrite
            )
            
            end_total_time = time.perf_counter()
            result['time_taken'] = end_total_time - start_total_time
            
            self.after(0, self.on_processing_complete, result)

        except Exception as e:
            error_context = {
                'exception_type': type(e).__name__,
                'error_message': str(e),
                'thread': 'processing_worker'
            }
            log_error_details('PROCESSING_ERROR', str(e), error_context)
            logging.error(f"Critical error in processing thread: {e}", exc_info=True)
            self.after(0, self.on_processing_complete, {"message": f"Critical error: {e}"})

    def on_processing_complete(self, result):
        self.set_gui_state(processing=False)
        
        base_message = result.get("message", "Processing completed without a message.")
        time_taken = result.get("time_taken")
        processed_count = result.get("processed_count", 0)
        skipped_count = result.get("skipped_count", 0)

        final_message = f"{base_message}\n\n"
        final_message += f"- New files processed: {processed_count}\n"
        final_message += f"- Files skipped: {skipped_count}\n"
        if time_taken is not None:
            final_message += f"- Execution time: {time_taken:.2f} seconds."

        if self.email_enabled_var.get():
            subject = f"[TDR Processor] Processing Complete - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            try:
                port = int(self.smtp_port_var.get())
                # Get credentials from secure storage first, fallback to session vars
                creds = get_smtp_credentials()
                if creds:
                    smtp_user, smtp_pass = creds
                else:
                    # Fallback to session-only credentials
                    smtp_user = self.smtp_user_var.get()
                    smtp_pass = self.smtp_pass_var.get()
                
                if smtp_user and smtp_pass:
                    send_notification_email(
                        smtp_server=self.smtp_server_var.get(),
                        smtp_port=port,
                        smtp_user=smtp_user,
                        smtp_pass=smtp_pass,
                        recipient_email=self.recipient_email_var.get(),
                        subject=subject,
                        body=final_message
                    )
                else:
                    logging.warning("[Email] SMTP credentials not configured. Email not sent.")
            except ValueError:
                logging.error("[Email] Cổng SMTP không hợp lệ. Phải là một số.")
            except Exception as e:
                logging.error(f"[Email] Lỗi không xác định khi cố gắng gửi email: {e}")
        
        if "error" in base_message.lower() or "no data" in base_message.lower():
            self.status_label.config(text=f"⚠️ Completed with warnings", bootstyle=WARNING)
            messagebox.showwarning("Processing Result", final_message)
        else:
            self.status_label.config(text="✅ Processing successful", bootstyle=SUCCESS)
            messagebox.showinfo("Complete", final_message)
            if messagebox.askyesno("Open Folder", "Would you like to open the output folder?"):
                self.open_output_folder()

    def open_output_folder(self):
        output_path = self.output_dir / "outputs"
        if output_path.exists():
            os.startfile(output_path)
        else:
            # Fallback to data_excel if outputs doesn't exist for some reason
            excel_dir = self.output_dir / "data_excel"
            if excel_dir.exists():
                os.startfile(excel_dir)
            else:
                messagebox.showerror("Error", f"Folder does not exist: {output_path}")

    def set_gui_state(self, processing: bool):
        state = tk.DISABLED if processing else tk.NORMAL
        self.process_button.config(state=state)
        self.auto_mode_check.config(state=state)
        self.overwrite_check.config(state=state)
        self.settings_button.config(state=state)
        self.open_folder_button.config(state=tk.NORMAL)
        
        if processing:
            self.status_label.config(text="🔄 Processing...", bootstyle=INFO)
            self.progress_bar['value'] = 0
            self.progress_label.config(text="0%")
        else:
            self.progress_bar['value'] = 0
            self.progress_label.config(text="0%")
            if not self.auto_mode_var.get():
                self.status_label.config(text="✅ Ready (Auto-mode OFF).", bootstyle=SUCCESS)

    def update_status(self, text: str):
        self.status_label.config(text=f"🔄 {text}")

    def update_progress(self, current, total):
        if total > 0:
            percentage = (current / total) * 100
            self.progress_bar['value'] = percentage
            self.progress_label.config(text=f"{int(percentage)}%")
        else:
            self.progress_bar['value'] = 0
            self.progress_label.config(text="0%")

    def on_closing(self):
        """Hàm được gọi khi người dùng nhấn nút X để đóng cửa sổ."""
        if self.processor_thread and self.processor_thread.is_alive():
            if not messagebox.askyesno("Exit", "A process is running. Are you sure you want to exit?"):
                return
        
        self.save_settings()
        if self.watcher:
            self.watcher.stop()
        if self.scheduler:
            self.scheduler.stop()
            
        self.destroy()

if __name__ == "__main__":
    # Đảm bảo các thư mục cần thiết tồn tại trước khi khởi tạo App
    if setup_project_directories(Path.cwd(), REQUIRED_DIRS):
        app = App()
        app.mainloop()