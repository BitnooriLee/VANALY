import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "vanaly.db"
UPLOADS_DIR = Path(__file__).parent / "uploads"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    UPLOADS_DIR.mkdir(exist_ok=True)

    with db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL DEFAULT '코치님',
                created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS user_goals (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                daily_calories   INTEGER NOT NULL DEFAULT 2000,
                carbs_pct        REAL    NOT NULL DEFAULT 50.0,
                protein_pct      REAL    NOT NULL DEFAULT 25.0,
                fat_pct          REAL    NOT NULL DEFAULT 25.0,
                goal_type        TEXT    NOT NULL DEFAULT 'maintenance',
                updated_at       TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS coach_sessions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                situation    TEXT,
                messages     TEXT    NOT NULL DEFAULT '[]',
                meal_context TEXT    NOT NULL DEFAULT '[]',
                is_crisis    INTEGER NOT NULL DEFAULT 0,
                summary      TEXT,
                created_at   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                closed_at    TEXT
            );

            CREATE TABLE IF NOT EXISTS meals (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id               INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                image_path            TEXT,
                food_items            TEXT,
                calories              INTEGER,
                carbs_g               REAL,
                protein_g             REAL,
                fat_g                 REAL,
                fiber_g               REAL,
                sodium_mg             REAL,
                glycemic_load         REAL,
                blood_sugar_impact    TEXT,
                energy_peak_minutes   INTEGER,
                confidence            REAL,
                feedback_text         TEXT,
                next_meal_suggestion  TEXT,
                raw_analysis          TEXT,
                eaten_at              TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            );
        """)

        # 마이그레이션: 기존 DB에 situation 컬럼이 없을 경우 추가
        try:
            conn.execute("ALTER TABLE coach_sessions ADD COLUMN situation TEXT")
        except Exception:
            pass  # 이미 컬럼이 존재하면 무시

        # 마이그레이션: lang 컬럼 추가
        try:
            conn.execute("ALTER TABLE coach_sessions ADD COLUMN lang TEXT NOT NULL DEFAULT 'ko'")
        except Exception:
            pass
