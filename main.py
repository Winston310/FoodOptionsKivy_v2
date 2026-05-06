import json
import re
import time
from datetime import datetime
from pathlib import Path

import kivy.app
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.camera import Camera
from kivy.uix.screenmanager import Screen
from kivy.utils import platform

DEFAULT_FOODS = [
    ("Омлет", 270, 18, 19, 3),
    ("Гречка с курицей", 520, 38, 12, 64),
    ("Овсянка с бананом", 360, 11, 7, 65),
    ("Рис с овощами", 410, 9, 8, 78),
    ("Куриный суп", 310, 27, 9, 28),
    ("Творог с ягодами", 290, 31, 8, 20),
    ("Паста с томатным соусом", 480, 15, 9, 86),
    ("Салат с тунцом", 350, 34, 14, 18),
    ("Картофельное пюре", 330, 7, 12, 50),
    ("Индейка с овощами", 430, 42, 13, 29),
    ("Борщ", 300, 15, 12, 32),
    ("Сырники", 450, 24, 19, 47),
    ("Рыба с рисом", 510, 37, 14, 58),
    ("Куриная грудка", 390, 55, 8, 20),
    ("Плов", 620, 27, 24, 76),
    ("Греческий салат", 330, 10, 26, 14),
    ("Яичница", 260, 17, 20, 2),
    ("Суп-пюре", 280, 9, 11, 35),
    ("Булгур с овощами", 420, 12, 9, 76),
    ("Тушёная говядина", 540, 43, 27, 20),
    ("Котлеты с гречкой", 610, 35, 25, 61),
    ("Лапша с курицей", 560, 34, 17, 69),
    ("Фасоль с овощами", 390, 19, 8, 63),
    ("Тост с авокадо", 340, 10, 20, 30),
    ("Каша пшённая", 370, 10, 9, 64),
    ("Рагу овощное", 310, 8, 13, 42),
    ("Запечённая рыба", 420, 45, 18, 16),
    ("Курица карри", 580, 39, 25, 50),
    ("Салат Цезарь", 520, 31, 34, 22),
    ("Пельмени", 650, 27, 28, 76),
    ("Шакшука", 330, 18, 21, 16),
    ("Перловка с грибами", 400, 12, 10, 70),
    ("Сэндвич с индейкой", 430, 28, 16, 44),
    ("Гороховый суп", 360, 22, 9, 51),
    ("Курица с картофелем", 590, 39, 20, 63),
    ("Рис с яйцом", 460, 17, 13, 70),
    ("Творожная запеканка", 410, 27, 14, 42),
    ("Макароны с сыром", 620, 24, 28, 72),
    ("Овощной салат", 220, 5, 15, 18),
    ("Стейк из индейки", 450, 55, 16, 14),
    ("Кускус с овощами", 390, 11, 8, 71),
    ("Суп с фрикадельками", 420, 24, 18, 38),
    ("Блины", 520, 16, 18, 76),
    ("Лосось с овощами", 560, 42, 35, 19),
    ("Чечевичный суп", 380, 23, 7, 58),
    ("Паста с курицей", 640, 41, 22, 70),
    ("Картошка с грибами", 430, 9, 17, 62),
    ("Рисовая каша", 340, 9, 8, 61),
    ("Куриные тефтели", 490, 36, 20, 38),
    ("Салат с курицей", 410, 35, 19, 17),
]


def format_number(value):
    value = float(value)
    if value.is_integer():
        return str(int(value))
    return f"{value:.1f}"


def today_key(timestamp=None):
    if timestamp is None:
        timestamp = time.time()
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")


class MenuScreen(Screen):
    def on_pre_enter(self):
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self.update_summary(), 0)

    def update_summary(self):
        if "summary_label" not in self.ids:
            return

        app = App.get_running_app()

        if not hasattr(app, "history"):
            return

        self.ids.summary_label.text = app.get_today_summary_text()


class FoodListScreen(Screen):
    def on_pre_enter(self):
        self.refresh()

    def refresh(self):
        app = kivy.app.App.get_running_app()
        self.ids.food_list.clear_widgets()
        self.ids.total_label.text = app.get_today_summary_text()

        foods = sorted(
            app.foods.items(),
            key=lambda item: (item[1].get("last_eaten", 0), item[0].lower())
        )

        if not foods:
            self.ids.food_list.add_widget(EmptyRow())
            return

        total = len(foods)

        for index, (food_name, food_data) in enumerate(foods, start=1):
            last_eaten = food_data.get("last_eaten", 0)
            if last_eaten:
                last_text = datetime.fromtimestamp(last_eaten).strftime("%d.%m.%Y %H:%M")
            else:
                last_text = "ещё не ели"

            kcal = format_number(food_data.get("calories", 0))
            protein = format_number(food_data.get("protein", 0))
            fat = format_number(food_data.get("fat", 0))
            carbs = format_number(food_data.get("carbs", 0))
            photo_path = food_data.get("photo_path", "")

            row = FoodRow(
                food_name=food_name,
                title_text=f"{index}/{total}. {food_name}",
                last_text=f"Последний раз: {last_text}",
                macro_text=f"{kcal} ккал   Б {protein} г   Ж {fat} г   У {carbs} г",
                photo_text="Фото: есть" if photo_path else "Фото: нет",
            )
            self.ids.food_list.add_widget(row)


