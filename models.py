import json
import os
import psycopg2

class DataManager:
    """Maneja la persistencia tanto en PostgreSQL (en la nube) como en JSON (local)."""
    
    def __init__(self, filename="data.json"):
        self.filename = filename
        self.db_url = os.environ.get("DATABASE_URL")
        self.data = {
            "goal": 800, 
            "worked_days": [], 
            "notified_100": False
        }
        
        if self.db_url:
            self._init_db()
        self.load()

    def _get_db_connection(self):
        """Obtiene una conexión a la base de datos de Render."""
        # Render utiliza la sintaxis postgres:// pero psycopg2 requiere postgresql://
        url = self.db_url.replace("postgres://", "postgresql://")
        return psycopg2.connect(url)

    def _init_db(self):
        """Crea la tabla en PostgreSQL si no existe."""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_state (
                    id INT PRIMARY KEY,
                    data_json TEXT NOT NULL
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error inicializando PostgreSQL: {e}")

    def load(self):
        """Carga el estado desde PostgreSQL o desde el archivo JSON local."""
        if self.db_url:
            try:
                conn = self._get_db_connection()
                cur = conn.cursor()
                cur.execute("SELECT data_json FROM app_state WHERE id = 1;")
                row = cur.fetchone()
                if row:
                    self.data.update(json.loads(row[0]))
                cur.close()
                conn.close()
                return
            except Exception as e:
                print(f"Error cargando desde DB: {e}")

        # Si no hay DB_URL o falla, usa archivo local
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                try:
                    loaded = json.load(f)
                    self.data.update(loaded)
                except json.JSONDecodeError:
                    pass

    def save(self):
        """Guarda el estado en la base de datos o en el archivo JSON local."""
        if self.db_url:
            try:
                conn = self._get_db_connection()
                cur = conn.cursor()
                data_str = json.dumps(self.data)
                cur.execute("""
                    INSERT INTO app_state (id, data_json) 
                    VALUES (1, %s)
                    ON CONFLICT (id) DO UPDATE SET data_json = EXCLUDED.data_json;
                """, (data_str,))
                conn.commit()
                cur.close()
                conn.close()
                return
            except Exception as e:
                print(f"Error guardando en DB: {e}")

        # Guardado local de respaldo
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4)

    @property
    def goal(self):
        return self.data["goal"]

    @goal.setter
    def goal(self, value):
        self.data["goal"] = value
        self.save()

    @property
    def worked_days(self):
        return self.data["worked_days"]

    def toggle_day(self, date_str):
        if date_str in self.data["worked_days"]:
            self.data["worked_days"].remove(date_str)
        else:
            self.data["worked_days"].append(date_str)
        self.save()

    @property
    def notified_100(self):
        return self.data.get("notified_100", False)

    @notified_100.setter
    def notified_100(self, val):
        self.data["notified_100"] = val
        self.save()
