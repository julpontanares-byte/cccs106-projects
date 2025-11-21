import flet as ft
import httpx
from weather_service import WeatherService
from config import Config
import json
from pathlib import Path


class WeatherApp:
    """Main Weather Application class."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.history_file = Path("search_history.json")
        self.search_history = self.load_history()
        self.weather_service = WeatherService()
        self.setup_page()
        self.build_ui()

    def setup_page(self):
        self.page.title = Config.APP_TITLE
        self.page.theme_mode = ft.ThemeMode.SYSTEM
        self.page.theme = ft.Theme(
            color_scheme_seed=ft.Colors.BLUE,
            )
        
        self.page.padding = 20

        # Window properties are accessed via page.window object in Flet 0.28.3
        self.page.window.frameless = True
        self.page.window.width = 700
        self.page.window.height = 800
        self.page.window.min_width = 400
        self.page.window.min_height = 600
        self.page.window.resizable = True
        self.page.window.center()
        self.page.scroll = ft.ScrollMode.AUTO
        
        # Center the window on desktop
        self.page.window.center()
    
    def load_history(self):
        """Load saved search history from file."""
        if self.history_file.exists():
            with open(self.history_file, "r") as f:
                return json.load(f)
        return []

    def on_history_select(self, e):
        """Handle dropdown selection."""
        selected_city = e.control.value
        if selected_city:
            self.city_input.value = selected_city
            self.page.update()
            self.page.run_task(self.get_weather)

    def build_history_dropdown(self):
        """Build dropdown with event handler connected."""
        return ft.Dropdown(
            label="Recent Searches",
            width=350,
            border_radius=12,
            text_size=16,
            border_color=ft.Colors.BLUE_400,
            bgcolor=ft.Colors.WHITE,
            options=[ft.dropdown.Option(city) for city in self.search_history],
            on_change=self.on_history_select, 
            expand=True,
        )

    def save_history(self):
        """Save city to search history."""
        with open(self.history_file, "w") as f:
            json.dump(self.search_history, f)

    def add_to_history(self, city: str):
        """Add city to search history."""
        city = city.strip()
        if city not in self.search_history:
            self.search_history.insert(0, city)
            self.search_history = self.search_history[:5] 
            self.save_history()
    
    def update_history_dropdown(self):
        """Update the search history dropdown options."""
        self.history_dropdown.options = [
            ft.dropdown.Option(city) for city in self.search_history
        ]
        self.history_section.visible = True
        self.page.update()

    def build_ui(self):
        """Build the user interface."""
        # Title
        self.title = ft.Row(
            [
                ft.Text("☁️", size=32),
                ft.Text(
                    "Weather App",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_700,
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=8,
        )
        
        
        self.theme_button = ft.IconButton(
            icon=ft.Icons.NIGHTLIGHT_OUTLINED,
            tooltip="Toggle Theme",
            on_click=self.toggle_theme,
            icon_color=ft.Colors.BLUE_700,
        ) 
        
        title_row = ft.Row(
            [
                self.title,
                self.theme_button,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        
        # City input field
        self.city_input = ft.TextField(
            label="Enter city name",
            border_color=ft.Colors.BLUE_400,
            prefix=ft.Icons.LOCATION_CITY,
            hint_text="e.g., London, Tokyo, New York",
            autofocus=True,
            expand=True,
            border_radius=12,
            height= 40,
            on_submit=self.on_search_async,
        )
        
        # Search history dropdown
        self.history_dropdown = self.build_history_dropdown()
        
        # History section container (fits UI layout)
        self.history_section = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Recent Searches",
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.BLUE_700,
                    ),
                    self.history_dropdown,
                ],
                spacing=6,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ft.Colors.BLUE_50,
            border_radius=12,
            padding=15,
            width=800,
            visible=True if self.search_history else False,
        )

        # Search button
        self.search_button = ft.ElevatedButton(
            "Search",
            icon=ft.Icons.SEARCH,
            on_click=self.on_search_async,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=20),
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
            ),
            height=50,
        )

        city_row = ft.Row(
            [
                self.city_input,
                self.search_button,
            ],
            spacing=10,
            width=800,
        )
        self.city_input.expand = True

        # Weather display container (initially hidden)
        self.weather_container = ft.Container(
            visible=False,
            bgcolor=ft.Colors.BLUE_50,
            border_radius=12,
            padding=20,
            width=900,
            alignment=ft.alignment.center,
        )

        # Forecast container (hidden initially)
        self.forecast_container = ft.Container(
            visible=False,
            bgcolor=ft.Colors.BLUE_50,
            border_radius=12,
            padding=20,
            width=900,
            alignment=ft.alignment.center,
        )

        
        # Error message
        self.error_message = ft.Text(
            "",
            color=ft.Colors.RED_700,
            visible=False,
        )
        
        # Loading indicator
        self.loading = ft.ProgressRing(visible=False)
        
        self.info_box = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.INFO, color=ft.Colors.BLUE_700),
                    ft.Text(
                        "Enter a city name and click Search to get weather information",
                        size=14,
                        color=ft.Colors.BLUE_700,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=ft.Colors.BLUE_100,
            border_radius=12,
            padding=15,
            margin=ft.margin.only(top=15),
            width=800,
            alignment=ft.alignment.center,
        )
        self.info_box.visible = True

        # Add all components to page
        scroll_area = ft.Container(
            content=ft.Column(
                [
                    self.loading,
                    self.error_message,
                    self.weather_container,
                    self.forecast_container,
                    self.info_box,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,   
            ),
            expand=True,
        )

        self.page.add(
            ft.Column(
                    [
                        title_row,
                        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                        city_row,
                        self.history_section,
                        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                        scroll_area,
                    ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                expand=True,
                
            )
        )

    def on_location_click(self, e):
        """Handle location button click."""
        self.page.run_task(self.get_location_weather)

    def toggle_theme(self, e):
        """Toggle betwee light and dark theme."""
        if self.page.theme_mode == ft.ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.DARK
            self.theme_button.icon = ft.Icons.SUNNY
        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.theme_button.icon = ft.Icons.DARK_MODE
        self.page.update()

    async def on_search_async(self, e):
        """Async event handler."""
        await self.get_weather()

        self.search_button = ft.ElevatedButton(
            "Search",
            on_click=self.on_search_async,
    )

    async def get_weather(self):
        """Fetch and display weather data."""
        city = self.city_input.value.strip()

        # Validate input
        if not city:
            self.show_error("Please enter a city name")
            return

        # Show loading, hide previous results
        self.loading.visible = True
        self.error_message.visible = False
        self.weather_container.visible = False
        self.page.update()
        
        try:
            # Fetch weather data
            weather_data = await self.weather_service.get_weather(city)
            
            # Add to history
            self.add_to_history(city)
            self.update_history_dropdown()
            
            # Display weather
            await self.display_weather(weather_data)
            forecast_data = await self.weather_service.get_forecast(city)
            await self.display_forecast(forecast_data)
            
        except Exception as e:
            self.show_error(str(e))
        
        finally:
            self.loading.visible = False
            self.page.update()
    
    async def get_location_weather(self):
        """Get weather for current location."""
        # This would require geolocation API
        # For now, use IP-based service
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://ipapi.co/json/")
                data = response.json()
                lat, lon = data['latitude'], data['longitude']
                weather = await self.weather_service.get_weather_by_coordinates(
                    lat, lon
                )
                await self.display_weather(weather)
        except Exception as e:
            self.show_error("Could not get your location")
    
    async def display_weather(self, data: dict):
        """Display weather information."""
        # Extract data
        city_name = data.get("name", "Unknown")
        country = data.get("sys", {}).get("country", "")
        temp = data.get("main", {}).get("temp", 0)
        feels_like = data.get("main", {}).get("feels_like", 0)
        humidity = data.get("main", {}).get("humidity", 0)
        pressure = data.get("main", {}).get("pressure", 0)
        temp_min = data.get("main", {}).get("temp_min", 0)
        temp_max = data.get("main", {}).get("temp_max", 0)
        cloudiness = data.get("clouds", {}).get("all", 0)
        description = data.get("weather", [{}])[0].get("description", "").title()
        icon_code = data.get("weather", [{}])[0].get("icon", "01d")
        wind_speed = data.get("wind", {}).get("speed", 0)

        temp = data.get("main", {}).get("temp", 0)
        if temp > 35:
            alert = ft.Banner(
                bgcolor=ft.Colors.AMBER_100,
                leading=ft.Icon(ft.Icons.WARNING, color=ft.Colors.AMBER, size=40),
                content=ft.Text("⚠️ High temperature alert!"),
            )
            self.page.banner = alert
            self.page.banner.open = True
            self.page.update()
    
        self.weather_container.bgcolor = ft.Colors.BLUE_100
        self.weather_container.border_radius = 12
        self.weather_container.padding = 30
        self.weather_container.width = 700
    
        # Build weather display
        location = ft.Row(
            [
                ft.Icon(ft.Icons.LOCATION_ON, color=ft.Colors.RED_700),
                ft.Text(
                    f"{city_name}, {country}",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_900,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        )

        weather_icon = ft.Image(
            src=f"https://openweathermap.org/img/wn/{icon_code}@2x.png",
            width=100,
            height=100
        )

        description_text = ft.Text(description,
                            size=20,
                            italic=True,
                            color=ft.Colors.GREY_800,
                            )
        temp_text = ft.Text(
            f"{temp:.1f}°C",
            size=48,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_900,
        )

        feels_like_text = ft.Text(
            f"Feels like {feels_like:.1f}°C",
            size=16,
            color=ft.Colors.GREY_700,
        )

        min_max_text =  ft.Text(
                    f"↑ {temp_max:.1f}°C  ↓ {temp_min:.1f}°C",
                    size=16,
                    color=ft.Colors.GREY_700,
                )

        divider = ft.Divider(height=20, color=ft.Colors.TRANSPARENT)

        info_cards = ft.GridView(
            expand=False,
            max_extent=160,
            child_aspect_ratio=1.3,
            run_spacing=20,
            spacing=20,
            controls=[
                self.create_info_card(
                    ft.Icons.WATER_DROP, "Humidity", f"{humidity}%", ft.Colors.BLUE_400
                ),
                self.create_info_card(
                    ft.Icons.AIR, "Wind Speed", f"{wind_speed} m/s", ft.Colors.TEAL_300
                ),  
                self.create_info_card(
                    ft.Icons.COMPRESS, "Pressure", f"{pressure} hPa", ft.Colors.PURPLE_400
                ),
                self.create_info_card(
                    ft.Icons.CLOUD, "Cloudiness", f"{cloudiness}%", ft.Colors.GREY_700
                ),
            ],
        )

        self.weather_container.content = ft.Column(
            [
                location,
                weather_icon,
                description_text,
                temp_text,
                feels_like_text,
                min_max_text,
                divider,
                info_cards,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

        
        self.weather_container.animate_opacity = 300
        self.weather_container.opacity = 0
        self.weather_container.visible = True
        self.error_message.visible = False
        self.page.update()

        import asyncio
        await asyncio.sleep(0.1)
        self.weather_container.opacity = 1
        self.page.update()

    async def display_forecast(self, data: dict):
        forecast_list = data.get("list", [])
        daily = {}

        # Organize 5 days by taking 12:00 noon entry
        for item in forecast_list:
            date = item["dt_txt"].split(" ")[0]
            time = item["dt_txt"].split(" ")[1]
            if time == "12:00:00" and len(daily) < 5:
                daily[date] = item

        cards = []
        for date, info in daily.items():
            temp_min = info["main"]["temp_min"]
            temp_max = info["main"]["temp_max"]
            desc = info["weather"][0]["description"].title()
            icon = info["weather"][0]["icon"]

            card = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(date, weight=ft.FontWeight.BOLD, size=16),
                        ft.Image(
                            src=f"https://openweathermap.org/img/wn/{icon}@2x.png",
                            width=60,
                            height=60,
                        ),
                        ft.Text(desc, size=14),
                        ft.Text(f"High: {temp_max:.1f}°C", size=14),
                        ft.Text(f"Low: {temp_min:.1f}°C", size=14),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                ),
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                padding=15,
                width=150,
                alignment=ft.alignment.center,
            )
            cards.append(card)

        forecast_view = ft.Row(
            cards,
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        self.forecast_container.content = ft.Column(
            [
                ft.Text(
                    "5-Day Weather Forecast",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_900,
                ),
                forecast_view,
            ],
            spacing=15,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.forecast_container.visible = True
        self.page.update()

        
    def create_info_card(self, icon, label, value, icon_color):
        """Create an info card for weather details."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icon, size=30, color=icon_color),
                    ft.Text(label, size=12, color=ft.Colors.GREY_600),
                    ft.Text(
                        value,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_900,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            ),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=15,
            width=150,
            height=120,
            alignment=ft.alignment.center,
            shadow=ft.BoxShadow(
                blur_radius=3,
                spread_radius=1,
                color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                offset=ft.Offset(0, 6),
            ),
        )
    
    def show_error(self, message: str):
        """Display error message."""
        self.error_message.value = f"❌ {message}"
        self.error_message.visible = True
        self.weather_container.visible = False
        self.page.update()

    
def main(page: ft.Page):
    """Main entry point."""
    WeatherApp(page)


if __name__ == "__main__":
    ft.app(target=main)                                                                                                      # weather_service.py