class AddFoodScreen(Screen):
    def on_pre_enter(self):
        self.ids.result_label.text = ""

    def add_food(self):
        name = self.ids.name_input.text.strip()
        if not name:
            self.ids.result_label.text = "Введите название блюда."
            return

        try:
            calories = self.parse_float(self.ids.calories_input.text)
            protein = self.parse_float(self.ids.protein_input.text)
            fat = self.parse_float(self.ids.fat_input.text)
            carbs = self.parse_float(self.ids.carbs_input.text)
        except ValueError:
            self.ids.result_label.text = "Калории и БЖУ должны быть числами. Например: 250 или 12.5"
            return

        app = kivy.app.App.get_running_app()
        existed = name in app.foods

        old_data = app.foods.get(name, {})
        app.foods[name] = {
            "last_eaten": old_data.get("last_eaten", 0),
            "calories": calories,
            "protein": protein,
            "fat": fat,
            "carbs": carbs,
            "photo_path": old_data.get("photo_path", ""),
        }
        app.save_data()

        self.ids.result_label.text = (
            f"Обновлено: {name}" if existed else f"Добавлено: {name}"
        )
        self.clear_inputs()

    @staticmethod
    def parse_float(value):
        value = value.strip().replace(",", ".")
        if not value:
            return 0.0
        return float(value)

    def clear_inputs(self):
        self.ids.name_input.text = ""
        self.ids.calories_input.text = ""
        self.ids.protein_input.text = ""
        self.ids.fat_input.text = ""
        self.ids.carbs_input.text = ""


class CameraScreen(Screen):
    camera_widget = None

    def on_pre_enter(self):
        app = kivy.app.App.get_running_app()
        food_name = app.selected_food_for_photo or "блюдо"
        self.ids.camera_title.text = f"Фото: {food_name}"
        self.ids.camera_status.text = "Камера запускается..."
        self.start_camera()

    def on_leave(self):
        self.stop_camera()

    def start_camera(self):
        self.stop_camera()
        kivy.app.App.get_running_app().request_camera_permission()

        try:
            self.camera_widget = Camera(resolution=(720, 720), play=True)
            self.ids.camera_holder.clear_widgets()
            self.ids.camera_holder.add_widget(self.camera_widget)
            self.ids.camera_status.text = "Камера готова. Нажми «Сделать фото»."
        except Exception as exc:
            self.camera_widget = None
            self.ids.camera_holder.clear_widgets()
            self.ids.camera_status.text = f"Не удалось открыть камеру: {exc}"

    def stop_camera(self):
        if self.camera_widget is not None:
            try:
                self.camera_widget.play = False
            except Exception:
                pass
        if hasattr(self, "ids") and "camera_holder" in self.ids:
            self.ids.camera_holder.clear_widgets()
        self.camera_widget = None

    def capture_photo(self):
        app = kivy.app.App.get_running_app()
        food_name = app.selected_food_for_photo

        if not food_name:
            self.ids.camera_status.text = "Блюдо не выбрано."
            return

        if self.camera_widget is None:
            self.ids.camera_status.text = "Камера не запущена."
            return

        photos_dir = Path(app.user_data_dir) / "photos"
        photos_dir.mkdir(parents=True, exist_ok=True)

        safe_name = re.sub(r"[^A-Za-zА-Яа-я0-9_-]+", "_", food_name).strip("_")
        filename = f"{safe_name}_{int(time.time())}.png"
        photo_path = photos_dir / filename

        try:
            self.camera_widget.export_to_png(str(photo_path))
        except Exception as exc:
            self.ids.camera_status.text = f"Фото не сохранено: {exc}"
            return

        app.foods[food_name]["photo_path"] = str(photo_path)
        app.save_data()
        self.ids.camera_status.text = f"Фото сохранено: {filename}"


class FoodRow(BoxLayout):
    food_name = StringProperty("")
    title_text = StringProperty("")
    last_text = StringProperty("")
    macro_text = StringProperty("")
    photo_text = StringProperty("")

    def mark_as_eaten(self):
        app = kivy.app.App.get_running_app()
        app.mark_food_as_eaten(self.food_name)

        screen = app.root.get_screen("list_food")
        screen.refresh()

    def open_camera(self):
        app = kivy.app.App.get_running_app()
        app.selected_food_for_photo = self.food_name
        app.root.current = "camera"


