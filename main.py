# main.py
# Переписано с KivyMD на Flet


import os
import json
import datetime
import threading



# os.environ["SSL_CERT_FILE"] = certifi.where()
# os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from pathlib import Path

import flet as ft
#import flet_audio


# === Цвета тем (аналог KivyMD palettes) ===
THEME_COLORS = {
    "Red": ft.Colors.RED,
    "Pink": ft.Colors.PINK,
    "Purple": ft.Colors.PURPLE,
    "DeepPurple": ft.Colors.DEEP_PURPLE,
    "Indigo": ft.Colors.INDIGO,
    "Blue": ft.Colors.BLUE,
    "Teal": ft.Colors.TEAL,
    "Green": ft.Colors.GREEN,
    "LightGreen": ft.Colors.LIGHT_GREEN,
    "Orange": ft.Colors.ORANGE,
    "DeepOrange": ft.Colors.DEEP_ORANGE,
    "Brown": ft.Colors.BROWN,
}


# === Карточка задачи ===
class TaskItem(ft.Container):
    def __init__(self, task_data: dict, app_ref: "TodoApp", is_completed: bool = False):
        super().__init__()
        self.task_data = task_data
        self.app_ref = app_ref
        self.is_completed = is_completed

        # Текст напоминания
        time_str = task_data.get("time", "—")
        if is_completed:
            reminder_text = "—"
        else:
            reminder_text = (
                "Напоминание включено" if task_data.get("reminder_enabled") else "—"
            )

        secondary_text = f"{task_data['date']} · {time_str} · {reminder_text}"

        # Кнопки действий
        action_buttons = []
        if not is_completed:
            action_buttons.extend(
                [
                    ft.IconButton(
                        icon=ft.Icons.EDIT,
                        icon_color=ft.Colors.BLUE,
                        tooltip="Редактировать",
                        on_click=self.edit_clicked,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CHECK,
                        icon_color=ft.Colors.GREEN,
                        tooltip="Завершить",
                        on_click=self.complete_clicked,
                    ),
                ]
            )
        action_buttons.append(
            ft.IconButton(
                icon=ft.Icons.DELETE,
                icon_color=ft.Colors.RED,
                tooltip="Удалить",
                on_click=self.delete_clicked,
            )
        )

        self.content = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(
                    spacing=4,
                    controls=[
                        ft.Text(task_data["title"], weight=ft.FontWeight.BOLD, size=16),
                        ft.Text(secondary_text, size=12, color=ft.Colors.GREY_600),
                    ],
                    expand=True,
                ),
                ft.Row(controls=action_buttons, spacing=0),
            ],
        )
        self.padding = 16
        self.margin = ft.Margin.only(bottom=8)
        self.border_radius = 12
        self.bgcolor = ft.Colors.WHITE
        self.shadow = ft.BoxShadow(
            spread_radius=0,
            blur_radius=4,
            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            offset=ft.Offset(0, 2),
        )

    def edit_clicked(self, e):
        self.app_ref.edit_task(self.task_data)

    def complete_clicked(self, e):
        self.app_ref.move_to_completed(self.task_data)

    def delete_clicked(self, e):
        self.app_ref.confirm_delete(self.task_data, self.is_completed)


