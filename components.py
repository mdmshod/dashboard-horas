import flet as ft
import calendar
from datetime import datetime

class StatCard(ft.Card):
    """Tarjeta moderna para mostrar KPIs (horas, días, etc.)."""
    def __init__(self, title, icon, color=ft.colors.BLUE_400):
        super().__init__(elevation=4)
        self.val_text = ft.Text("0", size=26, weight=ft.FontWeight.BOLD, color=color)
        self.content = ft.Container(
            padding=15,
            width=220,
            content=ft.Row([
                ft.Icon(icon, size=40, color=color),
                ft.Column([
                    ft.Text(title, size=13, color=ft.colors.WHITE70),
                    self.val_text
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=2)
            ])
        )

    def update_value(self, new_value):
        self.val_text.value = str(new_value)
        self.update()

class BatteryIndicator(ft.Container):
    """Indicador animado que simula una batería de teléfono."""
    def __init__(self):
        super().__init__()
        # El interior de la batería que se animará
        self.inner = ft.Container(
            width=54, height=0, bgcolor=ft.colors.RED,
            border_radius=ft.border_radius.only(bottom_left=4, bottom_right=4),
            animate=ft.animation.Animation(600, ft.AnimationCurve.EASE_OUT)
        )
        self.percentage_text = ft.Text("0.0%", weight=ft.FontWeight.BOLD, size=18)

        # Diseño estructural de la batería
        tip = ft.Container(width=20, height=8, bgcolor=ft.colors.WHITE54, border_radius=ft.border_radius.only(top_left=4, top_right=4))
        body = ft.Container(
            width=60, height=140,
            border=ft.border.all(3, ft.colors.WHITE54),
            border_radius=8,
            alignment=ft.alignment.bottom_center,
            content=self.inner
        )

        self.content = ft.Column(
            controls=[tip, body, ft.Container(height=5), self.percentage_text],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        )

    def update_level(self, percentage):
        clamped_percentage = min(100.0, max(0.0, percentage))
        self.percentage_text.value = f"{clamped_percentage:.1f}%"
        # Altura máxima interna descontando bordes es ~134
        self.inner.height = (clamped_percentage / 100) * 134 

        if clamped_percentage <= 20:
            self.inner.bgcolor = ft.colors.RED
        elif clamped_percentage <= 50:
            self.inner.bgcolor = ft.colors.ORANGE
        elif clamped_percentage <= 80:
            self.inner.bgcolor = ft.colors.YELLOW
        else:
            self.inner.bgcolor = ft.colors.GREEN
            
        self.update()

class CalendarView(ft.Card):
    """Calendario interactivo con lógica de días laborables/sábados/domingos."""
    def __init__(self, data_manager, on_toggle):
        super().__init__(elevation=4)
        self.data = data_manager
        self.on_toggle = on_toggle
        
        now = datetime.now()
        self.year = now.year
        self.month = now.month

        self.month_label = ft.Text(size=20, weight="bold")
        self.grid = ft.Column(spacing=5)

        self.content = ft.Container(
            padding=20,
            content=ft.Column([
                ft.Row([
                    ft.IconButton(ft.icons.CHEVRON_LEFT, on_click=self.prev_month),
                    self.month_label,
                    ft.IconButton(ft.icons.CHEVRON_RIGHT, on_click=self.next_month),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                self.grid
            ])
        )
        self.build_calendar()

    def prev_month(self, e):
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1
        self.build_calendar()
        self.update()

    def next_month(self, e):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self.build_calendar()
        self.update()

    def build_calendar(self):
        meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.month_label.value = f"{meses[self.month]} {self.year}"
        self.grid.controls.clear()

        # Encabezados de días
        days_header = ft.Row(
            controls=[
                ft.Container(content=ft.Text(d, weight="bold", color=ft.colors.BLUE_200),
                             width=45, alignment=ft.alignment.center) 
                for d in ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )
        self.grid.controls.append(days_header)

        # Matriz de días
        cal = calendar.monthcalendar(self.year, self.month)
        for week in cal:
            row = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=5)
            for weekday, day in enumerate(week):
                if day == 0:
                    row.controls.append(ft.Container(width=45, height=45))
                else:
                    date_str = f"{self.year}-{self.month:02d}-{day:02d}"
                    is_worked = date_str in self.data.worked_days
                    is_sunday = (weekday == 6)

                    # Estilos según las reglas del negocio
                    if is_sunday:
                        bg_color = ft.colors.GREY_900
                        text_color = ft.colors.GREY_700
                    else:
                        bg_color = ft.colors.BLUE_700 if is_worked else ft.colors.GREY_800
                        text_color = ft.colors.WHITE

                    is_today = date_str == datetime.now().strftime("%Y-%m-%d")
                    border = ft.border.all(2, ft.colors.AMBER) if is_today else None

                    btn = ft.Container(
                        content=ft.Text(str(day), color=text_color),
                        width=45, height=45,
                        alignment=ft.alignment.center,
                        bgcolor=bg_color,
                        border_radius=8,
                        border=border,
                        on_click=None if is_sunday else (lambda e, ds=date_str: self.handle_day_click(ds)),
                        ink=not is_sunday # Efecto de click (ripple) solo si no es domingo
                    )
                    row.controls.append(btn)
            self.grid.controls.append(row)

    def handle_day_click(self, date_str):
        self.data.toggle_day(date_str)
        self.build_calendar() # Reconstruye el mes para actualizar colores
        self.update()
        self.on_toggle() # Notifica al Dashboard principal

class MonthlyStatsCard(ft.Card):
    """Muestra un resumen de horas acumuladas agrupadas por mes."""
    def __init__(self):
        super().__init__(elevation=4)
        self.stats_column = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO, height=120)
        self.content = ft.Container(
            padding=15, width=220,
            content=ft.Column([
                ft.Text("Horas por Mes", weight="bold", size=14, color=ft.colors.WHITE70),
                ft.Divider(height=1),
                self.stats_column
            ])
        )

    def update_stats(self, month_stats):
        self.stats_column.controls.clear()
        if not month_stats:
            self.stats_column.controls.append(ft.Text("Sin registros", color=ft.colors.WHITE54))
        else:
            # Ordenar meses de más reciente a más antiguo
            for m_key in sorted(month_stats.keys(), reverse=True):
                self.stats_column.controls.append(
                    ft.Row([
                        ft.Text(m_key, size=13),
                        ft.Text(f"{month_stats[m_key]}h", weight="bold", color=ft.colors.BLUE_200, size=13)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                )
        self.update()