class EmptyRow(BoxLayout):
    pass


class FoodOptionsApp(kivy.app.App):
    def build(self):
        self.title = "Дневник питания"
        self.data_file = Path(self.user_data_dir) / "food_data.json"
        self.selected_food_for_photo = None
        self.foods = {}
        self.history = []
        self.load_data()
        return Builder.load_file("ui.kv")

    def create_default_foods(self):
        result = {}
        base_time = time.time() - len(DEFAULT_FOODS) * 86400

        for index, (name, calories, protein, fat, carbs) in enumerate(DEFAULT_FOODS):
            result[name] = {
                "last_eaten": base_time + index * 60,
                "calories": float(calories),
                "protein": float(protein),
                "fat": float(fat),
                "carbs": float(carbs),
                "photo_path": "",
            }

        return result

    def load_data(self):
        if not self.data_file.exists():
            self.foods = self.create_default_foods()
            self.history = []
            self.save_data()
            return

        try:
            with self.data_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            self.foods = self.create_default_foods()
            self.history = []
            self.save_data()
            return

        foods = data.get("foods", {})
        history = data.get("history", [])

        if not isinstance(foods, dict) or not foods:
            foods = self.create_default_foods()

        if not isinstance(history, list):
            history = []

        self.foods = self.normalize_foods(foods)
        self.history = self.normalize_history(history)

    def normalize_foods(self, foods):
        normalized = {}

        for name, item in foods.items():
            if not isinstance(name, str) or not isinstance(item, dict):
                continue

            normalized[name] = {
                "last_eaten": float(item.get("last_eaten", 0) or 0),
                "calories": float(item.get("calories", 0) or 0),
                "protein": float(item.get("protein", 0) or 0),
                "fat": float(item.get("fat", 0) or 0),
                "carbs": float(item.get("carbs", 0) or 0),
                "photo_path": str(item.get("photo_path", "") or ""),
            }

        return normalized if normalized else self.create_default_foods()

    def normalize_history(self, history):
        normalized = []

        for item in history:
            if not isinstance(item, dict):
                continue

            try:
                normalized.append({
                    "food_name": str(item.get("food_name", "")),
                    "timestamp": float(item.get("timestamp", 0)),
                    "calories": float(item.get("calories", 0)),
                    "protein": float(item.get("protein", 0)),
                    "fat": float(item.get("fat", 0)),
                    "carbs": float(item.get("carbs", 0)),
                })
            except (TypeError, ValueError):
                continue

        return normalized

    def save_data(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "foods": self.foods,
            "history": self.history,
        }

        with self.data_file.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def mark_food_as_eaten(self, food_name):
        if food_name not in self.foods:
            return

        timestamp = time.time()
        food_data = self.foods[food_name]
        food_data["last_eaten"] = timestamp

        self.history.append({
            "food_name": food_name,
            "timestamp": timestamp,
            "calories": float(food_data.get("calories", 0)),
            "protein": float(food_data.get("protein", 0)),
            "fat": float(food_data.get("fat", 0)),
            "carbs": float(food_data.get("carbs", 0)),
        })

        self.save_data()

    def get_today_totals(self):
        current_day = today_key()

        totals = {
            "count": 0,
            "calories": 0.0,
            "protein": 0.0,
            "fat": 0.0,
            "carbs": 0.0,
        }

        for item in self.history:
            if today_key(item.get("timestamp", 0)) != current_day:
                continue

            totals["count"] += 1
            totals["calories"] += float(item.get("calories", 0))
            totals["protein"] += float(item.get("protein", 0))
            totals["fat"] += float(item.get("fat", 0))
            totals["carbs"] += float(item.get("carbs", 0))

        return totals

    def get_today_summary_text(self):
        totals = self.get_today_totals()

        return (
            f"Сегодня: {totals['count']} блюд | "
            f"{format_number(totals['calories'])} ккал | "
            f"Б {format_number(totals['protein'])} г | "
            f"Ж {format_number(totals['fat'])} г | "
            f"У {format_number(totals['carbs'])} г"
        )

    def reset_default_foods(self):
        self.foods = self.create_default_foods()
        self.history = []
        self.save_data()

        if self.root:
            self.root.current = "menu"
            self.root.get_screen("menu").update_summary()

    def request_camera_permission(self):
        if platform != "android":
            return

        try:
            from android.permissions import Permission, request_permissions
            request_permissions([Permission.CAMERA])
        except Exception:
            pass


if __name__ == "__main__":
    FoodOptionsApp().run()