# === Диалог создания/редактирования задачи ===
class CreateTaskDialog(ft.Column):
    def __init__(self, page: ft.Page, on_save, original_task: dict = None):
        super().__init__()
        self._page = page
        self.on_save = on_save
        self.original_task = original_task
        self.date_picker = None

        # Поля формы
        self.task_field = ft.TextField(
            label="Название задачи",
            border=ft.InputBorder.OUTLINE,
            value=original_task["title"] if original_task else "",
        )

        # Дата
        default_date = datetime.datetime.now()
        if original_task:
            try:
                # Парсим новый формат dd.mm.yyyy
                date_str = original_task["date"].replace(".", "")
                default_date = datetime.datetime.strptime(date_str, "%d%m%Y")
            except:
                pass

        self.selected_date = default_date
        self.date_text = ft.Text(
            self.selected_date.strftime("%d.%m.%Y"),
            size=14,
        )

        # Время
        default_time = "09:00"
        if original_task and original_task.get("time"):
            default_time = original_task["time"]

        self.time_field = ft.TextField(
            label="Время (чч:мм)",
            border=ft.InputBorder.OUTLINE,
            value=default_time,
            hint_text="Например: 14:30",
            width=150,
        )

        # Переключатель напоминания
        reminder_active = (
            original_task.get("reminder_enabled", False) if original_task else False
        )
        self.reminder_switch = ft.Switch(
            value=reminder_active,
            on_change=self.reminder_changed,
        )
        self.reminder_label = ft.Text(
            "Включено" if reminder_active else "Выключено",
            size=14,
        )

        self.spacing = 16
        self.build_controls()

    def build_controls(self):
        self.controls = [
            self.task_field,
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.CALENDAR_MONTH, size=20),
                                self.date_text,
                            ],
                            spacing=8,
                        ),
                        padding=12,
                        border=ft.Border.all(1, ft.Colors.GREY_400),
                        border_radius=4,
                        on_click=self.show_date_picker,
                        expand=True,
                    ),
                    self.time_field,
                ],
                spacing=16,
            ),
            ft.Divider(),
            ft.Text("Напоминание:", weight=ft.FontWeight.BOLD),
            ft.Row(
                controls=[
                    self.reminder_switch,
                    self.reminder_label,
                ],
                spacing=16,
            ),
            ft.Container(
                content=ft.Text(
                    "Напоминания работают только пока приложение открыто или работает в фоне."
                    
                    "  Рекомендуем внести приложение в список автозагрузки",

                    color=ft.Colors.RED_700,
                    size=12,
                ),
                padding=8,
                bgcolor=ft.Colors.RED_50,
                border_radius=4,
            ),
        ]

    def reminder_changed(self, e):
        self.reminder_label.value = (
            "Включено" if self.reminder_switch.value else "Выключено"
        )
        self._page.update()

    def show_date_picker(self, e):
        if self.date_picker and self.date_picker in self._page.overlay:
            self._page.overlay.remove(self.date_picker)

        self.date_picker = ft.DatePicker(
            first_date=datetime.datetime(2020, 1, 1),
            last_date=datetime.datetime(2030, 12, 31),
            value=self.selected_date,
            on_change=self.date_picker_changed,
        )

        self._page.overlay.append(self.date_picker)
        self._page.update()
        self.date_picker.open = True
        self._page.update()

    def date_picker_changed(self, e):
        """ФИКС: +1 день к DatePicker багу"""
        if self.date_picker and self.date_picker.value:
            # ПРИБАВЛЯЕМ 1 ДЕНЬ к тому что показывает DatePicker
            fixed_date = self.date_picker.value + datetime.timedelta(days=1)

            year = fixed_date.year
            month = fixed_date.month
            day = fixed_date.day

            self.date_text.value = f"{day:02d}.{month:02d}.{year}"
            self.selected_date = datetime.datetime(year, month, day, 12, 0, 0)

        if self.date_picker in self._page.overlay:
            self._page.overlay.remove(self.date_picker)
            self.date_picker = None
        self._page.update()

    def get_task_data(self) -> dict | None:
        title = self.task_field.value.strip()
        if not title:
            return None

        time_str = self.time_field.value.strip()
        try:
            h, m = map(int, time_str.split(":"))
            if not (0 <= h < 24 and 0 <= m < 60):
                raise ValueError
            time_str = f"{h:02d}:{m:02d}"
        except:
            return None

        return {
            "title": title,
            "date": self.date_text.value,  # "15.02.2026"
            "time": time_str,
            "reminder_enabled": self.reminder_switch.value,
        }

        # === Главное приложение ===
