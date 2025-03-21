import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
import os
import shutil
from datetime import datetime
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
import threading
from queue import Queue
import hashlib

def calculate_md5(file_path):
    """计算文件的MD5值"""
    with open(file_path, 'rb') as f:
        md5_hash = hashlib.md5()
        while chunk := f.read(8192):
            md5_hash.update(chunk)
        return md5_hash.hexdigest()

class PhotoOrganizer:
    def __init__(self, root):
        self.root = root
        self.root.title('照片和视频整理工具')
        self.root.geometry('700x400')
        
        # 创建队列用于线程间通信
        self.progress_queue = Queue()
        
        # 设置ttk风格
        style = ttk.Style()
        style.theme_use('vista')
        style.configure('TButton', padding=6)
        style.configure('TEntry', padding=6)
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0')
        style.configure('Horizontal.TProgressbar', thickness=15)
        
        # 主容器
        main_frame = ttk.Frame(root, padding="20 20 20 20")
        main_frame.pack(fill='both', expand=True)
        
        # 源文件夹选择
        self.source_frame = ttk.Frame(main_frame)
        self.source_frame.pack(fill='x', pady=(0, 15))
        
        self.source_label = ttk.Label(self.source_frame, text='源文件夹：', width=10)
        self.source_label.pack(side='left', anchor='e')
        
        # 创建一个容器来限制Entry的宽度
        entry_container = ttk.Frame(self.source_frame)
        entry_container.pack(side='left', padx=(5, 10), fill='x', expand=True)
        
        self.source_entry = ttk.Entry(entry_container)
        self.source_entry.pack(fill='both', expand=True, pady=2)
        
        self.source_button = ttk.Button(self.source_frame, text='选择文件夹', command=self.select_source, width=20)
        self.source_button.pack(side='left')
        
        # 目标文件夹选择
        self.target_frame = ttk.Frame(main_frame)
        self.target_frame.pack(fill='x', pady=(0, 15))
        
        self.target_label = ttk.Label(self.target_frame, text='目标文件夹：', width=10)
        self.target_label.pack(side='left', anchor='e')
        
        # 创建一个容器来限制Entry的宽度
        target_entry_container = ttk.Frame(self.target_frame)
        target_entry_container.pack(side='left', padx=(5, 10), fill='x', expand=True)
        
        self.target_entry = ttk.Entry(target_entry_container)
        self.target_entry.pack(fill='both', expand=True, pady=2)
        
        self.target_button = ttk.Button(self.target_frame, text='选择文件夹', command=self.select_target, width=20)
        self.target_button.pack(side='left')
        
        # 进度条
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(fill='x', pady=(0, 20))
        
        self.progress_label = ttk.Label(self.progress_frame, text='处理进度：', width=10)
        self.progress_label.pack(side='left', anchor='e')
        
        # 创建一个容器来包装进度条和文本
        progress_container = ttk.Frame(self.progress_frame)
        progress_container.pack(side='left', padx=(5, 10), fill='x', expand=True, ipadx=155)
        
        # 添加进度条，使其填充容器
        self.progress_bar = ttk.Progressbar(progress_container, mode='determinate', style='Horizontal.TProgressbar')
        self.progress_bar.pack(fill='x', expand=True)
        
        # 当前处理文件显示
        self.progress_text = ttk.Label(self.progress_frame, text='0/0')
        self.progress_text.pack(side='left', padx=(5, 10))

        # 添加文件名显示标签
        self.current_file_label = ttk.Label(self.progress_frame, text='', width=50)
        self.current_file_label.pack(side='left', padx=(0, 0))
        
        # 按钮框架
        self.button_frame = ttk.Frame(main_frame)
        self.button_frame.pack()
        
        # 整理按钮
        self.organize_button = ttk.Button(self.button_frame, text='开始整理', command=self.organize_photos, style='TButton')
        self.organize_button.pack(side='left', padx=(0, 10))
        
        # 停止按钮
        self.stop_button = ttk.Button(self.button_frame, text='停止整理', command=self.stop_organize, state='disabled', style='TButton')
        self.stop_button.pack(side='left')
        
        # 添加停止标志
        self.stop_flag = False
        self.invalid_files = []  # 用于记录不符合规则的文件路径
        # 添加照片和视频计数器
        self.photo_count = 0
        self.video_count = 0
        self.skipped_count = 0  # 添加跳过文件计数器
        # 添加工作线程
        self.worker_thread = None

    def select_source(self):
        """选择源文件夹"""
        folder = filedialog.askdirectory()
        if folder:
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, folder)

    def select_target(self):
        """选择目标文件夹"""
        folder = filedialog.askdirectory()
        if folder:
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, folder)

    def toggle_buttons(self, state):
        """控制按钮状态"""
        self.source_button['state'] = state
        self.target_button['state'] = state
        self.organize_button['state'] = state
        # 停止按钮状态相反
        self.stop_button['state'] = 'normal' if state == 'disabled' else 'disabled'

    def stop_organize(self):
        """停止整理"""
        self.stop_flag = True

    def process_files(self, source_dir, target_dir, files_to_process, total_files):
        """在工作线程中处理文件"""
        processed_files = 0

        for root, file in files_to_process:
            if self.stop_flag:
                self.progress_queue.put(('stop', None))
                return

            file_path = os.path.join(root, file)
            file_type = '视频' if file.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv')) else '照片'
            # 发送当前处理的文件信息
            self.progress_queue.put(('progress', (processed_files, total_files, file)))
            self.root.after_idle(self.process_queue_message)
            
            try:
                date_folder = 'UnknownDate'
                if file_type == '照片':
                    with Image.open(file_path) as img:
                        exif = img._getexif()
                        if exif is not None:
                            date_str = exif.get(36867)  # 获取拍摄日期
                            if date_str:
                                date = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                                date_folder = date.strftime('%Y.%m.%d')
                else:  # 视频文件
                    parser = createParser(file_path)
                    if parser:
                        try:
                            metadata = extractMetadata(parser)
                            if metadata and metadata.has('creation_date'):
                                date = metadata.get('creation_date')
                                date_folder = date.strftime('%Y.%m.%d')
                        finally:
                            parser.close()
                
                if date_folder == 'UnknownDate':
                    date_folder = datetime.fromtimestamp(
                        os.path.getmtime(file_path)
                    ).strftime('%Y.%m.%d')
            except Exception:
                date_folder = 'UnknownDate'

            new_folder = os.path.join(target_dir, date_folder)
            os.makedirs(new_folder, exist_ok=True)

            new_file_path = os.path.join(new_folder, file)
            base_name, ext = os.path.splitext(file)
            counter = 1
            
            # 计算源文件的MD5值
            source_md5 = calculate_md5(file_path)
            target_md5 = None
            while os.path.exists(new_file_path):
                # 只在第一次或文件路径改变时计算目标文件的MD5值
                if target_md5 is None:
                    target_md5 = calculate_md5(new_file_path)
                
                # 如果MD5值相同，说明是相同文件，跳过复制
                if source_md5 == target_md5:
                    self.skipped_count += 1
                    break
                    
                # MD5值不同，继续查找新的文件名
                new_file_name = f"{base_name}_{counter}{ext}"
                new_file_path = os.path.join(new_folder, new_file_name)
                counter += 1
                target_md5 = None  # 重置target_md5，因为文件路径已改变

            # 如果文件不存在，或存在但MD5值不同，则复制文件
            if not os.path.exists(new_file_path) or (target_md5 is not None and source_md5 != target_md5):
                # 使用shutil.copy2复制文件并保留元数据
                shutil.copy2(file_path, new_file_path)
            
            if file_type == '视频':
                self.video_count += 1
            else:
                self.photo_count += 1
            
            processed_files += 1

        # 发送完成信息
        self.progress_queue.put(('complete', (self.photo_count, self.video_count, self.skipped_count)))

    def truncate_filename(self, filename, max_length=35):
        """截断文件名，保留开头和结尾，中间用...代替"""
        if len(filename) <= max_length:
            return filename
        head_len = 5
        tail_len = 4
        return f"{filename[:head_len]}...{filename[-tail_len:]}"

    def process_queue_message(self):
        """处理队列消息并更新UI"""
        try:
            msg_type, data = self.progress_queue.get_nowait()
            
            if msg_type == 'progress':
                processed_files, total_files, current_file = data
                self.progress_bar['value'] = processed_files
                self.progress_text.config(text=f'{processed_files}/{total_files}')
                truncated_filename = self.truncate_filename(current_file, 15)
                self.current_file_label.config(text=f'{truncated_filename}')
            elif msg_type == 'complete':
                photo_count, video_count, skipped_count = data
                self.current_file_label.config(text='')
                total_processed = photo_count + video_count
                if self.invalid_files:
                    log_file = os.path.join(self.target_entry.get(), datetime.now().strftime('%Y%m%d_%H%M%S.log'))
                    with open(log_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(self.invalid_files))
                    messagebox.showinfo('完成', f'处理完成！\n共处理 {total_processed + skipped_count + len(self.invalid_files)} 个文件：\n- {photo_count} 张照片\n- {video_count} 个视频文件\n- {skipped_count} 个相同文件（已跳过）\n- {len(self.invalid_files)} 个不符合规则的文件（已记录到日志）')
                else:
                    messagebox.showinfo('成功', f'处理完成！\n共处理 {total_processed + skipped_count} 个文件：\n- {photo_count} 张照片\n- {video_count} 个视频文件\n- {skipped_count} 个相同文件（已跳过）')
                self.cleanup()
            elif msg_type == 'stop':
                self.cleanup()
                return
            elif msg_type == 'error':
                messagebox.showerror('错误', f'整理过程中出现错误：{data}')
                self.cleanup()
                return

            # 如果队列中还有消息，继续处理
            if not self.progress_queue.empty():
                self.root.after_idle(self.process_queue_message)
        except:
            # 如果工作线程还在运行，继续监听队列
            if self.worker_thread and self.worker_thread.is_alive():
                self.root.after_idle(self.process_queue_message)

    def cleanup(self):
        """清理资源并重置UI"""
        self.progress_bar['value'] = 0
        self.progress_text.config(text='0/0')
        self.current_file_label.config(text='')
        self.toggle_buttons('normal')

    def organize_photos(self):
        """启动文件处理"""
        self.stop_flag = False
        self.invalid_files = []  # 用于记录不符合规则的文件路径
        self.toggle_buttons('disabled')
        self.photo_count = 0
        self.video_count = 0
        
        source_dir = self.source_entry.get()
        target_dir = self.target_entry.get()

        if not source_dir or not target_dir:
            messagebox.showerror('错误', '请选择源文件夹和目标文件夹')
            self.cleanup()
            return
        if source_dir in target_dir or target_dir in source_dir:
            messagebox.showerror('错误', '源文件夹和目标文件夹不能互相包含')
            self.cleanup()
            return

        try:
            # 预先收集所有需要处理的文件信息
            files_to_process = []
            for root, _, files in os.walk(source_dir):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp','.heic','webp',
                                           '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv')):
                        files_to_process.append((root, file))
                    else:
                        self.invalid_files.append(os.path.join(root, file))
                        

            total_files = len(files_to_process)
            if total_files == 0:
                messagebox.showinfo('提示', '未找到图片或视频文件')
                self.toggle_buttons('normal')
                return

            self.progress_bar['maximum'] = total_files
            
            # 启动工作线程
            self.worker_thread = threading.Thread(
                target=self.process_files,
                args=(source_dir, target_dir, files_to_process, total_files)
            )
            self.worker_thread.daemon = True
            self.worker_thread.start()
            
            # 启动消息处理
            self.root.after_idle(self.process_queue_message)

        except Exception as e:
            self.progress_queue.put(('error', str(e)))


if __name__ == '__main__':
    root = tk.Tk()
    app = PhotoOrganizer(root)
    root.mainloop()