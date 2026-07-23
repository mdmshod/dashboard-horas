import json
import os

class DataManager:
    """Maneja la lectura y escritura del estado de la aplicación en un archivo JSON."""
    
    def __init__(self, filename="data.json"):
        self.filename = filename
        self.data = {
            "goal": 800, 
            "worked_days": [], 
            "notified_100": False
        }
        self.load()

    def load(self):
        """Carga los datos si el archivo existe."""
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                try:
                    loaded = json.load(f)
                    self.data.update(loaded)
                except json.JSONDecodeError:
                    pass # Si el archivo está corrupto, usa los valores por defecto

    def save(self):
        """Guarda el estado actual en el disco."""
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
        """Alterna el estado de un día (marcado/desmarcado)."""
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