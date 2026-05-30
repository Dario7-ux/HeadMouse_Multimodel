import os
import sqlite3
import json
import uuid
import logging
from datetime import datetime

logger = logging.getLogger("DatabaseManager")

DB_PATH = os.path.join("configs", "focuzvoz.db")


class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        # Asegurar que el directorio configs exista
        os.makedirs("configs", exist_ok=True)
        self.db_path = DB_PATH
        self._init_db()
        self._initialized = True

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")  # Habilitar eliminaciones en cascada
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Inicializar todas las tablas relacionales de la base de datos."""
        logger.info(f"Initializing SQLite database at {self.db_path}")
        with self._get_connection() as conn:
            # 1. Tabla de Perfiles
            conn.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    name TEXT PRIMARY KEY
                );
            """)

            # 2. Tabla de Configuración de Cursor
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cursor_config (
                    profile_name TEXT PRIMARY KEY,
                    config_json TEXT NOT NULL,
                    FOREIGN KEY (profile_name) REFERENCES profiles(name) ON DELETE CASCADE
                );
            """)

            # 3. Tabla de Asignaciones (Teclado/Ratón)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bindings (
                    profile_name TEXT,
                    gesture_name TEXT,
                    device_name TEXT, -- 'mouse' o 'keyboard'
                    action_name TEXT NOT NULL,
                    threshold REAL NOT NULL,
                    trigger_type TEXT NOT NULL, -- 'single' o 'hold'
                    PRIMARY KEY (profile_name, gesture_name, device_name),
                    FOREIGN KEY (profile_name) REFERENCES profiles(name) ON DELETE CASCADE
                );
            """)

            # 4. Tabla de Configuración de Voz
            conn.execute("""
                CREATE TABLE IF NOT EXISTS voice_config (
                    profile_name TEXT PRIMARY KEY,
                    config_json TEXT NOT NULL,
                    FOREIGN KEY (profile_name) REFERENCES profiles(name) ON DELETE CASCADE
                );
            """)

            # 5. Tabla de Sesiones de Investigación
            conn.execute("""
                CREATE TABLE IF NOT EXISTS research_sessions (
                    session_id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL,
                    profile_name TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    total_clicks INTEGER DEFAULT 0,
                    total_keystrokes INTEGER DEFAULT 0,
                    total_voice_commands INTEGER DEFAULT 0,
                    total_distance_px REAL DEFAULT 0.0,
                    active_duration_seconds REAL DEFAULT 0.0,
                    subject_first_name TEXT DEFAULT '',
                    subject_last_name TEXT DEFAULT ''
                );
            """)

            # Auto-migración: comprobar si las columnas existen en las bases de datos de usuarios existentes, agregarlas si faltan
            try:
                conn.execute("ALTER TABLE research_sessions ADD COLUMN subject_first_name TEXT DEFAULT '';")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE research_sessions ADD COLUMN subject_last_name TEXT DEFAULT '';")
            except sqlite3.OperationalError:
                pass

            # 6. Tabla de Eventos de Investigación
            conn.execute("""
                CREATE TABLE IF NOT EXISTS research_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL, -- 'mouse_move', 'click', 'keystroke', 'voice_command', etc.
                    gesture_name TEXT,
                    blendshape_value REAL,
                    cursor_x REAL,
                    cursor_y REAL,
                    dwell_time_ms REAL,
                    voice_text TEXT,
                    voice_confidence REAL,
                    voice_success INTEGER,
                    voice_duration_ms REAL,
                    FOREIGN KEY (session_id) REFERENCES research_sessions(session_id) ON DELETE CASCADE
                );
            """)
            conn.commit()

    # --- Operaciones de Perfil ---
    def get_profiles(self) -> list:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT name FROM profiles ORDER BY name ASC;")
            return [row["name"] for row in cursor.fetchall()]

    def add_profile(self, name: str) -> bool:
        try:
            with self._get_connection() as conn:
                conn.execute("INSERT INTO profiles (name) VALUES (?);", (name,))
                conn.commit()
            logger.info(f"Profile '{name}' successfully added to database.")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Profile '{name}' already exists.")
            return False

    def rename_profile(self, old_name: str, new_name: str) -> bool:
        try:
            with self._get_connection() as conn:
                # Actualizar la tabla de perfiles (se propaga automáticamente debido a las referencias de clave foránea con ON UPDATE/ON DELETE manejadas manualmente o mediante transacción)
                # El borrado/actualización en cascada de SQLite no siempre está habilitado por defecto para tablas estándar a menos que se especifique, por lo que actualizamos las tablas secundarias directamente dentro de una transacción.
                conn.execute("BEGIN TRANSACTION;")
                conn.execute("INSERT OR IGNORE INTO profiles (name) VALUES (?);", (new_name,))
                conn.execute("UPDATE cursor_config SET profile_name = ? WHERE profile_name = ?;", (new_name, old_name))
                conn.execute("UPDATE bindings SET profile_name = ? WHERE profile_name = ?;", (new_name, old_name))
                conn.execute("UPDATE voice_config SET profile_name = ? WHERE profile_name = ?;", (new_name, old_name))
                conn.execute("DELETE FROM profiles WHERE name = ?;", (old_name,))
                conn.commit()
            logger.info(f"Renamed profile '{old_name}' to '{new_name}'")
            return True
        except Exception as e:
            logger.error(f"Error renaming profile: {e}")
            return False

    def delete_profile(self, name: str) -> bool:
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM profiles WHERE name = ?;", (name,))
                conn.commit()
            logger.info(f"Profile '{name}' deleted from database.")
            return True
        except Exception as e:
            logger.error(f"Error deleting profile: {e}")
            return False

    # --- Operaciones de Configuración y Asignaciones ---
    def get_cursor_config(self, profile_name: str) -> dict:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT config_json FROM cursor_config WHERE profile_name = ?;", (profile_name,))
            row = cursor.fetchone()
            return json.loads(row["config_json"]) if row else {}

    def save_cursor_config(self, profile_name: str, config: dict):
        self.add_profile(profile_name)  # Asegurar que el perfil exista
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO cursor_config (profile_name, config_json)
                VALUES (?, ?)
                ON CONFLICT(profile_name) DO UPDATE SET config_json = excluded.config_json;
            """, (profile_name, json.dumps(config, indent=4)))
            conn.commit()

    def get_bindings(self, profile_name: str, device_name: str) -> dict:
        """Obtiene las asignaciones para un perfil y dispositivo específico en el formato de diccionario heredado."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT gesture_name, device_name, action_name, threshold, trigger_type
                FROM bindings
                WHERE profile_name = ? AND device_name = ?;
            """, (profile_name, device_name))
            
            bindings_dict = {}
            for row in cursor.fetchall():
                # Formato heredado: gesture_name -> [device, action, threshold, trigger_type]
                bindings_dict[row["gesture_name"]] = [
                    row["device_name"],
                    row["action_name"],
                    row["threshold"],
                    row["trigger_type"]
                ]
            return bindings_dict

    def save_bindings(self, profile_name: str, device_name: str, bindings: dict):
        self.add_profile(profile_name)  # Asegurar que el perfil exista
        with self._get_connection() as conn:
            # Eliminar las asignaciones antiguas para este dispositivo para sincronizar completamente
            conn.execute("""
                DELETE FROM bindings WHERE profile_name = ? AND device_name = ?;
            """, (profile_name, device_name))
            
            # Insertar las nuevas
            for gesture_name, val in bindings.items():
                if len(val) >= 4:
                    conn.execute("""
                        INSERT INTO bindings (profile_name, gesture_name, device_name, action_name, threshold, trigger_type)
                        VALUES (?, ?, ?, ?, ?, ?);
                    """, (profile_name, gesture_name, val[0], val[1], float(val[2]), val[3]))
            conn.commit()

    def get_voice_config(self, profile_name: str) -> dict:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT config_json FROM voice_config WHERE profile_name = ?;", (profile_name,))
            row = cursor.fetchone()
            return json.loads(row["config_json"]) if row else {}

    def save_voice_config(self, profile_name: str, config: dict):
        self.add_profile(profile_name)  # Asegurar que el perfil exista
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO voice_config (profile_name, config_json)
                VALUES (?, ?)
                ON CONFLICT(profile_name) DO UPDATE SET config_json = excluded.config_json;
            """, (profile_name, json.dumps(config, indent=4)))
            conn.commit()

    # --- Telemetría de Investigación de Usabilidad ---
    def start_research_session(self, subject_id: str, profile_name: str,
                               subject_first_name: str = "", subject_last_name: str = "") -> str:
        session_id = str(uuid.uuid4())
        start_time = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO research_sessions (session_id, subject_id, profile_name, start_time, subject_first_name, subject_last_name)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (session_id, subject_id, profile_name, start_time, subject_first_name, subject_last_name))
            conn.commit()
        logger.info(f"Started research session {session_id} for subject {subject_first_name} {subject_last_name}")
        return session_id

    def end_research_session(self, session_id: str, total_clicks: int, total_keystrokes: int,
                             total_voice_commands: int, total_distance_px: float, active_duration_seconds: float):
        end_time = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE research_sessions
                SET end_time = ?,
                    total_clicks = ?,
                    total_keystrokes = ?,
                    total_voice_commands = ?,
                    total_distance_px = ?,
                    active_duration_seconds = ?
                WHERE session_id = ?;
            """, (end_time, total_clicks, total_keystrokes, total_voice_commands, total_distance_px, active_duration_seconds, session_id))
            conn.commit()
        logger.info(f"Ended research session {session_id}")

    def log_research_event(self, session_id: str, event_type: str, gesture_name: str = None,
                           blendshape_value: float = None, cursor_x: float = None, cursor_y: float = None,
                           dwell_time_ms: float = None, voice_text: str = None, voice_confidence: float = None,
                           voice_success: int = None, voice_duration_ms: float = None):
        timestamp = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO research_events (
                    session_id, timestamp, event_type, gesture_name, blendshape_value,
                    cursor_x, cursor_y, dwell_time_ms, voice_text, voice_confidence,
                    voice_success, voice_duration_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (session_id, timestamp, event_type, gesture_name, blendshape_value,
                  cursor_x, cursor_y, dwell_time_ms, voice_text, voice_confidence,
                  voice_success, voice_duration_ms))
            conn.commit()

    def get_all_research_sessions(self) -> list:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM research_sessions ORDER BY start_time DESC;")
            return [dict(row) for row in cursor.fetchall()]

    def get_session_events(self, session_id: str) -> list:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM research_events WHERE session_id = ? ORDER BY timestamp ASC;", (session_id,))
            return [dict(row) for row in cursor.fetchall()]
