import os
import flet as ft
from datetime import datetime
import openpyxl
import traceback
from models import DataManager
from components import StatCard, BatteryIndicator, CalendarView, MonthlyStatsCard

def main(page: ft.Page):
    page.title = "Dashboard - Control de Avance"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ft.colors.BACKGROUND # Evita el negro absoluto si falla el tema
    
    # Envolvemos toda la lógica en un try-except para atrapar errores y mostrarlos en pantalla
    try:
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

        # --- Funciones Extra ---
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
                page.snack_bar = ft.SnackBar(ft.Text("Excel generado con éxito!"), bgcolor=ft.colors.GREEN_700)
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

        header = ft.ResponsiveRow([
            ft.Text("Panel de Avance", size=24, weight="bold", col={"xs": 12, "sm": 6}),
            ft.Row([
                goal_input,
                ft.IconButton(icon=ft.icons.DOWNLOAD, tooltip="Exportar", on_click=export_excel, icon_color=ft.colors.BLUE_200)
            ], alignment=ft.MainAxisAlignment.START, col={"xs": 12, "sm": 6})
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # --- Layout Responsivo ---
        # Usamos "xs" (extra small) para asegurar que se aplique desde la pantalla de móvil más pequeña
        main_content = ft.ResponsiveRow([
            ft.Column([card_accum, card_rem, card_days, card_sats, monthly_card], col={"xs": 12, "md": 4}, spacing=10),
            ft.Container(content=battery, col={"xs": 12, "md": 2}, alignment=ft.alignment.center, padding=10),
            ft.Container(content=calendar_view, col={"xs": 12, "md": 6})
        ])

        # EL SECRETO ESTÁ AQUÍ: ListView es el contenedor maestro para scroll web sin romper dimensiones
        main_layout = ft.ListView(
            expand=True,
            spacing=15,
            padding=15,
            controls=[
                header,
                progress_bar,
                main_content
            ]
        )

        page.add(main_layout)
        update_dashboard()

    except Exception as e:
        # Modo rescate: Si algo se rompe, pinta el error en lugar de dejar la pantalla negra
        error_msg = traceback.format_exc()
        page.add(
            ft.ListView(
                expand=True,
                padding=20,
                controls=[
                    ft.Text("❌ Error crítico al iniciar el dashboard", size=20, color=ft.colors.RED_400, weight="bold"),
                    ft.Text("Detalles técnicos para el desarrollador:", color=ft.colors.WHITE70),
                    ft.Container(
                        bgcolor=ft.colors.GREY_900,
                        padding=10,
                        border_radius=8,
                        content=ft.Text(error_msg, selectable=True, size=12, color=ft.colors.RED_200)
                    )
                ]
            )
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    ft.app(
        target=main, 
        view=ft.AppView.WEB_BROWSER, 
        host="0.0.0.0", 
        port=port
    )
