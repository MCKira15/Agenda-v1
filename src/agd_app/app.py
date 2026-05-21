from __future__ import annotations

import calendar
import os
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import filedialog, messagebox, ttk

from .db import Database
from .models import SECTION_OPTIONS, STATUS_OPTIONS, Course, Event, Note, Task


DATE_FORMAT = "%Y-%m-%d %H:%M"
COLORS = {
    "bg": "#f8fafc",
    "panel": "#ffffff",
    "ink": "#0f172a",
    "muted": "#64748b",
    "line": "#dbe3ef",
    "blue": "#2563eb",
    "teal": "#0f766e",
    "amber": "#d97706",
    "red": "#dc2626",
    "green": "#16a34a",
}


class AgendaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.title("Agenda Universitaria y Personal")
        self.geometry("1220x760")
        self.minsize(980, 640)
        self.configure(bg=COLORS["bg"])
        self.selected_month = date.today().replace(day=1)
        self.task_filter = tk.StringVar(value="Todas")
        self.section_filter = tk.StringVar(value="Todas")
        self.search_filter = tk.StringVar(value="")
        self._configure_style()
        self._build_shell()
        self.refresh_all()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _configure_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), background=COLORS["bg"], foreground=COLORS["ink"])
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("Panel.TFrame", background=COLORS["panel"])
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["ink"])
        style.configure("Muted.TLabel", background=COLORS["bg"], foreground=COLORS["muted"])
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 18), background=COLORS["bg"])
        style.configure("CardTitle.TLabel", font=("Segoe UI Semibold", 11), background=COLORS["panel"])
        style.configure("Panel.TLabel", background=COLORS["panel"])
        style.configure("TButton", padding=(10, 6))
        style.configure("Accent.TButton", background=COLORS["blue"], foreground="#ffffff")
        style.configure("Treeview", rowheight=30, fieldbackground="#ffffff", background="#ffffff")
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 10))
        style.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", COLORS["ink"])])
        style.configure("TNotebook", background=COLORS["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", padding=(14, 8))

    def _build_shell(self):
        header = ttk.Frame(self, padding=(18, 14, 18, 6))
        header.pack(fill="x")
        ttk.Label(header, text="Agenda universitaria y personal", style="Title.TLabel").pack(side="left")
        ttk.Button(header, text="Actualizar", command=self.refresh_all).pack(side="right")

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=14, pady=12)
        self.dashboard_tab = ttk.Frame(self.tabs, padding=12)
        self.tasks_tab = ttk.Frame(self.tabs, padding=12)
        self.notes_tab = ttk.Frame(self.tabs, padding=12)
        self.courses_tab = ttk.Frame(self.tabs, padding=12)
        self.events_tab = ttk.Frame(self.tabs, padding=12)
        self.analytics_tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(self.dashboard_tab, text="Inicio")
        self.tabs.add(self.tasks_tab, text="Tareas")
        self.tabs.add(self.notes_tab, text="Notas")
        self.tabs.add(self.courses_tab, text="Cursos")
        self.tabs.add(self.events_tab, text="Calendario")
        self.tabs.add(self.analytics_tab, text="Analiticas")

        self._build_dashboard()
        self._build_tasks()
        self._build_notes()
        self._build_courses()
        self._build_events()
        self._build_analytics()

    def panel(self, parent, **pack):
        frame = ttk.Frame(parent, style="Panel.TFrame", padding=12)
        frame.pack(**pack)
        return frame

    def _build_dashboard(self):
        top = ttk.Frame(self.dashboard_tab)
        top.pack(fill="x")
        self.summary_frame = ttk.Frame(top)
        self.summary_frame.pack(side="left", fill="x", expand=True)
        month_nav = ttk.Frame(top)
        month_nav.pack(side="right")
        ttk.Button(month_nav, text="<", width=3, command=lambda: self.move_month(-1)).pack(side="left", padx=2)
        self.month_label = ttk.Label(month_nav, text="", font=("Segoe UI Semibold", 12))
        self.month_label.pack(side="left", padx=10)
        ttk.Button(month_nav, text=">", width=3, command=lambda: self.move_month(1)).pack(side="left", padx=2)

        body = ttk.Frame(self.dashboard_tab)
        body.pack(fill="both", expand=True, pady=(12, 0))
        self.calendar_frame = self.panel(body, side="left", fill="both", expand=True, padx=(0, 10))
        right = ttk.Frame(body)
        right.pack(side="right", fill="both", expand=False)
        self.urgent_frame = self.panel(right, fill="both", expand=True, pady=(0, 10))
        self.timeline_frame = self.panel(right, fill="both", expand=True)

    def _build_tasks(self):
        filters = ttk.Frame(self.tasks_tab)
        filters.pack(fill="x", pady=(0, 10))
        ttk.Label(filters, text="Estado").pack(side="left")
        ttk.Combobox(filters, textvariable=self.task_filter, width=14, state="readonly", values=("Todas",) + STATUS_OPTIONS).pack(side="left", padx=6)
        ttk.Label(filters, text="Seccion").pack(side="left", padx=(12, 0))
        ttk.Combobox(filters, textvariable=self.section_filter, width=14, state="readonly", values=("Todas",) + SECTION_OPTIONS).pack(side="left", padx=6)
        ttk.Label(filters, text="Buscar").pack(side="left", padx=(12, 0))
        search = ttk.Entry(filters, textvariable=self.search_filter, width=28)
        search.pack(side="left", padx=6)
        ttk.Button(filters, text="Filtrar", command=self.refresh_tasks).pack(side="left")
        ttk.Button(filters, text="Nueva tarea", style="Accent.TButton", command=self.open_task_dialog).pack(side="right")

        columns = ("title", "section", "course", "due", "status", "progress", "urgency")
        self.tasks_tree = ttk.Treeview(self.tasks_tab, columns=columns, show="headings")
        for col, text, width in (
            ("title", "Tarea", 250), ("section", "Seccion", 110), ("course", "Curso", 150),
            ("due", "Entrega", 145), ("status", "Estado", 110), ("progress", "%", 60), ("urgency", "Urgencia", 140),
        ):
            self.tasks_tree.heading(col, text=text)
            self.tasks_tree.column(col, width=width, anchor="w")
        self.tasks_tree.pack(fill="both", expand=True)
        self.tasks_tree.bind("<Double-1>", lambda _e: self.edit_selected_task())
        buttons = ttk.Frame(self.tasks_tab)
        buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(buttons, text="Editar", command=self.edit_selected_task).pack(side="left")
        ttk.Button(buttons, text="Eliminar", command=self.delete_selected_task).pack(side="left", padx=6)
        ttk.Button(buttons, text="Marcar finalizada", command=self.finish_selected_task).pack(side="left")

    def _build_notes(self):
        ttk.Button(self.notes_tab, text="Nueva nota", style="Accent.TButton", command=self.open_note_dialog).pack(anchor="e", pady=(0, 10))
        columns = ("title", "section", "course", "updated")
        self.notes_tree = ttk.Treeview(self.notes_tab, columns=columns, show="headings")
        for col, text, width in (("title", "Nota", 300), ("section", "Seccion", 120), ("course", "Curso", 180), ("updated", "Actualizada", 160)):
            self.notes_tree.heading(col, text=text)
            self.notes_tree.column(col, width=width, anchor="w")
        self.notes_tree.pack(fill="both", expand=True)
        self.notes_tree.bind("<Double-1>", lambda _e: self.edit_selected_note())
        buttons = ttk.Frame(self.notes_tab)
        buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(buttons, text="Editar", command=self.edit_selected_note).pack(side="left")
        ttk.Button(buttons, text="Eliminar", command=self.delete_selected_note).pack(side="left", padx=6)

    def _build_courses(self):
        ttk.Button(self.courses_tab, text="Nuevo curso/seccion", style="Accent.TButton", command=self.open_course_dialog).pack(anchor="e", pady=(0, 10))
        columns = ("name", "section", "color", "notes")
        self.courses_tree = ttk.Treeview(self.courses_tab, columns=columns, show="headings")
        for col, text, width in (("name", "Nombre", 260), ("section", "Seccion", 130), ("color", "Color", 90), ("notes", "Notas generales", 420)):
            self.courses_tree.heading(col, text=text)
            self.courses_tree.column(col, width=width, anchor="w")
        self.courses_tree.pack(fill="both", expand=True)
        self.courses_tree.bind("<Double-1>", lambda _e: self.edit_selected_course())
        buttons = ttk.Frame(self.courses_tab)
        buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(buttons, text="Editar", command=self.edit_selected_course).pack(side="left")
        ttk.Button(buttons, text="Eliminar", command=self.delete_selected_course).pack(side="left", padx=6)

    def _build_events(self):
        ttk.Button(self.events_tab, text="Nuevo bloque", style="Accent.TButton", command=self.open_event_dialog).pack(anchor="e", pady=(0, 10))
        self.week_frame = self.panel(self.events_tab, fill="both", expand=True)
        buttons = ttk.Frame(self.events_tab)
        buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(buttons, text="Editar bloque seleccionado", command=self.edit_selected_event).pack(side="left")
        ttk.Button(buttons, text="Eliminar bloque", command=self.delete_selected_event).pack(side="left", padx=6)
        self.selected_event_id = None

    def _build_analytics(self):
        self.analytics_frame = ttk.Frame(self.analytics_tab)
        self.analytics_frame.pack(fill="both", expand=True)

    def refresh_all(self):
        self.courses_cache = self.db.courses()
        self.tasks_cache = self.db.tasks()
        self.notes_cache = self.db.notes()
        self.events_cache = self.db.events()
        self.refresh_dashboard()
        self.refresh_tasks()
        self.refresh_notes()
        self.refresh_courses()
        self.refresh_events()
        self.refresh_analytics()

    def refresh_dashboard(self):
        for widget in self.summary_frame.winfo_children() + self.calendar_frame.winfo_children() + self.urgent_frame.winfo_children() + self.timeline_frame.winfo_children():
            widget.destroy()
        pending = [t for t in self.tasks_cache if t.status not in ("Completado", "Finalizado")]
        done = [t for t in self.tasks_cache if t.status in ("Completado", "Finalizado")]
        overdue = [t for t in pending if t.due_datetime and t.due_datetime < datetime.now()]
        for title, value, color in (
            ("Pendientes", len(pending), COLORS["blue"]),
            ("Vencidas", len(overdue), COLORS["red"]),
            ("Finalizadas", len(done), COLORS["green"]),
            ("Cursos/secciones", len(self.courses_cache), COLORS["teal"]),
        ):
            card = ttk.Frame(self.summary_frame, style="Panel.TFrame", padding=10)
            card.pack(side="left", padx=(0, 8))
            ttk.Label(card, text=str(value), foreground=color, background=COLORS["panel"], font=("Segoe UI Semibold", 20)).pack(anchor="w")
            ttk.Label(card, text=title, style="Panel.TLabel").pack(anchor="w")

        self.month_label.config(text=self.selected_month.strftime("%B %Y").capitalize())
        self.draw_month_calendar()
        self.draw_urgent_list()
        self.draw_today_timeline()

    def draw_month_calendar(self):
        ttk.Label(self.calendar_frame, text="Calendario mensual", style="CardTitle.TLabel").grid(row=0, column=0, columnspan=7, sticky="w", pady=(0, 8))
        for idx, day in enumerate(("Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom")):
            ttk.Label(self.calendar_frame, text=day, style="Panel.TLabel", anchor="center").grid(row=1, column=idx, sticky="ew", padx=2)
            self.calendar_frame.columnconfigure(idx, weight=1)
        month_tasks = [t for t in self.tasks_cache if t.due_datetime and t.due_datetime.date().replace(day=1) == self.selected_month]
        cal = calendar.Calendar(firstweekday=0).monthdatescalendar(self.selected_month.year, self.selected_month.month)
        for r, week in enumerate(cal, start=2):
            self.calendar_frame.rowconfigure(r, weight=1)
            for c, day in enumerate(week):
                frame = tk.Frame(self.calendar_frame, bg="#ffffff", highlightbackground=COLORS["line"], highlightthickness=1)
                frame.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
                color = COLORS["ink"] if day.month == self.selected_month.month else "#94a3b8"
                tk.Label(frame, text=str(day.day), bg="#ffffff", fg=color, font=("Segoe UI Semibold", 9)).pack(anchor="nw", padx=5, pady=3)
                items = [t for t in month_tasks if t.due_datetime and t.due_datetime.date() == day]
                for task in items[:3]:
                    badge = self.urgency_label(task)
                    tk.Label(frame, text=f"{badge} {task.title[:22]}", bg="#eff6ff", fg=COLORS["ink"], anchor="w", font=("Segoe UI", 8)).pack(fill="x", padx=4, pady=1)
                if len(items) > 3:
                    tk.Label(frame, text=f"+{len(items) - 3} mas", bg="#ffffff", fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w", padx=5)

    def draw_urgent_list(self):
        ttk.Label(self.urgent_frame, text="Termometro de urgencia", style="CardTitle.TLabel").pack(anchor="w")
        pending = [t for t in self.tasks_cache if t.status not in ("Completado", "Finalizado")]
        pending.sort(key=lambda task: self.urgency_score(task), reverse=True)
        if not pending:
            ttk.Label(self.urgent_frame, text="No hay tareas pendientes.", style="Panel.TLabel").pack(anchor="w", pady=8)
            return
        for task in pending[:8]:
            color = self.urgency_color(task)
            row = tk.Frame(self.urgent_frame, bg=COLORS["panel"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text=self.urgency_label(task), fg=color, bg=COLORS["panel"], font=("Segoe UI Semibold", 10), width=9, anchor="w").pack(side="left")
            tk.Label(row, text=task.title[:34], bg=COLORS["panel"], fg=COLORS["ink"], anchor="w").pack(side="left", fill="x", expand=True)
            tk.Label(row, text=self.time_left(task), bg=COLORS["panel"], fg=COLORS["muted"]).pack(side="right")

    def draw_today_timeline(self):
        ttk.Label(self.timeline_frame, text="Hoy", style="CardTitle.TLabel").pack(anchor="w")
        today = date.today()
        today_events = [e for e in self.events_cache if self.event_occurs_on(e, today)]
        today_tasks = [t for t in self.tasks_cache if t.due_datetime and t.due_datetime.date() == today]
        if not today_events and not today_tasks:
            ttk.Label(self.timeline_frame, text="Sin bloques ni entregas para hoy.", style="Panel.TLabel").pack(anchor="w", pady=8)
            return
        for text in [self.event_line(e, today) for e in today_events] + [f"Entrega: {t.title} - {t.due_datetime.strftime('%H:%M')}" for t in today_tasks]:
            ttk.Label(self.timeline_frame, text=text, style="Panel.TLabel", wraplength=330).pack(anchor="w", pady=3)

    def move_month(self, delta: int):
        month = self.selected_month.month + delta
        year = self.selected_month.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        self.selected_month = date(year, month, 1)
        self.refresh_dashboard()

    def refresh_tasks(self):
        self.tasks_tree.delete(*self.tasks_tree.get_children())
        course_names = {c.id: c.name for c in self.courses_cache}
        query = self.search_filter.get().strip().lower()
        for task in self.tasks_cache:
            if self.task_filter.get() != "Todas" and task.status != self.task_filter.get():
                continue
            if self.section_filter.get() != "Todas" and task.section != self.section_filter.get():
                continue
            if query and query not in f"{task.title} {task.description}".lower():
                continue
            self.tasks_tree.insert(
                "",
                "end",
                iid=str(task.id),
                values=(
                    task.title,
                    task.section,
                    course_names.get(task.course_id, ""),
                    self.format_dt(task.due_at),
                    task.status,
                    f"{task.progress}%",
                    f"{self.urgency_label(task)} {self.time_left(task)}",
                ),
            )

    def refresh_notes(self):
        self.notes_tree.delete(*self.notes_tree.get_children())
        course_names = {c.id: c.name for c in self.courses_cache}
        for note in self.notes_cache:
            self.notes_tree.insert("", "end", iid=str(note.id), values=(note.title, note.section, course_names.get(note.course_id, ""), self.format_dt(note.updated_at)))

    def refresh_courses(self):
        self.courses_tree.delete(*self.courses_tree.get_children())
        for course in self.courses_cache:
            self.courses_tree.insert("", "end", iid=str(course.id), values=(course.name, course.section, course.color, course.notes[:90]))

    def refresh_events(self):
        for widget in self.week_frame.winfo_children():
            widget.destroy()
        ttk.Label(self.week_frame, text="Vista semanal de bloques de tiempo", style="CardTitle.TLabel").grid(row=0, column=0, columnspan=7, sticky="w", pady=(0, 8))
        start = date.today() - timedelta(days=date.today().weekday())
        for col in range(7):
            day = start + timedelta(days=col)
            day_frame = tk.Frame(self.week_frame, bg="#ffffff", highlightbackground=COLORS["line"], highlightthickness=1, width=150)
            day_frame.grid(row=1, column=col, sticky="nsew", padx=3, pady=3)
            self.week_frame.columnconfigure(col, weight=1)
            self.week_frame.rowconfigure(1, weight=1)
            tk.Label(day_frame, text=day.strftime("%a %d").capitalize(), bg="#ffffff", fg=COLORS["ink"], font=("Segoe UI Semibold", 10)).pack(fill="x", pady=5)
            for event in [e for e in self.events_cache if self.event_occurs_on(e, day)]:
                label = tk.Label(day_frame, text=self.event_line(event, day), bg="#ecfeff", fg=COLORS["ink"], wraplength=130, justify="left", anchor="w", cursor="hand2")
                label.pack(fill="x", padx=5, pady=4)
                label.bind("<Button-1>", lambda _e, event_id=event.id: self.select_event(event_id))

    def refresh_analytics(self):
        for widget in self.analytics_frame.winfo_children():
            widget.destroy()
        done = [t for t in self.tasks_cache if t.completed_at]
        pending = [t for t in self.tasks_cache if not t.completed_at]
        avg_hours = 0
        if done:
            durations = []
            for task in done:
                try:
                    durations.append((datetime.fromisoformat(task.completed_at) - datetime.fromisoformat(task.created_at)).total_seconds() / 3600)
                except (TypeError, ValueError):
                    pass
            avg_hours = sum(durations) / len(durations) if durations else 0
        top = ttk.Frame(self.analytics_frame)
        top.pack(fill="x")
        for title, value in (
            ("Tareas registradas", len(self.tasks_cache)),
            ("Pendientes", len(pending)),
            ("Finalizadas", len(done)),
            ("Promedio para completar", f"{avg_hours:.1f} h"),
        ):
            card = ttk.Frame(top, style="Panel.TFrame", padding=14)
            card.pack(side="left", fill="x", expand=True, padx=(0, 8))
            ttk.Label(card, text=str(value), background=COLORS["panel"], font=("Segoe UI Semibold", 18)).pack(anchor="w")
            ttk.Label(card, text=title, style="Panel.TLabel").pack(anchor="w")
        detail = self.panel(self.analytics_frame, fill="both", expand=True, pady=(12, 0))
        ttk.Label(detail, text="Tiempo de completado por tarea", style="CardTitle.TLabel").pack(anchor="w")
        if not done:
            ttk.Label(detail, text="Todavia no hay tareas finalizadas para analizar.", style="Panel.TLabel").pack(anchor="w", pady=8)
            return
        for task in done[:12]:
            hours = (datetime.fromisoformat(task.completed_at) - datetime.fromisoformat(task.created_at)).total_seconds() / 3600
            ttk.Label(detail, text=f"{task.title}: {hours:.1f} horas desde registro hasta finalizacion", style="Panel.TLabel").pack(anchor="w", pady=2)

    def open_task_dialog(self, task: Task | None = None):
        TaskDialog(self, self.db, self.courses_cache, task, self.refresh_all)

    def edit_selected_task(self):
        selected = self.tasks_tree.selection()
        if selected:
            task = next((t for t in self.tasks_cache if t.id == int(selected[0])), None)
            if task:
                self.open_task_dialog(task)

    def delete_selected_task(self):
        selected = self.tasks_tree.selection()
        if selected and messagebox.askyesno("Eliminar tarea", "Deseas eliminar esta tarea?"):
            self.db.delete_task(int(selected[0]))
            self.refresh_all()

    def finish_selected_task(self):
        selected = self.tasks_tree.selection()
        if not selected:
            return
        task = next((t for t in self.tasks_cache if t.id == int(selected[0])), None)
        if task:
            self.db.update_task(task.id, title=task.title, section=task.section, course_id=task.course_id, due_at=task.due_at, status="Finalizado", progress=100, description=task.description, image_path=task.image_path, completed_at=task.completed_at)
            self.refresh_all()

    def open_note_dialog(self, note: Note | None = None):
        NoteDialog(self, self.db, self.courses_cache, note, self.refresh_all)

    def edit_selected_note(self):
        selected = self.notes_tree.selection()
        if selected:
            note = next((n for n in self.notes_cache if n.id == int(selected[0])), None)
            if note:
                self.open_note_dialog(note)

    def delete_selected_note(self):
        selected = self.notes_tree.selection()
        if selected and messagebox.askyesno("Eliminar nota", "Deseas eliminar esta nota?"):
            self.db.delete_note(int(selected[0]))
            self.refresh_all()

    def open_course_dialog(self, course: Course | None = None):
        CourseDialog(self, self.db, course, self.refresh_all)

    def edit_selected_course(self):
        selected = self.courses_tree.selection()
        if selected:
            course = next((c for c in self.courses_cache if c.id == int(selected[0])), None)
            if course:
                self.open_course_dialog(course)

    def delete_selected_course(self):
        selected = self.courses_tree.selection()
        if selected and messagebox.askyesno("Eliminar curso", "Se eliminara el curso/seccion, no las tareas asociadas. Continuar?"):
            self.db.delete_course(int(selected[0]))
            self.refresh_all()

    def open_event_dialog(self, event: Event | None = None):
        EventDialog(self, self.db, self.courses_cache, event, self.refresh_all)

    def select_event(self, event_id: int):
        self.selected_event_id = event_id
        messagebox.showinfo("Bloque seleccionado", "Bloque seleccionado. Usa editar o eliminar en la parte inferior.")

    def edit_selected_event(self):
        if self.selected_event_id:
            event = next((e for e in self.events_cache if e.id == self.selected_event_id), None)
            if event:
                self.open_event_dialog(event)

    def delete_selected_event(self):
        if self.selected_event_id and messagebox.askyesno("Eliminar bloque", "Deseas eliminar este bloque de calendario?"):
            self.db.delete_event(self.selected_event_id)
            self.selected_event_id = None
            self.refresh_all()

    def urgency_score(self, task: Task) -> int:
        due = task.due_datetime
        if not due:
            return 5
        hours = (due - datetime.now()).total_seconds() / 3600
        if hours < 0:
            return 100
        if hours <= 24:
            return 85
        if hours <= 72:
            return 65
        if hours <= 168:
            return 40
        return 15

    def urgency_label(self, task: Task) -> str:
        score = self.urgency_score(task)
        if score >= 90:
            return "Vencida"
        if score >= 80:
            return "Alta"
        if score >= 60:
            return "Media"
        if score >= 30:
            return "Normal"
        return "Baja"

    def urgency_color(self, task: Task) -> str:
        label = self.urgency_label(task)
        return {"Vencida": COLORS["red"], "Alta": COLORS["red"], "Media": COLORS["amber"], "Normal": COLORS["blue"], "Baja": COLORS["green"]}.get(label, COLORS["muted"])

    def time_left(self, task: Task) -> str:
        due = task.due_datetime
        if not due:
            return "Sin fecha"
        delta = due - datetime.now()
        total_minutes = int(delta.total_seconds() // 60)
        past = total_minutes < 0
        total_minutes = abs(total_minutes)
        days, minutes = divmod(total_minutes, 1440)
        hours = minutes // 60
        text = f"{days}d {hours}h" if days else f"{hours}h"
        return f"Hace {text}" if past else f"Faltan {text}"

    def format_dt(self, value: str | None) -> str:
        if not value:
            return ""
        try:
            return datetime.fromisoformat(value).strftime(DATE_FORMAT)
        except ValueError:
            return value

    def event_occurs_on(self, event: Event, day: date) -> bool:
        start = datetime.fromisoformat(event.starts_at)
        if event.repeats == "Semanal":
            return start.weekday() == day.weekday() and day >= start.date()
        return start.date() == day

    def event_line(self, event: Event, day: date) -> str:
        start = datetime.fromisoformat(event.starts_at)
        end = datetime.fromisoformat(event.ends_at)
        return f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')} {event.title}"

    def on_close(self):
        self.db.close()
        self.destroy()


class BaseDialog(tk.Toplevel):
    def __init__(self, parent, title: str):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=COLORS["bg"])
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)
        self.body = ttk.Frame(self, padding=14)
        self.body.pack(fill="both", expand=True)

    def row(self, label: str, widget, row: int):
        ttk.Label(self.body, text=label).grid(row=row, column=0, sticky="nw", pady=5, padx=(0, 10))
        widget.grid(row=row, column=1, sticky="ew", pady=5)
        self.body.columnconfigure(1, weight=1)

    def text_value(self, widget: tk.Text) -> str:
        return widget.get("1.0", "end").strip()


class TaskDialog(BaseDialog):
    def __init__(self, parent, db: Database, courses: list[Course], task: Task | None, on_save):
        super().__init__(parent, "Editar tarea" if task else "Nueva tarea")
        self.db, self.courses, self.task, self.on_save = db, courses, task, on_save
        self.course_map = {"": None, **{c.name: c.id for c in courses}}
        self.title_var = tk.StringVar(value=task.title if task else "")
        self.section_var = tk.StringVar(value=task.section if task else "Universidad")
        self.course_var = tk.StringVar(value=next((c.name for c in courses if task and c.id == task.course_id), ""))
        self.due_var = tk.StringVar(value=parent.format_dt(task.due_at) if task else "")
        self.status_var = tk.StringVar(value=task.status if task else "Pendiente")
        self.progress_var = tk.IntVar(value=task.progress if task else 0)
        self.image_var = tk.StringVar(value=task.image_path if task else "")
        self._build(task)

    def _build(self, task):
        self.row("Titulo", ttk.Entry(self.body, textvariable=self.title_var), 0)
        self.row("Seccion", ttk.Combobox(self.body, textvariable=self.section_var, values=SECTION_OPTIONS, state="readonly"), 1)
        self.row("Curso", ttk.Combobox(self.body, textvariable=self.course_var, values=list(self.course_map.keys()), state="readonly"), 2)
        self.row("Entrega (YYYY-MM-DD HH:MM)", ttk.Entry(self.body, textvariable=self.due_var), 3)
        self.row("Estado", ttk.Combobox(self.body, textvariable=self.status_var, values=STATUS_OPTIONS, state="readonly"), 4)
        self.row("Avance %", ttk.Scale(self.body, from_=0, to=100, variable=self.progress_var, orient="horizontal"), 5)
        self.desc = tk.Text(self.body, height=7, wrap="word")
        self.desc.insert("1.0", task.description if task else "")
        self.row("Descripcion", self.desc, 6)
        image_row = ttk.Frame(self.body)
        ttk.Entry(image_row, textvariable=self.image_var).pack(side="left", fill="x", expand=True)
        ttk.Button(image_row, text="Adjuntar imagen", command=self.pick_image).pack(side="left", padx=(6, 0))
        self.row("Imagen", image_row, 7)
        buttons = ttk.Frame(self.body)
        buttons.grid(row=8, column=1, sticky="e", pady=(10, 0))
        ttk.Button(buttons, text="Cancelar", command=self.destroy).pack(side="left", padx=5)
        ttk.Button(buttons, text="Guardar", style="Accent.TButton", command=self.save).pack(side="left")

    def pick_image(self):
        path = filedialog.askopenfilename(filetypes=[("Imagenes", "*.png *.jpg *.jpeg *.gif *.bmp"), ("Todos", "*.*")])
        if path:
            self.image_var.set(path)

    def save(self):
        try:
            due = datetime.strptime(self.due_var.get().strip(), DATE_FORMAT).isoformat() if self.due_var.get().strip() else None
        except ValueError:
            messagebox.showerror("Fecha invalida", "Usa el formato YYYY-MM-DD HH:MM, por ejemplo 2026-05-25 18:30.")
            return
        values = {
            "title": self.title_var.get().strip(),
            "section": self.section_var.get(),
            "course_id": self.course_map.get(self.course_var.get()),
            "due_at": due,
            "status": self.status_var.get(),
            "progress": int(float(self.progress_var.get())),
            "description": self.text_value(self.desc),
            "image_path": self.image_var.get().strip(),
            "completed_at": self.task.completed_at if self.task else None,
        }
        if not values["title"]:
            messagebox.showerror("Falta titulo", "Escribe un titulo para la tarea.")
            return
        if self.task:
            self.db.update_task(self.task.id, **values)
        else:
            self.db.add_task(**values)
        self.on_save()
        self.destroy()


class NoteDialog(BaseDialog):
    def __init__(self, parent, db: Database, courses: list[Course], note: Note | None, on_save):
        super().__init__(parent, "Editar nota" if note else "Nueva nota")
        self.db, self.courses, self.note, self.on_save = db, courses, note, on_save
        self.course_map = {"": None, **{c.name: c.id for c in courses}}
        self.title_var = tk.StringVar(value=note.title if note else "")
        self.section_var = tk.StringVar(value=note.section if note else "Universidad")
        self.course_var = tk.StringVar(value=next((c.name for c in courses if note and c.id == note.course_id), ""))
        self.image_var = tk.StringVar(value=note.image_path if note else "")
        self.row("Titulo", ttk.Entry(self.body, textvariable=self.title_var), 0)
        self.row("Seccion", ttk.Combobox(self.body, textvariable=self.section_var, values=SECTION_OPTIONS, state="readonly"), 1)
        self.row("Curso", ttk.Combobox(self.body, textvariable=self.course_var, values=list(self.course_map.keys()), state="readonly"), 2)
        self.body_text = tk.Text(self.body, height=10, wrap="word")
        self.body_text.insert("1.0", note.body if note else "")
        self.row("Nota", self.body_text, 3)
        image_row = ttk.Frame(self.body)
        ttk.Entry(image_row, textvariable=self.image_var).pack(side="left", fill="x", expand=True)
        ttk.Button(image_row, text="Adjuntar imagen", command=self.pick_image).pack(side="left", padx=(6, 0))
        self.row("Imagen", image_row, 4)
        buttons = ttk.Frame(self.body)
        buttons.grid(row=5, column=1, sticky="e", pady=(10, 0))
        ttk.Button(buttons, text="Cancelar", command=self.destroy).pack(side="left", padx=5)
        ttk.Button(buttons, text="Guardar", style="Accent.TButton", command=self.save).pack(side="left")

    def pick_image(self):
        path = filedialog.askopenfilename(filetypes=[("Imagenes", "*.png *.jpg *.jpeg *.gif *.bmp"), ("Todos", "*.*")])
        if path:
            self.image_var.set(path)

    def save(self):
        values = {
            "title": self.title_var.get().strip(),
            "section": self.section_var.get(),
            "course_id": self.course_map.get(self.course_var.get()),
            "body": self.text_value(self.body_text),
            "image_path": self.image_var.get().strip(),
        }
        if not values["title"]:
            messagebox.showerror("Falta titulo", "Escribe un titulo para la nota.")
            return
        if self.note:
            self.db.update_note(self.note.id, **values)
        else:
            self.db.add_note(**values)
        self.on_save()
        self.destroy()


class CourseDialog(BaseDialog):
    def __init__(self, parent, db: Database, course: Course | None, on_save):
        super().__init__(parent, "Editar curso/seccion" if course else "Nuevo curso/seccion")
        self.db, self.course, self.on_save = db, course, on_save
        self.name_var = tk.StringVar(value=course.name if course else "")
        self.section_var = tk.StringVar(value=course.section if course else "Universidad")
        self.color_var = tk.StringVar(value=course.color if course else "#2563eb")
        self.row("Nombre", ttk.Entry(self.body, textvariable=self.name_var), 0)
        self.row("Seccion", ttk.Combobox(self.body, textvariable=self.section_var, values=SECTION_OPTIONS, state="readonly"), 1)
        self.row("Color", ttk.Entry(self.body, textvariable=self.color_var), 2)
        self.notes = tk.Text(self.body, height=8, wrap="word")
        self.notes.insert("1.0", course.notes if course else "")
        self.row("Notas generales", self.notes, 3)
        buttons = ttk.Frame(self.body)
        buttons.grid(row=4, column=1, sticky="e", pady=(10, 0))
        ttk.Button(buttons, text="Cancelar", command=self.destroy).pack(side="left", padx=5)
        ttk.Button(buttons, text="Guardar", style="Accent.TButton", command=self.save).pack(side="left")

    def save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Falta nombre", "Escribe el nombre del curso o seccion.")
            return
        if self.course:
            self.db.update_course(self.course.id, name, self.section_var.get(), self.color_var.get().strip(), self.text_value(self.notes))
        else:
            self.db.add_course(name, self.section_var.get(), self.color_var.get().strip(), self.text_value(self.notes))
        self.on_save()
        self.destroy()


class EventDialog(BaseDialog):
    def __init__(self, parent, db: Database, courses: list[Course], event: Event | None, on_save):
        super().__init__(parent, "Editar bloque" if event else "Nuevo bloque")
        self.db, self.event, self.on_save = db, event, on_save
        self.course_map = {"": None, **{c.name: c.id for c in courses}}
        self.title_var = tk.StringVar(value=event.title if event else "")
        self.section_var = tk.StringVar(value=event.section if event else "Universidad")
        self.course_var = tk.StringVar(value=next((c.name for c in courses if event and c.id == event.course_id), ""))
        self.start_var = tk.StringVar(value=parent.format_dt(event.starts_at) if event else date.today().strftime("%Y-%m-%d") + " 08:00")
        self.end_var = tk.StringVar(value=parent.format_dt(event.ends_at) if event else date.today().strftime("%Y-%m-%d") + " 10:00")
        self.repeats_var = tk.StringVar(value=event.repeats if event else "Una vez")
        self.row("Titulo", ttk.Entry(self.body, textvariable=self.title_var), 0)
        self.row("Seccion", ttk.Combobox(self.body, textvariable=self.section_var, values=SECTION_OPTIONS, state="readonly"), 1)
        self.row("Curso", ttk.Combobox(self.body, textvariable=self.course_var, values=list(self.course_map.keys()), state="readonly"), 2)
        self.row("Inicio", ttk.Entry(self.body, textvariable=self.start_var), 3)
        self.row("Fin", ttk.Entry(self.body, textvariable=self.end_var), 4)
        self.row("Repite", ttk.Combobox(self.body, textvariable=self.repeats_var, values=("Una vez", "Semanal"), state="readonly"), 5)
        self.notes = tk.Text(self.body, height=6, wrap="word")
        self.notes.insert("1.0", event.notes if event else "")
        self.row("Notas", self.notes, 6)
        buttons = ttk.Frame(self.body)
        buttons.grid(row=7, column=1, sticky="e", pady=(10, 0))
        ttk.Button(buttons, text="Cancelar", command=self.destroy).pack(side="left", padx=5)
        ttk.Button(buttons, text="Guardar", style="Accent.TButton", command=self.save).pack(side="left")

    def save(self):
        try:
            start = datetime.strptime(self.start_var.get().strip(), DATE_FORMAT)
            end = datetime.strptime(self.end_var.get().strip(), DATE_FORMAT)
        except ValueError:
            messagebox.showerror("Fecha invalida", "Usa el formato YYYY-MM-DD HH:MM.")
            return
        if end <= start:
            messagebox.showerror("Horario invalido", "La hora de fin debe ser posterior al inicio.")
            return
        values = {
            "title": self.title_var.get().strip(),
            "section": self.section_var.get(),
            "course_id": self.course_map.get(self.course_var.get()),
            "starts_at": start.isoformat(),
            "ends_at": end.isoformat(),
            "repeats": self.repeats_var.get(),
            "notes": self.text_value(self.notes),
        }
        if not values["title"]:
            messagebox.showerror("Falta titulo", "Escribe un titulo para el bloque.")
            return
        if self.event:
            self.db.update_event(self.event.id, **values)
        else:
            self.db.add_event(**values)
        self.on_save()
        self.destroy()
