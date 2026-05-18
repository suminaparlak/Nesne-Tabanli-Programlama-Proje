from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


@dataclass(frozen=True)
class UserSession:
    username: str
    role: str  # "admin" | "doktor" | "hasta"
    doctor_id: Optional[int] = None
    patient_id: Optional[int] = None


def db_path() -> Path:
    return Path(__file__).with_name("randevu.db")


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(db_path())
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")
    return con


def init_db() -> None:
    con = connect()
    try:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              username TEXT PRIMARY KEY,
              password TEXT NOT NULL,
              role TEXT NOT NULL CHECK(role IN ('admin','doktor','hasta')),
              doctor_id INTEGER REFERENCES doctors(id) ON DELETE SET NULL,
              patient_id INTEGER REFERENCES patients(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS doctors (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              specialty TEXT NOT NULL,
              working_hours TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS patients (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              tc TEXT NOT NULL UNIQUE,
              phone TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS appointments (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              doctor_id INTEGER NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
              patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
              appt_date TEXT NOT NULL,
              appt_time TEXT NOT NULL,
              note TEXT NOT NULL DEFAULT '',
              UNIQUE(doctor_id, appt_date, appt_time)
            );
            """
        )
        _migrate_users_table_if_needed(con)
        _ensure_user_columns(con)
        con.commit()
        _seed_if_empty(con)
    finally:
        con.close()


def _seed_if_empty(con: sqlite3.Connection) -> None:
    # Users
    cur = con.execute("SELECT COUNT(*) AS c FROM users;").fetchone()
    if int(cur["c"]) == 0:
        con.executemany(
            "INSERT INTO users(username,password,role,doctor_id,patient_id) VALUES(?,?,?,?,?);",
            [
                ("admin", "admin123", "admin", None, None),
            ],
        )

    # Doctors
    cur = con.execute("SELECT COUNT(*) AS c FROM doctors;").fetchone()
    if int(cur["c"]) == 0:
        # Stored as CSV like "09:00,10:00,11:00,14:00"
        con.executemany(
            "INSERT INTO doctors(name,specialty,working_hours) VALUES(?,?,?);",
            [
                ("Dr. Ayse Yilmaz", "Kardiyoloji", "09:00,10:00,11:00,14:00,15:00"),
                ("Dr. Mehmet Kaya", "Dahiliye", "09:00,10:00,13:00,14:00,16:00"),
            ],
        )
    _ensure_min_doctors(con)

    # Patients
    cur = con.execute("SELECT COUNT(*) AS c FROM patients;").fetchone()
    if int(cur["c"]) == 0:
        con.executemany(
            "INSERT INTO patients(name,tc,phone) VALUES(?,?,?);",
            [
                ("Ali Demir", "12345678901", "05550000001"),
                ("Zeynep Kaya", "10987654321", "05550000002"),
            ],
        )

    _seed_role_accounts(con)
    con.commit()


def _ensure_min_doctors(con: sqlite3.Connection) -> None:
    """Keep demo data rich enough for class presentation."""
    default_doctors = [
        ("Dr. Elif Arslan", "NoroLoji", "09:00,10:00,11:00,13:00,15:00"),
        ("Dr. Burak Sen", "Ortopedi", "09:00,11:00,12:00,14:00,16:00"),
        ("Dr. Seda Akin", "Cildiye", "10:00,11:00,13:00,14:00,15:00"),
    ]
    for name, specialty, hours in default_doctors:
        exists = con.execute("SELECT 1 FROM doctors WHERE name=? LIMIT 1;", (name,)).fetchone()
        if not exists:
            con.execute(
                "INSERT INTO doctors(name,specialty,working_hours) VALUES(?,?,?);",
                (name, specialty, hours),
            )


def authenticate(username: str, password: str) -> Optional[UserSession]:
    con = connect()
    try:
        row = con.execute(
            "SELECT username, role, doctor_id, patient_id FROM users WHERE username=? AND password=?;",
            (username.strip(), password),
        ).fetchone()
        if not row:
            return None
        return UserSession(
            username=row["username"],
            role=row["role"],
            doctor_id=row["doctor_id"],
            patient_id=row["patient_id"],
        )
    finally:
        con.close()


def _migrate_users_table_if_needed(con: sqlite3.Connection) -> None:
    row = con.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users';").fetchone()
    if not row or not row["sql"]:
        return
    sql = row["sql"].lower().replace(" ", "")
    legacy_roles = "check(rolein('admin','personel'))" in sql
    if not legacy_roles:
        return
    con.execute("ALTER TABLE users RENAME TO users_old;")
    con.execute(
        """
        CREATE TABLE users (
          username TEXT PRIMARY KEY,
          password TEXT NOT NULL,
          role TEXT NOT NULL CHECK(role IN ('admin','doktor','hasta')),
          doctor_id INTEGER REFERENCES doctors(id) ON DELETE SET NULL,
          patient_id INTEGER REFERENCES patients(id) ON DELETE SET NULL
        );
        """
    )
    old_rows = con.execute("SELECT username, password, role FROM users_old;").fetchall()
    for r in old_rows:
        mapped = "doktor" if r["role"] == "personel" else r["role"]
        con.execute(
            "INSERT INTO users(username,password,role,doctor_id,patient_id) VALUES(?,?,?,?,?);",
            (r["username"], r["password"], mapped, None, None),
        )
    con.execute("DROP TABLE users_old;")


def _ensure_user_columns(con: sqlite3.Connection) -> None:
    cols = {r["name"] for r in con.execute("PRAGMA table_info(users);").fetchall()}
    if "doctor_id" not in cols:
        con.execute("ALTER TABLE users ADD COLUMN doctor_id INTEGER REFERENCES doctors(id) ON DELETE SET NULL;")
    if "patient_id" not in cols:
        con.execute("ALTER TABLE users ADD COLUMN patient_id INTEGER REFERENCES patients(id) ON DELETE SET NULL;")


def _seed_role_accounts(con: sqlite3.Connection) -> None:
    d = con.execute("SELECT id FROM doctors ORDER BY id LIMIT 1;").fetchone()
    p = con.execute("SELECT id FROM patients ORDER BY id LIMIT 1;").fetchone()
    if d and not con.execute("SELECT 1 FROM users WHERE role='doktor' LIMIT 1;").fetchone():
        con.execute(
            "INSERT OR IGNORE INTO users(username,password,role,doctor_id,patient_id) VALUES(?,?,?,?,?);",
            ("doktor1", "1234", "doktor", int(d["id"]), None),
        )
    if p and not con.execute("SELECT 1 FROM users WHERE role='hasta' LIMIT 1;").fetchone():
        con.execute(
            "INSERT OR IGNORE INTO users(username,password,role,doctor_id,patient_id) VALUES(?,?,?,?,?);",
            ("hasta1", "1234", "hasta", None, int(p["id"])),
        )


def get_doctors() -> list[sqlite3.Row]:
    con = connect()
    try:
        return con.execute("SELECT id, name, specialty FROM doctors ORDER BY name;").fetchall()
    finally:
        con.close()


def get_patients() -> list[sqlite3.Row]:
    con = connect()
    try:
        return con.execute("SELECT id, name, tc FROM patients ORDER BY name;").fetchall()
    finally:
        con.close()


def create_patient(name: str, tc: str, phone: str) -> int:
    con = connect()
    try:
        cur = con.execute(
            "INSERT INTO patients(name,tc,phone) VALUES(?,?,?);",
            (name.strip(), tc.strip(), phone.strip()),
        )
        con.commit()
        return int(cur.lastrowid)
    finally:
        con.close()


def create_user(username: str, password: str, role: str, doctor_id: Optional[int], patient_id: Optional[int]) -> None:
    con = connect()
    try:
        con.execute(
            "INSERT INTO users(username,password,role,doctor_id,patient_id) VALUES(?,?,?,?,?);",
            (username.strip(), password, role, doctor_id, patient_id),
        )
        con.commit()
    finally:
        con.close()


def list_users() -> list[sqlite3.Row]:
    con = connect()
    try:
        return con.execute(
            """
            SELECT u.username, u.role, d.name AS doctor_name, p.name AS patient_name
            FROM users u
            LEFT JOIN doctors d ON d.id = u.doctor_id
            LEFT JOIN patients p ON p.id = u.patient_id
            ORDER BY u.username;
            """
        ).fetchall()
    finally:
        con.close()


def parse_hours(hours_csv: str) -> list[str]:
    return [h.strip() for h in hours_csv.split(",") if h.strip()]


def hours_to_csv(hours: Iterable[str]) -> str:
    cleaned = []
    for h in hours:
        hh = (h or "").strip()
        if hh:
            cleaned.append(hh)
    return ",".join(cleaned)

