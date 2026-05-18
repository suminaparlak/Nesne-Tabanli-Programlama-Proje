from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional


@dataclass(frozen=True)
class UserSession:
    username: str
    role: str  # "admin" | "personel"


def db_path() -> Path:
    return Path(__file__).with_name("depo.db")


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
              role TEXT NOT NULL CHECK(role IN ('admin','personel')),
              full_name TEXT NOT NULL DEFAULT '',
              phone TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS suppliers (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL UNIQUE,
              phone TEXT NOT NULL DEFAULT '',
              email TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS products (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              sku TEXT NOT NULL UNIQUE,
              name TEXT NOT NULL,
              category TEXT NOT NULL DEFAULT '',
              unit TEXT NOT NULL DEFAULT 'adet',
              price REAL NOT NULL DEFAULT 0,
              stock INTEGER NOT NULL DEFAULT 0,
              min_stock INTEGER NOT NULL DEFAULT 0,
              supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS stock_moves (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ts TEXT NOT NULL,
              product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
              move_type TEXT NOT NULL CHECK(move_type IN ('IN','OUT','ADJUST')),
              qty INTEGER NOT NULL,
              unit_price REAL NOT NULL DEFAULT 0,
              note TEXT NOT NULL DEFAULT '',
              username TEXT NOT NULL REFERENCES users(username) ON DELETE RESTRICT
            );

            CREATE INDEX IF NOT EXISTS idx_stock_moves_product_ts ON stock_moves(product_id, ts);
            """
        )
        _ensure_user_columns(con)
        con.commit()
        _seed_if_empty(con)
    finally:
        con.close()


def _seed_if_empty(con: sqlite3.Connection) -> None:
    c = int(con.execute("SELECT COUNT(*) AS c FROM users;").fetchone()["c"])
    if c == 0:
        con.executemany(
            "INSERT INTO users(username,password,role,full_name,phone) VALUES(?,?,?,?,?);",
            [
                ("admin", "admin123", "admin", "Admin", ""),
                ("personel", "1234", "personel", "Personel", ""),
            ],
        )

    sc = int(con.execute("SELECT COUNT(*) AS c FROM suppliers;").fetchone()["c"])
    if sc == 0:
        con.executemany(
            "INSERT INTO suppliers(name,phone,email) VALUES(?,?,?);",
            [
                ("Tekno Tedarik", "05550000001", "info@teknotedarik.local"),
                ("Ofis Market", "05550000002", "iletisim@ofismarket.local"),
            ],
        )

    pc = int(con.execute("SELECT COUNT(*) AS c FROM products;").fetchone()["c"])
    if pc == 0:
        s1 = con.execute("SELECT id FROM suppliers ORDER BY id LIMIT 1;").fetchone()
        s2 = con.execute("SELECT id FROM suppliers ORDER BY id DESC LIMIT 1;").fetchone()
        con.executemany(
            """
            INSERT INTO products(sku,name,category,unit,price,stock,min_stock,supplier_id)
            VALUES(?,?,?,?,?,?,?,?);
            """,
            [
                ("LPT-001", "Laptop", "Elektronik", "adet", 25000.0, 10, 3, int(s1["id"]) if s1 else None),
                ("MOU-010", "Mouse", "Elektronik", "adet", 500.0, 50, 10, int(s1["id"]) if s1 else None),
                ("KAG-500", "A4 Kagit", "Sarf", "paket", 180.0, 25, 5, int(s2["id"]) if s2 else None),
            ],
        )

    con.commit()


def authenticate(username: str, password: str) -> Optional[UserSession]:
    con = connect()
    try:
        row = con.execute(
            "SELECT username, role FROM users WHERE username=? AND password=?;",
            (username.strip(), password),
        ).fetchone()
        if not row:
            return None
        return UserSession(username=row["username"], role=row["role"])
    finally:
        con.close()


def _ensure_user_columns(con: sqlite3.Connection) -> None:
    cols = {r["name"] for r in con.execute("PRAGMA table_info(users);").fetchall()}
    if "full_name" not in cols:
        con.execute("ALTER TABLE users ADD COLUMN full_name TEXT NOT NULL DEFAULT '';")
    if "phone" not in cols:
        con.execute("ALTER TABLE users ADD COLUMN phone TEXT NOT NULL DEFAULT '';")


def list_suppliers() -> list[sqlite3.Row]:
    con = connect()
    try:
        return con.execute("SELECT * FROM suppliers ORDER BY name;").fetchall()
    finally:
        con.close()


def create_supplier(name: str, phone: str, email: str) -> None:
    con = connect()
    try:
        con.execute(
            "INSERT INTO suppliers(name,phone,email) VALUES(?,?,?);",
            (name.strip(), (phone or "").strip(), (email or "").strip()),
        )
        con.commit()
    finally:
        con.close()


def update_supplier(supplier_id: int, name: str, phone: str, email: str) -> None:
    con = connect()
    try:
        con.execute(
            "UPDATE suppliers SET name=?, phone=?, email=? WHERE id=?;",
            (name.strip(), (phone or "").strip(), (email or "").strip(), int(supplier_id)),
        )
        con.commit()
    finally:
        con.close()


def delete_supplier(supplier_id: int) -> None:
    con = connect()
    try:
        con.execute("DELETE FROM suppliers WHERE id=?;", (int(supplier_id),))
        con.commit()
    finally:
        con.close()


def list_products(search: str = "") -> list[sqlite3.Row]:
    q = (search or "").strip().lower()
    con = connect()
    try:
        rows = con.execute(
            """
            SELECT p.*, s.name AS supplier_name
            FROM products p
            LEFT JOIN suppliers s ON s.id = p.supplier_id
            ORDER BY p.id DESC;
            """
        ).fetchall()
        if not q:
            return rows
        filtered: list[sqlite3.Row] = []
        for r in rows:
            blob = f"{r['sku']} {r['name']} {r['category']} {r['supplier_name'] or ''}".lower()
            if q in blob:
                filtered.append(r)
        return filtered
    finally:
        con.close()


def create_product(
    sku: str,
    name: str,
    category: str,
    unit: str,
    price: float,
    stock: int,
    min_stock: int,
    supplier_id: Optional[int],
) -> None:
    con = connect()
    try:
        con.execute(
            """
            INSERT INTO products(sku,name,category,unit,price,stock,min_stock,supplier_id)
            VALUES(?,?,?,?,?,?,?,?);
            """,
            (
                sku.strip(),
                name.strip(),
                (category or "").strip(),
                (unit or "adet").strip(),
                float(price),
                int(stock),
                int(min_stock),
                int(supplier_id) if supplier_id else None,
            ),
        )
        con.commit()
    finally:
        con.close()


def update_product(
    product_id: int,
    sku: str,
    name: str,
    category: str,
    unit: str,
    price: float,
    stock: int,
    min_stock: int,
    supplier_id: Optional[int],
) -> None:
    con = connect()
    try:
        con.execute(
            """
            UPDATE products
            SET sku=?, name=?, category=?, unit=?, price=?, stock=?, min_stock=?, supplier_id=?
            WHERE id=?;
            """,
            (
                sku.strip(),
                name.strip(),
                (category or "").strip(),
                (unit or "adet").strip(),
                float(price),
                int(stock),
                int(min_stock),
                int(supplier_id) if supplier_id else None,
                int(product_id),
            ),
        )
        con.commit()
    finally:
        con.close()


def delete_product(product_id: int) -> None:
    con = connect()
    try:
        con.execute("DELETE FROM products WHERE id=?;", (int(product_id),))
        con.commit()
    finally:
        con.close()


def low_stock_products() -> list[sqlite3.Row]:
    con = connect()
    try:
        return con.execute(
            """
            SELECT p.*, s.name AS supplier_name
            FROM products p
            LEFT JOIN suppliers s ON s.id = p.supplier_id
            WHERE p.stock <= p.min_stock
            ORDER BY (p.min_stock - p.stock) DESC, p.name;
            """
        ).fetchall()
    finally:
        con.close()


def add_stock_move(
    *,
    product_id: int,
    move_type: str,
    qty: int,
    unit_price: float,
    note: str,
    username: str,
) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    con = connect()
    try:
        row = con.execute("SELECT stock FROM products WHERE id=?;", (int(product_id),)).fetchone()
        if not row:
            raise ValueError("Urun bulunamadi.")
        current = int(row["stock"])
        qv = int(qty)
        if qv <= 0:
            raise ValueError("Miktar pozitif olmali.")

        new_stock = current
        if move_type == "IN":
            new_stock = current + qv
        elif move_type == "OUT":
            if qv > current:
                raise ValueError(f"Yetersiz stok. Mevcut: {current}")
            new_stock = current - qv
        elif move_type == "ADJUST":
            new_stock = qv
            qv = new_stock - current
        else:
            raise ValueError("Gecersiz hareket tipi.")

        con.execute("UPDATE products SET stock=? WHERE id=?;", (int(new_stock), int(product_id)))
        con.execute(
            """
            INSERT INTO stock_moves(ts,product_id,move_type,qty,unit_price,note,username)
            VALUES(?,?,?,?,?,?,?);
            """,
            (ts, int(product_id), move_type, int(qv), float(unit_price), (note or "").strip(), username),
        )
        con.commit()
    finally:
        con.close()


def list_stock_moves(limit: int = 200, search: str = "") -> list[sqlite3.Row]:
    q = (search or "").strip().lower()
    con = connect()
    try:
        rows = con.execute(
            """
            SELECT m.id, m.ts, m.move_type, m.qty, m.unit_price, m.note, m.username,
                   p.sku, p.name AS product_name
            FROM stock_moves m
            JOIN products p ON p.id = m.product_id
            ORDER BY m.id DESC
            LIMIT ?;
            """,
            (int(limit),),
        ).fetchall()
        if not q:
            return rows
        filtered: list[sqlite3.Row] = []
        for r in rows:
            blob = f"{r['ts']} {r['move_type']} {r['sku']} {r['product_name']} {r['note']} {r['username']}".lower()
            if q in blob:
                filtered.append(r)
        return filtered
    finally:
        con.close()


def export_moves_to_csv(path: str, rows: Iterable[sqlite3.Row]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "ts", "type", "qty", "unit_price", "sku", "product", "note", "user"])
        for r in rows:
            w.writerow(
                [
                    r["id"],
                    r["ts"],
                    r["move_type"],
                    r["qty"],
                    r["unit_price"],
                    r["sku"],
                    r["product_name"],
                    r["note"],
                    r["username"],
                ]
            )


def list_users() -> list[sqlite3.Row]:
    con = connect()
    try:
        return con.execute("SELECT username, role, full_name, phone FROM users ORDER BY username;").fetchall()
    finally:
        con.close()


def create_user(username: str, password: str, role: str, full_name: str = "", phone: str = "") -> None:
    con = connect()
    try:
        con.execute(
            "INSERT INTO users(username,password,role,full_name,phone) VALUES(?,?,?,?,?);",
            (username.strip(), password, role, (full_name or "").strip(), (phone or "").strip()),
        )
        con.commit()
    finally:
        con.close()