class TodoApp(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()
        self._page = page
        self.active_tasks: list[dict] = []
        self.completed_tasks: list[dict] = []
        self.current_view = "active"
        self.pending_reminders: dict[str, float] = {}
        self.reminder_thread: threading.Thread | None = None
        self.reminder_running = False
        self.reminder_audio = None

        # Текущая тема
        self.current_theme = "DeepPurple"

        # Инициализация UI
        self.build()

    def load_sound(self):
        """Инициализация аудио для напоминаний"""
        try:
            sound_path = os.path.join(os.path.dirname(__file__), "reminder.wav")
            if os.path.exists(sound_path):
                # Создаем аудио объект (не добавляем в page, работает независимо)
                ##self.reminder_audio = flet_audio.Audio(
                  ##  src=sound_path,
                   ## autoplay=False,
                   ## volume=1.0,
                #)
                print("🔊 Звук загружен:", sound_path)
            else:
                print("🔊 reminder.wav не найден")
        except Exception as e:
            print("⚠️ Ошибка загрузки звука:", e)

    def play_sound(self):
        """Воспроизведение звука напоминания"""
        if self.reminder_audio and self._page:
            # Определяем async функцию для воспроизведения
            async def play_audio():
                try:
                    await self.reminder_audio.play()
                except Exception as e:
                    print("⚠️ Ошибка воспроизведения:", e)
            
            # запуск через run task
            self._page.run_task(play_audio)

        if not self.reminder_audio or not self._page:
            return


    def build(self):
        # Загрузка данных
        self.load_theme()
        self.load_tasks()
        self.load_sound()

        # Кнопки переключения вкладок
        self.btn_active = ft.Button(
            content="Активные",
            on_click=self.show_active,
            bgcolor=THEME_COLORS[self.current_theme],
            color=ft.Colors.WHITE,
        )
        self.btn_completed = ft.Button(
            content="Завершённые",
            on_click=self.show_completed,
            bgcolor=ft.Colors.GREY_300,
            color=ft.Colors.BLACK,
        )

        # Контейнер для списка задач
        self.tasks_column = ft.Column(
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        # FAB кнопки
        self.fab_add = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            on_click=self.show_add_dialog,
            bgcolor=THEME_COLORS[self.current_theme],
        )
        self.fab_theme = ft.FloatingActionButton(
            icon=ft.Icons.PALETTE,
            on_click=self.show_theme_picker,
            bgcolor=THEME_COLORS[self.current_theme],
        )

        self.expand = True
        self.controls = [
            # Заголовок
            ft.Container(
                content=ft.Row(
                    controls=[ft.Text("Dailys", size=24, weight=ft.FontWeight.BOLD)],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=16,
            ),
            # Вкладки
            ft.Container(
                content=ft.Row(
                    controls=[self.btn_active, self.btn_completed],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=16,
                ),
                padding=ft.Padding.only(bottom=16),
            ),
            # Список задач
            ft.Container(
                content=self.tasks_column,
                expand=True,
                padding=ft.Padding.symmetric(horizontal=16),
            ),
            # Нижняя панель с FAB
            ft.Container(
                content=ft.Row(
                    controls=[self.fab_theme, ft.Container(expand=True), self.fab_add],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=16,
            ),
        ]

        # Обновляем список и запускаем напоминания
        self.update_list()
        self.start_reminder_checker()

    # === Переключение вкладок ===
    def show_active(self, e=None):
        self.current_view = "active"
        self.btn_active.bgcolor = THEME_COLORS[self.current_theme]
        self.btn_active.color = ft.Colors.WHITE
        self.btn_completed.bgcolor = ft.Colors.GREY_300
        self.btn_completed.color = ft.Colors.BLACK
        self.update_list()

    def show_completed(self, e=None):
        self.current_view = "completed"
        self.btn_completed.bgcolor = THEME_COLORS[self.current_theme]
        self.btn_completed.color = ft.Colors.WHITE
        self.btn_active.bgcolor = ft.Colors.GREY_300
        self.btn_active.color = ft.Colors.BLACK
        self.update_list()

    # === Обновление списка задач ===
    def update_list(self):
        self.tasks_column.controls.clear()
        tasks = (
            self.active_tasks if self.current_view == "active" else self.completed_tasks
        )
        is_completed = self.current_view == "completed"

        if not tasks:
            self.tasks_column.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text(
                                "Нет задач"
                                if not is_completed
                                else "Нет завершённых задач",
                                color=ft.Colors.GREY_500,
                                size=16,
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    padding=32,
                )
            )
        else:
            for task in tasks:
                self.tasks_column.controls.append(
                    TaskItem(task, self, is_completed=is_completed)
                )

        if self._page:
            self._page.update()

    # === Диалоги ===
    def show_add_dialog(self, e=None):
        dialog_content = CreateTaskDialog(self._page, self.add_task)

        def close_dialog(e):
            dialog.open = False
            self._page.update()

        def save_task(e):
            task_data = dialog_content.get_task_data()
            if task_data:
                self.add_task(task_data)
                dialog.open = False
                self._page.update()
            else:
                self.show_snackbar("Проверьте название и формат времени (чч:мм)")

        dialog = ft.AlertDialog(
            title=ft.Text("Новая задача"),
            content=ft.Container(content=dialog_content, width=400),
            actions=[
                ft.TextButton(content="Отмена", on_click=close_dialog),
                ft.Button(content="Создать", on_click=save_task),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def edit_task(self, task: dict):
        dialog_content = CreateTaskDialog(self._page, None, original_task=task)

        def close_dialog(e):
            dialog.open = False
            self._page.update()

        def save_changes(e):
            new_data = dialog_content.get_task_data()
            if new_data:
                # Удаляем старое напоминание
                self.cancel_reminder(task)
                # Обновляем данные
                task.update(new_data)
                # Планируем новое напоминание
                if task.get("reminder_enabled"):
                    self.schedule_reminder(task)
                self.update_list()
                self.save_tasks()
                dialog.open = False
                self._page.update()
            else:
                self.show_snackbar("Проверьте название и формат времени (чч:мм)")

        dialog = ft.AlertDialog(
            title=ft.Text("Редактировать задачу"),
            content=ft.Container(content=dialog_content, width=400),
            actions=[
                ft.TextButton(content="Отмена", on_click=close_dialog),
                ft.Button(content="Сохранить", on_click=save_changes),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def confirm_delete(self, task: dict, is_completed: bool):
        def close_dialog(e):
            dialog.open = False
            self._page.update()

        def do_delete(e):
            self.delete_task(task, is_completed)
            dialog.open = False
            self._page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Удалить задачу?"),
            content=ft.Text(f"«{task['title']}» будет удалена."),
            actions=[
                ft.TextButton(content="Отмена", on_click=close_dialog),
                ft.Button(
                    content="Удалить",
                    on_click=do_delete,
                    bgcolor=ft.Colors.RED,
                    color=ft.Colors.WHITE,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    # === Операции с задачами ===
    def add_task(self, task_data: dict):
        self.active_tasks.append(task_data)
        if  task_data.get("reminder_enabled"):
            self.schedule_reminder(task_data)
        self.update_list()
        self.save_tasks()

    def move_to_completed(self, task: dict):
        if task in self.active_tasks:
            self.active_tasks.remove(task)
            self.completed_tasks.append(task)
            self.cancel_reminder(task)
            self.update_list()
            self.save_tasks()

    def delete_task(self, task: dict, is_completed: bool):
        target_list = self.completed_tasks if is_completed else self.active_tasks
        if task in target_list:
            target_list.remove(task)
            if not is_completed:
                self.cancel_reminder(task)
        self.update_list()
        self.save_tasks()

    # === Напоминания ===
    def get_task_id(self, task: dict) -> str:
        try:
            date_str = task['date']
            time_str = task['time']
            dt_str = f"{date_str} {time_str}"
            dt = datetime.datetime.strptime(dt_str, "%d.%m.%Y %H:%M")
            return f"{task['title']}_{int(dt.timestamp())}"
        except:
            return f"{task['title']}_{id(task)}"

    def schedule_reminder(self, task: dict):
        if not task.get("reminder_enabled"):
            return
        try:
            date_str = task['date']
            time_str = task['time']
            dt_str = f"{date_str} {time_str}"
            print(f"⏰ Планирую: {dt_str}")

            # ★★★ НОВЫЙ ФОРМАТ: %d.%m.%Y %H:%M ★★★
            dt = datetime.datetime.strptime(dt_str, "%d.%m.%Y %H:%M")
            print(f"📅 Парсится как: {dt}")

            now = datetime.datetime.now()
            if dt <= now:
                return

            task_id = self.get_task_id(task)
            self.pending_reminders[task_id] = dt.timestamp()
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")

    def cancel_reminder(self, task: dict):
        task_id = self.get_task_id(task)
        self.pending_reminders.pop(task_id, None)

    def start_reminder_checker(self):
        """Запуск фонового потока для проверки напоминаний"""
        self.reminder_running = True

        def checker():
            while self.reminder_running:
                now = datetime.datetime.now().timestamp()
                to_fire = [
                    tid for tid, ts in list(self.pending_reminders.items()) if now >= ts
                ]
                for task_id in to_fire:
                    self.fire_reminder(task_id)
                    self.pending_reminders.pop(task_id, None)
                import time

                time.sleep(2)

        self.reminder_thread = threading.Thread(target=checker, daemon=True)
        self.reminder_thread.start()

    def fire_reminder(self, task_id: str):

        """ Отладка """

        print(
            f"🔥 fire_reminder вызвана для {task_id} из {self._page.overlay} | Thread: {threading.current_thread().name}")



        """Показать напоминание"""

        title = task_id.split("_")[0]
        self.play_sound()
        try:
            from plyer import notification

            notification.notify(
                title="Напоминание",
                message=f"Время выполнить: {title}",
                app_name="My ToDo",
                timeout=10,
            )
        except Exception as e:
            print("Уведомление не поддерживается:", e)

        def show_dialog():
            dialog = ft.AlertDialog(
                title=ft.Row(
                    [
                        ft.Icon(ft.Icons.ALARM, color=ft.Colors.ORANGE),
                        ft.Text(" Напоминание!"),
                    ]
                ),
                content=ft.Text(f"Время выполнить задачу:\n\n{title}"),
                actions=[
                    ft.Button(
                        content="ОК",
                        on_click=lambda e: self._close_reminder_dialog(dialog),
                    ),
                ],
            )
            self._page.overlay.append(dialog)
            dialog.open = True
            self._page.update()

    def _close_reminder_dialog(self, dialog):
        dialog.open = False
        self._page.update()

    # === Выбор темы ===
    def show_theme_picker(self, e=None):
        def close_dialog(e):
            dialog.open = False
            self._page.update()

        def set_theme(color_name):
            self.current_theme = color_name
            self.apply_theme()
            self.save_theme()
            dialog.open = False
            self._page.update()

        # Сетка цветов
        color_grid = ft.Column(spacing=12)
        color_names = list(THEME_COLORS.keys())

        for i in range(0, len(color_names), 3):
            row = ft.Row(spacing=12)
            for j in range(3):
                if i + j < len(color_names):
                    color_name = color_names[i + j]
                    row.controls.append(
                        ft.Button(
                            content=color_name,
                            bgcolor=THEME_COLORS[color_name],
                            color=ft.Colors.WHITE,
                            on_click=lambda e, c=color_name: set_theme(c),
                            expand=True,
                        )
                    )
            color_grid.controls.append(row)

        dialog = ft.AlertDialog(
            title=ft.Text("Выберите основной цвет"),
            content=ft.Container(content=color_grid, width=400),
            actions=[ft.TextButton(content="Закрыть", on_click=close_dialog)],
        )

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def apply_theme(self):
        """Применить текущую тему к элементам UI"""
        color = THEME_COLORS[self.current_theme]
        self.fab_add.bgcolor = color
        self.fab_theme.bgcolor = color

        if self.current_view == "active":
            self.btn_active.bgcolor = color
        else:
            self.btn_completed.bgcolor = color

        self._page.update()

    # === Сохранение/загрузка ===
    def get_tasks_path(self) -> str:
        # Используем домашнюю директорию пользователя
        data_dir = Path.home() / ".todo_flet"
        data_dir.mkdir(exist_ok=True)
        return str(data_dir / "tasks.json")

    def save_tasks(self):
        all_tasks = [{**t, "completed": False} for t in self.active_tasks] + [
            {**t, "completed": True} for t in self.completed_tasks
        ]
        # Добавляем метаданные темы в начало
        full_data = [{"theme_color": self.current_theme}] + all_tasks
        try:
            with open(self.get_tasks_path(), "w", encoding="utf-8") as f:
                json.dump(full_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Ошибка сохранения: {e}")

    def load_tasks(self):
        path = self.get_tasks_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Фильтруем: только словари с 'title'
            tasks = [t for t in data if isinstance(t, dict) and "title" in t]

            self.active_tasks = [t for t in tasks if not t.get("completed", False)]
            self.completed_tasks = [t for t in tasks if t.get("completed", False)]

            # Убираем поле completed из задач
            for t in self.active_tasks + self.completed_tasks:
                t.pop("completed", None)

            # Восстанавливаем напоминания для активных задач
            for task in self.active_tasks:
                if task.get("reminder_enabled"):
                    self.schedule_reminder(task)

        except Exception as e:
            print(f"⚠️ Ошибка загрузки: {e}")
            self.active_tasks = []
            self.completed_tasks = []

    def save_theme(self):
        # Тема сохраняется вместе с задачами
        self.save_tasks()

    def load_theme(self):
        path = self.get_tasks_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if (
                isinstance(data, list)
                and data
                and isinstance(data[0], dict)
                and "theme_color" in data[0]
            ):
                self.current_theme = data[0]["theme_color"]
        except:
            pass

    # === Вспомогательные методы ===
    def show_snackbar(self, message: str):
        snackbar = ft.SnackBar(content=ft.Text(message))
        self._page.overlay.append(snackbar)
        snackbar.open = True
        self._page.update()


# === Точка входа ===
def main(page: ft.Page):
    page.title = "Dailys"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.bgcolor = ft.Colors.GREY_100
    page.window.width = 500
    page.window.height = 700

    app = TodoApp(page)
    page.add(app)


if __name__ == "__main__":
    ft.run(main)
