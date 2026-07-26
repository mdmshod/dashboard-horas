import os
import flet as ft
from datetime import datetime
import openpyxl
from models import DataManager
from components import StatCard, BatteryIndicator, CalendarView, MonthlyStatsCard

def main(page: ft.Page):
    page.title = "Dashboard - Control de Avance"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 15
    page.scroll = ft.ScrollMode.AUTO  # Permite desplazamiento vertical
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    data = DataManager("data.json")

    # --- Componentes UI ---
    battery = BatteryIndicator()
    card_accum = StatCard("Horas Acumuladas", ft.icons.ACCESS_TIME, ft.colors.BLUE_400)
    card_rem = StatCard("Horas Restantes", ft.icons.TIMER_OFF, ft.colors.ORANGE_400)
    card_days = StatCard("Días Trabajados", ft.icons.CALENDAR_MONTH, ft.colors.GREEN_400)
    card_sats = StatCard("Sábados Trabajados", ft.icons.EVENT_AVAILABLE, ft.colors.PURPLE_400)
    monthly_card = MonthlyStatsCard()
    
    progress_bar = ft.ProgressBar(value=0, color=ft.colors.BLUE_400, bgcolor=ft.colors.GREY_800, height=8)

    # --- Diálogo de Felicitación ---
    dlg_congrats = ft.AlertDialog(
        title=ft.Text("¡Objetivo Completado! 🎉", size=24, color=ft.colors.GREEN_400),
        content=ft.Text("Has alcanzado el 100% de tu objetivo de horas. ¡Excelente trabajo!"),
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
            
            h = 8 if wd < 5 else (4 if wd == 5 else 0)
            total_hours += h
            
            if wd == 5:
                total_sats += 1
                
            m_key = dt.strftime("%Y-%m")
            month_stats[m_key] = month_stats.get(m_key, 0) + h

        remaining = max(0, data.goal - total_hours)
        percentage = (total_hours / data.goal) * 100 if data.goal > 0 else 0

        card_accum.update_value(total_hours)
        card_rem.update_value(remaining)
        card_days.update_value(len(data.worked_days))
        card_sats.update_value(total_sats)
        monthly_card.update_stats(month_stats)
        
        battery.update_level(percentage)
        progress_bar.value = min(1.0, percentage / 100)
        progress_bar.update()

        if percentage >= 100 and not data.notified_100:
            dlg_congrats.open = True
            data.notified_100 = True
        elif percentage < 100:
            data.notified_100 = False

    calendar_view = CalendarView(data, on_toggle=update_dashboard)

    # --- Funciones Extra (Meta y Exportación) ---
    def update_goal(e):
        try:
            val = int(e.control.value)
            if val > 0:
                data.goal = val
                update_dashboard()
        except ValueError:
            pass

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

    # --- Controles Superiores ---
    goal_input = ft.TextField(
        label="Meta (Hs)", value=str(data.goal), 
        width=100, height=40, text_size=12,
        keyboard_type=ft.KeyboardType.NUMBER,
        on_submit=update_goal, on_blur=update_goal
    )

    header = ft.Row([
        ft.Text("Panel de Avance", size=24, weight="bold"),
        ft.Row([
            goal_input,
            ft.IconButton(icon=ft.icons.DOWNLOAD, tooltip="Exportar Excel", on_click=export_excel, icon_color=ft.colors.BLUE_200)
        ], spacing=10)
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True)

    # --- Layout Responsivo (Apto para Móviles y Escritorio) ---
    main_content = ft.ResponsiveRow([
        # Columna de KPIs (4 columnas en escritorio, 12 en móviles)
        ft.Column([card_accum, card_rem, card_days, card_sats, monthly_card], col={"sm": 12, "md": 4}, spacing=10),
        # Batería
        ft.Container(content=battery, col={"sm": 12, "md": 2}, alignment=ft.alignment.center, padding=10),
        # Calendario
        ft.Container(content=calendar_view, col={"sm": 12, "md": 6})
    ], vertical_alignment=ft.CrossAxisAlignment.START)

    # Añadir todo directamente a la página
    page.add(
        ft.Container(
            content=ft.Column([
                header,
                progress_bar,
                ft.Container(height=10),
                main_content
            ], spacing=15),
            max_width=1200 # Limita el ancho en pantallas gigantes para verse centrado
        )
    )

    update_dashboard()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    ft.app(
        target=main, 
        view=ft.AppView.WEB_BROWSER, 
        host="0.0.0.0", 
        port=port
    )
