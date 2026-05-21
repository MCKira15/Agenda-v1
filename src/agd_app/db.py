from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from .models import Course, Event, Note, Task


APP_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = APP_DIR / "data"
DB_PATH = DATA_DIR / "agenda.db"


class Database:
    def __init__(self, path: Path = DB_PATH):
        DATA_DIR.mkdir(exist_ok=True)
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.setup()

    def setup(self):
        self.conn.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                section TEXT NOT NULL DEFAULT 'Universidad',
                color TEXT NOT NULL DEFAULT '#2563eb',
                notes TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                section TEXT NOT NULL,
                course_id INTEGER,
                due_at TEXT,
                status TEXT NOT NULL DEFAULT 'Pendiente',
                progress INTEGER NOT NULL DEFAULT 0,
                description TEXT NOT NULL DEFAULT '',
                image_path TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                section TEXT NOT NULL,
                course_id INTEGER,
                body TEXT NOT NULL DEFAULT '',
                image_path TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                section TEXT NOT NULL,
                course_id INTEGER,
                starts_at TEXT NOT NULL,
                ends_at TEXT NOT NULL,
                repeats TEXT NOT NULL DEFAULT 'Una vez',
                notes TEXT NOT NULL DEFAULT '',
                FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE SET NULL
            );
            """
        )
        self.conn.commit()
        self.seed()

    def seed(self):
        count = self.conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        if count:
            return
        bootcamp_id = self.add_course(
            "Bootcamp Data Science", "Extra", "#0f766e", "Lunes, miercoles y viernes de 7:00 pm a 11:00 pm."
        )
        for day_offset, title in ((0, "Bootcamp Data Science"), (2, "Bootcamp Data Science"), (4, "Bootcamp Data Science")):
            self.add_event(
                title=title,
                section="Extra",
                course_id=bootcamp_id,
                starts_at=f"2026-05-{18 + day_offset:02d}T19:00",
                ends_at=f"2026-05-{18 + day_offset:02d}T23:00",
                repeats="Semanal",
                notes="Bloque fijo del bootcamp.",
            )

    def now(self) -> str:
        return datetime.now().replace(microsecond=0).isoformat()

    def add_course(self, name: str, section: str, color: str, notes: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO courses (name, section, color, notes) VALUES (?, ?, ?, ?)",
            (name, section, color, notes),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def update_course(self, course_id: int, name: str, section: str, color: str, notes: str):
        self.conn.execute(
            "UPDATE courses SET name=?, section=?, color=?, notes=? WHERE id=?",
            (name, section, color, notes, course_id),
        )
        self.conn.commit()

    def delete_course(self, course_id: int):
        self.conn.execute("DELETE FROM courses WHERE id=?", (course_id,))
        self.conn.commit()

    def courses(self) -> list[Course]:
        rows = self.conn.execute("SELECT * FROM courses ORDER BY section, name").fetchall()
        return [Course(**dict(row)) for row in rows]

    def add_task(self, **values) -> int:
        values.setdefault("created_at", self.now())
        cur = self.conn.execute(
            """
            INSERT INTO tasks
            (title, section, course_id, due_at, status, progress, description, image_path, created_at, completed_at)
            VALUES (:title, :section, :course_id, :due_at, :status, :progress, :description, :image_path, :created_at, :completed_at)
            """,
            values,
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def update_task(self, task_id: int, **values):
        if values.get("status") in ("Completado", "Finalizado") and not values.get("completed_at"):
            values["completed_at"] = self.now()
            values["progress"] = 100
        if values.get("status") not in ("Completado", "Finalizado"):
            values["completed_at"] = None
        values["id"] = task_id
        self.conn.execute(
            """
            UPDATE tasks SET
                title=:title, section=:section, course_id=:course_id, due_at=:due_at,
                status=:status, progress=:progress, description=:description,
                image_path=:image_path, completed_at=:completed_at
            WHERE id=:id
            """,
            values,
        )
        self.conn.commit()

    def delete_task(self, task_id: int):
        self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()

    def tasks(self) -> list[Task]:
        rows = self.conn.execute("SELECT * FROM tasks ORDER BY COALESCE(due_at, '9999-12-31'), created_at DESC").fetchall()
        return [Task(**dict(row)) for row in rows]

    def add_note(self, **values) -> int:
        now = self.now()
        values.setdefault("created_at", now)
        values.setdefault("updated_at", now)
        cur = self.conn.execute(
            """
            INSERT INTO notes (title, section, course_id, body, image_path, created_at, updated_at)
            VALUES (:title, :section, :course_id, :body, :image_path, :created_at, :updated_at)
            """,
            values,
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def update_note(self, note_id: int, **values):
        values["updated_at"] = self.now()
        values["id"] = note_id
        self.conn.execute(
            """
            UPDATE notes SET title=:title, section=:section, course_id=:course_id,
                body=:body, image_path=:image_path, updated_at=:updated_at
            WHERE id=:id
            """,
            values,
        )
        self.conn.commit()

    def delete_note(self, note_id: int):
        self.conn.execute("DELETE FROM notes WHERE id=?", (note_id,))
        self.conn.commit()

    def notes(self) -> list[Note]:
        rows = self.conn.execute("SELECT * FROM notes ORDER BY updated_at DESC").fetchall()
        return [Note(**dict(row)) for row in rows]

    def add_event(self, **values) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO events (title, section, course_id, starts_at, ends_at, repeats, notes)
            VALUES (:title, :section, :course_id, :starts_at, :ends_at, :repeats, :notes)
            """,
            values,
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def update_event(self, event_id: int, **values):
        values["id"] = event_id
        self.conn.execute(
            """
            UPDATE events SET title=:title, section=:section, course_id=:course_id,
                starts_at=:starts_at, ends_at=:ends_at, repeats=:repeats, notes=:notes
            WHERE id=:id
            """,
            values,
        )
        self.conn.commit()

    def delete_event(self, event_id: int):
        self.conn.execute("DELETE FROM events WHERE id=?", (event_id,))
        self.conn.commit()

    def events(self) -> list[Event]:
        rows = self.conn.execute("SELECT * FROM events ORDER BY starts_at").fetchall()
        return [Event(**dict(row)) for row in rows]

    def close(self):
        self.conn.close()
