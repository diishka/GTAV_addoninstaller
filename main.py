import os
import sys
import json
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# ------------------- КОНФИГУРАЦИЯ -------------------
# Сохраняем конфиг в домашней папке пользователя, чтобы
# настройки не терялись при упаковке в единый исполняемый файл.
CONFIG_FILE = Path.home() / ".gta5_addon_installer_config.json"

def load_config():
    """Загружает сохранённый путь к игре"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return Path(data.get("game_path", ""))
        except:
            pass
    return None

def save_config(game_path):
    """Сохраняет путь к игре"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump({"game_path": str(game_path)}, f, indent=2)

def validate_game_path(path):
    """Проверяет, что путь указывает на корректную установку GTA V"""
    if not path or not path.exists():
        return False
    required = [
        path / "GTA5.exe",
        path / "update" / "x64" / "dlcpacks",
        path / "update" / "update.rpf"
    ]
    return all(p.exists() for p in required)

# ------------------- ГЛАВНОЕ ПРИЛОЖЕНИЕ -------------------
class GTA5AddonInstaller:
    def __init__(self, master, game_path):
        self.master = master
        self.game_path = game_path
        master.title("GTA V Add-on Installer")
        master.geometry("640x370")
        master.resizable(False, False)

        self.use_mods = tk.BooleanVar(value=True)
        self.source_folder = None

        # Рамка пути к игре
        frame_path = tk.Frame(master)
        frame_path.pack(fill='x', padx=10, pady=8)

        tk.Label(frame_path, text="Путь к GTA V:").pack(side='left')
        self.lbl_game_path = tk.Label(frame_path, text=str(game_path), fg="#0066cc", anchor='w')
        self.lbl_game_path.pack(side='left', padx=5, fill='x', expand=True)
        self.btn_change_path = tk.Button(frame_path, text="Изменить", command=self.change_game_path)
        self.btn_change_path.pack(side='right')

        # Рамка выбора аддона
        frame_addon = tk.Frame(master)
        frame_addon.pack(fill='x', padx=10, pady=5)

        tk.Label(frame_addon, text="1. Выберите папку с аддоном (содержит dlc.rpf):").pack(anchor='w')
        self.btn_select = tk.Button(frame_addon, text="Выбрать папку", command=self.select_folder, width=20)
        self.btn_select.pack(pady=5)

        self.lbl_status = tk.Label(master, text="", fg="blue")
        self.lbl_status.pack(pady=5)

        # Чекбокс mods
        self.cb_mods = tk.Checkbutton(master, text="2. Использовать папку mods (рекомендуется)",
                                      variable=self.use_mods)
        self.cb_mods.pack(pady=5)

        # Прогресс
        self.progress = ttk.Progressbar(master, mode='indeterminate')
        self.progress.pack(pady=10, fill='x', padx=20)

        # Кнопка выхода
        tk.Button(master, text="Выход", command=master.quit, width=15).pack(pady=5)

        # Дополнительная информация
        info = tk.Label(master, text="При установке через mods:\n- Автоматически создаётся копия dlclist.xml\n- Оригинальные файлы игры не изменяются",
                        fg="gray", font=("Arial", 8))
        info.pack(pady=5)

    def change_game_path(self):
        new_path = filedialog.askdirectory(title="Выберите папку с GTA V (где лежит GTA5.exe)")
        if not new_path:
            return
        new_path = Path(new_path)
        if validate_game_path(new_path):
            self.game_path = new_path
            self.lbl_game_path.config(text=str(new_path))
            save_config(new_path)
            messagebox.showinfo("Путь обновлён", f"Новый путь к игре:\n{new_path}")
        else:
            messagebox.showerror("Ошибка", "Выбранная папка не содержит корректную установку GTA V.\n"
                                           "Убедитесь, что там есть GTA5.exe, update/x64/dlcpacks и update/update.rpf")

    def select_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку, содержащую dlc.rpf")
        if not folder:
            return
        self.source_folder = Path(folder)

        dlc_rpf = self.source_folder / "dlc.rpf"
        if not dlc_rpf.exists():
            messagebox.showerror("Ошибка", f"В выбранной папке нет файла dlc.rpf\n{self.source_folder}")
            return

        pack_name = self.source_folder.name
        self.lbl_status.config(text=f"Начинаю установку аддона: {pack_name}")
        self.progress.start()
        self.master.after(100, lambda: self.install_addon(pack_name))

    def install_addon(self, pack_name):
        try:
            if self.use_mods.get():
                # Пути при использовании mods
                dlcpacks_dest = self.game_path / "mods" / "update" / "x64" / "dlcpacks" / pack_name
                dlclist_dest = self.game_path / "mods" / "update" / "update.rpf" / "common" / "data" / "dlclist.xml"
                # Если dlclist.xml нет в mods - копируем из оригинала
                if not dlclist_dest.exists():
                    original_dlclist = self.game_path / "update" / "update.rpf" / "common" / "data" / "dlclist.xml"
                    if not original_dlclist.exists():
                        raise FileNotFoundError("Не найден оригинальный dlclist.xml. Проверьте установку игры.")
                    dlclist_dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(original_dlclist, dlclist_dest)
                    self.lbl_status.config(text="Скопирован оригинальный dlclist.xml в mods")
            else:
                # Прямая установка (рискованно)
                if not messagebox.askyesno("ПРЕДУПРЕЖДЕНИЕ",
                                           "Вы собираетесь изменять оригинальные файлы игры БЕЗ использования mods.\n"
                                           "Это может привести к повреждению игры или проблемам при обновлениях.\n"
                                           "Убедитесь, что у вас есть резервная копия.\n\n"
                                           "Продолжить?"):
                    self.finish(False)
                    return
                dlcpacks_dest = self.game_path / "update" / "x64" / "dlcpacks" / pack_name
                dlclist_dest = self.game_path / "update" / "update.rpf" / "common" / "data" / "dlclist.xml"
                # Проверка прав записи (попытка создать временный файл)
                if not os.access(dlclist_dest.parent, os.W_OK):
                    messagebox.showerror("Ошибка прав", f"Нет прав на запись в папку\n{dlclist_dest.parent}\n"
                                                       "Запустите программу от имени администратора.")
                    self.finish(False)
                    return

            # Копируем папку аддона
            if dlcpacks_dest.exists():
                if not messagebox.askyesno("Перезапись", f"Папка {pack_name} уже существует. Перезаписать?"):
                    self.finish(False)
                    return
                shutil.rmtree(dlcpacks_dest)
            shutil.copytree(self.source_folder, dlcpacks_dest)
            self.lbl_status.config(text=f"Папка {pack_name} скопирована")

            # Обновляем dlclist.xml (текстовый метод)
            self.update_dlclist(dlclist_dest, pack_name)

            messagebox.showinfo("Успех!", f"Аддон '{pack_name}' установлен!\n"
                                          f"Папка: {dlcpacks_dest}\n"
                                          f"Запись добавлена в:\n{dlclist_dest}")
            self.finish(True)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось установить аддон:\n{e}")
            self.finish(False)

    def update_dlclist(self, xml_path, pack_name):
        """
        Добавляет строку <Item>dlcpacks:/pack_name/</Item> внутрь <Paths> перед </Paths>
        Без дублирования. Работает на уровне текста.
        """
        new_line = f'        <Item>dlcpacks:/{pack_name}/</Item>'

        # Если файла нет - создаём базовый (такое может быть, если mods папка пустая)
        if not xml_path.exists():
            base_content = '''<?xml version="1.0" encoding="UTF-8"?>
<SMandatoryPacksData>
    <Paths>
    </Paths>
</SMandatoryPacksData>'''
            xml_path.parent.mkdir(parents=True, exist_ok=True)
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(base_content)
            self.lbl_status.config(text="Создан новый dlclist.xml")

        # Читаем файл
        with open(xml_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Ищем строку с </Paths>
        insert_index = -1
        for i, line in enumerate(lines):
            if '</Paths>' in line:
                insert_index = i
                break

        if insert_index == -1:
            raise ValueError("Не найден закрывающий тег </Paths> в файле dlclist.xml")

        # Проверяем наличие такой же записи (нормализуем пробелы)
        normalized_new = new_line.strip()
        already_exists = False
        for line in lines:
            if line.strip() == normalized_new:
                already_exists = True
                break

        if already_exists:
            self.lbl_status.config(text=f"Запись dlcpacks:/{pack_name}/ уже существует, пропускаем")
            return

        # Вставляем новую строку перед </Paths>
        lines.insert(insert_index, new_line + '\n')

        # Записываем обратно
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        self.lbl_status.config(text=f"Добавлена запись: dlcpacks:/{pack_name}/")

    def finish(self, success):
        self.progress.stop()
        if success:
            self.lbl_status.config(text="Установка завершена успешно!", fg="green")
        else:
            self.lbl_status.config(text="Установка не выполнена", fg="red")
        self.btn_select.config(state="normal")

# ------------------- ЗАПУСК -------------------
def main():
    root = tk.Tk()
    root.withdraw()  # скрываем пустой корневой диалог

    # Загружаем или запрашиваем путь к игре
    game_path = load_config()
    if game_path is None or not validate_game_path(game_path):
        messagebox.showinfo("Настройка", "Укажите папку с установленной игрой GTA V (где лежит GTA5.exe)")
        initial_dir = Path("D:/Games/Grand Theft Auto V") if Path("D:/Games/Grand Theft Auto V").exists() else Path.home()
        chosen = filedialog.askdirectory(title="Папка с GTA V", initialdir=initial_dir)
        if not chosen:
            root.destroy()
            sys.exit(0)
        game_path = Path(chosen)
        if not validate_game_path(game_path):
            messagebox.showerror("Ошибка", "Указанная папка не является корректной установкой GTA V.\nПрограмма будет закрыта.")
            root.destroy()
            sys.exit(1)
        save_config(game_path)

    root.destroy()  # закрываем временное окно

    # Создаём главное окно приложения
    main_root = tk.Tk()
    app = GTA5AddonInstaller(main_root, game_path)
    main_root.mainloop()

if __name__ == "__main__":
    main()
