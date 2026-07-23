import flet as ft
from datetime import datetime
import openpyxl
from models import DataManager
from components import StatCard, BatteryIndicator, CalendarView, MonthlyStatsCard

def main(page: ft.Page):
    page.title = "Dashboard - Control de Avance"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 30
    page.window_min_width = 1100
    page.window_min_height = 700

    data = DataManager("data.json")

    # --- Inicialización de Componentes UI ---
    battery = BatteryIndicator()
    card_accum = StatCard("Horas Acumuladas", ft.icons.ACCESS_TIME, ft.colors.BLUE_400)
    card_rem = StatCard("Horas Restantes", ft.icons.TIMER_OFF, ft.colors.ORANGE_400)
    card_days = StatCard("Días Trabajados", ft.icons.CALENDAR_MONTH, ft.colors.GREEN_400)
    card_sats = StatCard("Sábados Trabajados", ft.icons.EVENT_AVAILABLE, ft.colors.PURPLE_400)
    monthly_card = MonthlyStatsCard()
    
    progress_bar = ft.ProgressBar(value=0, color=ft.colors.BLUE_400, bgcolor=ft.colors.GREY_800, height=8)

    # --- Cuadro de Diálogo (Felicitación) ---
    dlg_congrats = ft.AlertDialog(
        title=ft.Text("¡Objetivo Completado! 🎉", size=24, color=ft.colors.GREEN_400),
        content=ft.Text("Has alcanzado el 100% de tu objetivo de horas. ¡Excelente disciplina!"),
        actions=[ft.TextButton("Cerrar", on_click=lambda e: close_dialog())]
    )
    page.overlay.append(dlg_congrats)

    def close_dialog():
        dlg_congrats.open = False
        page.update()

    # --- Lógica de Negocio ---
    def update_dashboard():
        total_hours = 0
        total_sats = 0
        month_stats = {}

        for d in data.worked_days:
            dt = datetime.strptime(d, "%Y-%m-%d")
            wd = dt.weekday()
            
            # Lunes a Viernes (0-4) -> 8h, Sábado (5) -> 4h
            h = 8 if wd < 5 else (4 if wd == 5 else 0)
            total_hours += h
            
            if wd == 5:
                total_sats += 1
                
            m_key = dt.strftime("%Y-%m")
            month_stats[m_key] = month_stats.get(m_key, 0) + h

        # Cálculos de progreso
        remaining = max(0, data.goal - total_hours)
        percentage = (total_hours / data.goal) * 100 if data.goal > 0 else 0

        # Actualizar UI
        card_accum.update_value(total_hours)
        card_rem.update_value(remaining)
        card_days.update_value(len(data.worked_days))
        card_sats.update_value(total_sats)
        monthly_card.update_stats(month_stats)
        
        battery.update_level(percentage)
        progress_bar.value = min(1.0, percentage / 100)
        progress_bar.update()

        # Validación del 100%
        if percentage >= 100 and not data.notified_100:
            dlg_congrats.open = True
            data.notified_100 = True
        elif percentage < 100:
            data.notified_100 = False

    # Instanciar calendario pasando el callback de actualización
    calendar_view = CalendarView(data, on_toggle=update_dashboard)

    # --- Funciones Extra (Meta y Exportación) ---
    def update_goal(e):
        try:
            val = int(e.control.value)
            if val > 0:
                data.goal = val
                update_dashboard()
        except ValueError:
            pass # Ignorar si no es número

    def export_excel(e):
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Progreso"
            ws.append(["Fecha", "Día", "Horas"])
            
            dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            
            for day in sorted(data.worked_days):
                dt = datetime.strptime(day, "%Y-%m-%d")
                wd = dt.weekday()
                h = 8 if wd < 5 else (4 if wd == 5 else 0)
                ws.append([day, dias_semana[wd], h])
                
            wb.save("reporte_horas.xlsx")
            page.snack_bar = ft.SnackBar(ft.Text("Excel 'reporte_horas.xlsx' generado con éxito!"), bgcolor=ft.colors.GREEN_700)
            page.snack_bar.open = True
            page.update()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error al exportar: {ex}"), bgcolor=ft.colors.RED_700)
            page.snack_bar.open = True
            page.update()

    # --- Maquetación Principal (Layout) ---
    goal_input = ft.TextField(
        label="Objetivo (Horas)", value=str(data.goal), 
        width=120, height=45, keyboard_type=ft.KeyboardType.NUMBER,
        on_submit=update_goal, on_blur=update_goal
    )

    header = ft.Row([
        ft.Text("Panel de Avance", size=32, weight="bold"),
        ft.Row([
            goal_input,
            ft.ElevatedButton("Exportar Excel", icon=ft.icons.DOWNLOAD, on_click=export_excel, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE)
        ], spacing=15)
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    # Ensamblar la pantalla
    page.add(
        header,
        ft.Container(height=10),
        progress_bar,
        ft.Container(height=20),
        ft.Row([
            # Columna Izquierda: KPIs
            ft.Column([card_accum, card_rem, card_days, card_sats, monthly_card], spacing=15),
            # Centro: Batería
            ft.Container(
                content=battery,
                padding=ft.padding.only(left=30, right=30),
                alignment=ft.alignment.center
            ),
            # Derecha: Calendario
            ft.Container(content=calendar_view, expand=True)
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START)
    )

    # Primer renderizado de cálculos
    update_dashboard()

if __name__ == "__main__":
    ft.app(target=main)