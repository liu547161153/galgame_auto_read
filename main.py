import tkinter as tk
from tkinter import ttk
import re
import pyperclip
import threading

import pyaudio
import configparser
from voicevox import text_to_voice_with_sentiment


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("语音转换器")
        self.device_indices = {}
        self.pack()
        self.create_widgets()
        self.load_settings()

    def get_audio_device_info(self):
        device_info = {}
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] == 0 and info['maxOutputChannels'] > 0:
                device_name = f"{info['name']} (index {i})"
                device_info[i] = device_name
                self.device_indices[device_name] = i
        return device_info


    def create_widgets(self):

        self.entries = []

        # Title label
        title_label = tk.Label(self, text="请输入要转换语音的人名和Speaker ID：")
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        for i in range(5):  # 根据需要更改人名和Speaker ID输入框的数量
            # Name Label
            name_label = tk.Label(self)
            name_label["text"] = f"人名{i + 1}："
            name_label.grid(row=i + 1, column=0, sticky="e")

            # Name Entry
            name_entry = tk.Entry(self)
            name_entry.grid(row=i + 1, column=1)

            # Speaker ID Label
            speaker_id_label = tk.Label(self)
            speaker_id_label["text"] = f"Speaker ID{i + 1}："
            speaker_id_label.grid(row=i + 1, column=2, padx=(10, 0), sticky="e")

            # Speaker ID Entry
            speaker_id_entry = tk.Entry(self)
            speaker_id_entry.grid(row=i + 1, column=3)

            self.entries.append((name_entry, speaker_id_entry))

        last_entry_row = len(self.entries) + 1

        # Narration Label
        narration_label = tk.Label(self)
        narration_label["text"] = "旁白："
        narration_label.grid(row=last_entry_row, column=0, sticky="e")

        # Narration Entry
        self.narration_entry = tk.Entry(self)
        self.narration_entry.grid(row=last_entry_row, column=1)

        # Add padding for better layout
        for i in range(4):
            self.grid_columnconfigure(i, weight=1, pad=10)

        last_row = last_entry_row + 1

        # Button
        self.convert_button = tk.Button(self)
        self.convert_button["text"] = "确定"
        self.convert_button["command"] = self.start_monitor_clipboard
        self.convert_button.grid(row=last_row, column=0, columnspan=2, pady=(10, 0))

        # Cancel Button
        self.cancel_button = tk.Button(self)
        self.cancel_button["text"] = "取消"
        self.cancel_button["state"] = "disabled"
        self.cancel_button["command"] = self.stop_monitor_clipboard
        self.cancel_button.grid(row=last_row, column=2, columnspan=2, pady=(10, 0))

        # Audio Channel Label
        audio_channel_label = tk.Label(self)
        audio_channel_label["text"] = "音频通道："
        audio_channel_label.grid(row=last_row + 1, column=0, sticky="e")

        # Audio Channel Combobox
        device_info = self.get_audio_device_info()
        self.audio_channel_combobox = ttk.Combobox(self, values=list(device_info.values()))
        self.audio_channel_combobox.grid(row=last_row + 1, column=1)

        # Quit Button
        self.quit = tk.Button(self, text="保存设定并退出", fg="red",
                              command=self.save_settings_and_quit)
        self.quit.grid(row=last_row + 1, column=2, sticky="e", pady=(10, 0))

    def load_settings(self):
        # 读取 INI 文件并将用户设置加载回输入框中
        config = configparser.ConfigParser()
        config.read('settings.ini', encoding='utf-8')
        if 'Settings' in config:
            for i, (name_entry, speaker_id_entry) in enumerate(self.entries):
                name_key = f'name_{i}'
                speaker_id_key = f'speaker_id_{i}'
                if name_key in config['Settings'] and speaker_id_key in config['Settings']:
                    name_entry.insert(0, config['Settings'][name_key])
                    speaker_id_entry.insert(0, config['Settings'][speaker_id_key])
            if 'narration' in config['Settings']:
                self.narration_entry.insert(0, config['Settings']['narration'])

    def save_settings_and_quit(self):
        # 将用户设置保存到 INI 文件中，并退出程序
        config = configparser.ConfigParser()
        config['Settings'] = {}

        for i, (name_entry, speaker_id_entry) in enumerate(self.entries):
            config['Settings'][f'name_{i}'] = name_entry.get()
            config['Settings'][f'speaker_id_{i}'] = speaker_id_entry.get()

        config['Settings']['narration'] = self.narration_entry.get()

        with open('settings.ini', 'w', encoding='utf-8') as config_file:
            config.write(config_file)
        self.master.destroy()




    def extract_name_and_text(self, text):
        # 匹配人名和内容的正则表达式
        pattern = r"^(.+?)「(.+?)」$"
        match = re.match(pattern, text)
        if match:
            return match.group(1), match.group(2)
        else:
            return None, text

    def start_monitor_clipboard(self):
        # 提取要转换语音的人名列表和Speaker ID
        self.target_names = {}
        for name_entry, speaker_id_entry in self.entries:
            name = name_entry.get().strip()
            speaker_id = speaker_id_entry.get().strip()
            if name and speaker_id:
                try:
                    speaker_id = int(speaker_id)
                    self.target_names[name] = speaker_id
                except ValueError:
                    pass

        # 锁定输入框和“确定”按钮，启用“取消”按钮
        for name_entry, speaker_id_entry in self.entries:
            name_entry["state"] = "disabled"
            speaker_id_entry["state"] = "disabled"
        self.narration_entry["state"] = "disabled"
        self.convert_button["state"] = "disabled"
        self.cancel_button["state"] = "normal"

        # 创建新线程监视剪贴板内容
        self.clipboard_thread = threading.Thread(target=self.monitor_clipboard)
        self.clipboard_thread.start()

    def stop_monitor_clipboard(self):
        # 停止监视剪贴板内容的线程，解锁输入框
        self.monitoring = False
        for name_entry, speaker_id_entry in self.entries:
            name_entry["state"] = "normal"
            speaker_id_entry["state"] = "normal"
        self.narration_entry["state"] = "normal"
        self.convert_button["state"] = "normal"
        self.cancel_button["state"] = "disabled"

    def monitor_clipboard(self):
        self.monitoring = True
        previous_clipboard_text = pyperclip.paste()
        while self.monitoring:
            clipboard_text = pyperclip.paste()
            if clipboard_text != previous_clipboard_text:
                name, text = self.extract_name_and_text(clipboard_text)
                if name is None or name in self.target_names:
                    speaker = self.target_names.get(name, int(self.narration_entry.get()))
                    device_name = self.audio_channel_combobox.get()
                    cab_d = self.device_indices.get(device_name, 0)
                    threading.Thread(target=text_to_voice_with_sentiment, args=(text, speaker, cab_d)).start()
                previous_clipboard_text = clipboard_text

if __name__ == '__main__':
        root = tk.Tk()

        app = Application(master=root)
        app.mainloop()
