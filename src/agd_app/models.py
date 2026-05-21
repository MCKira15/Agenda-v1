from dataclasses import dataclass
from datetime import datetime
from typing import Optional


STATUS_OPTIONS = ("Pendiente", "Parcial", "Completado", "Finalizado")
SECTION_OPTIONS = ("Universidad", "Personal", "Pendientes", "Extra")


@dataclass
class Course:
    id: int
    name: str
    section: str
    color: str
    notes: str


@dataclass
class Task:
    id: int
    title: str
    section: str
    course_id: Optional[int]
    due_at: Optional[str]
    status: str
    progress: int
    description: str
    image_path: str
    created_at: str
    completed_at: Optional[str]

    @property
    def due_datetime(self) -> Optional[datetime]:
        if not self.due_at:
            return None
        try:
            return datetime.fromisoformat(self.due_at)
        except ValueError:
            return None


@dataclass
class Note:
    id: int
    title: str
    section: str
    course_id: Optional[int]
    body: str
    image_path: str
    created_at: str
    updated_at: str


@dataclass
class Event:
    id: int
    title: str
    section: str
    course_id: Optional[int]
    starts_at: str
    ends_at: str
    repeats: str
    notes: str
