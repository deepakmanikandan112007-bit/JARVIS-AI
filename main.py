
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window

from datetime import datetime
from math import sin, cos, pi, hypot
import ast
import operator
import re

# Voice output
try:
    from plyer import tts
except ImportError:
    tts = None


# ---------------- SETTINGS ----------------

Window.clearcolor = (0.008, 0.018, 0.045, 1)
Window.softinput_mode = "below_target"

CYAN = (0.1, 0.85, 1, 1)
GREEN = (0.2, 1, 0.65, 1)
WHITE = (0.75, 0.9, 1, 1)


# ---------------- REACTOR ----------------

class Reactor(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.angle = 0
        self.tilt = 0.35
        self.zoom = 1
        self.offset_x = 0
        self.offset_y = 0
        self.time = 0

        self.touches = {}
        self.last_distance = None

        self.bind(size=self.redraw, pos=self.redraw)
        Clock.schedule_interval(self.animate, 1 / 30)

    def animate(self, dt):
        self.time += dt
        self.angle += 0.35 * dt
        self.redraw()

    def rotate_3d(self, x, y, z):
        x1 = x*cos(self.angle) + z*sin(self.angle)
        z1 = -x*sin(self.angle) + z*cos(self.angle)
        y2 = y*cos(self.tilt) - z1*sin(self.tilt)
        return x1, y2, z1

    def orbit_point(self, t, r, plane):

        if plane == 0:
            x, y, z = r*cos(t), r*sin(t), 0
        elif plane == 1:
            x, y, z = r*cos(t), 0, r*sin(t)
        elif plane == 2:
            x, y, z = 0, r*cos(t), r*sin(t)
        elif plane == 3:
            x, y, z = r*cos(t), r*sin(t)*0.7, r*sin(t)*0.7
        elif plane == 4:
            x, y, z = r*cos(t)*0.7, r*sin(t), r*cos(t)*0.7
        else:
            x, y, z = r*cos(t)*0.7, r*cos(t)*0.7, r*sin(t)

        return self.rotate_3d(x, y, z)

    def redraw(self, *args):

        self.canvas.clear()

        if self.width <= 0 or self.height <= 0:
            return

        cx = self.center_x + self.offset_x
        cy = self.center_y + self.offset_y
        r = min(self.width, self.height) * 0.31 * self.zoom

        if r <= 0:
            return

        with self.canvas:

            Color(0, 1, 0.5, 0.04)
            Ellipse(
                pos=(cx-r*1.6, cy-r*1.6),
                size=(r*3.2, r*3.2)
            )

            for plane in range(6):

                points = []

                for step in range(181):
                    t = step * 2*pi/180
                    x, y, z = self.orbit_point(t, r, plane)
                    p = 1 + z/(r*5)
                    points.extend([cx+x*p, cy+y*p])

                Color(0, 1, 0.45, 0.12)
                Line(points=points, width=dp(7), joint="round")

                Color(0, 1, 0.55, 0.9)
                Line(points=points, width=dp(1.5), joint="round")

                pt = self.time*(0.8+plane*0.15) % (2*pi)
                x, y, z = self.orbit_point(pt, r, plane)

                Color(0.7, 1, 0.85, 1)
                Ellipse(
                    pos=(cx+x-dp(4), cy+y-dp(4)),
                    size=(dp(8), dp(8))
                )

            core = r*0.38

            Color(0, 1, 0.5, 0.12)
            Ellipse(
                pos=(cx-core*1.5, cy-core*1.5),
                size=(core*3, core*3)
            )

            Color(0, 0.8, 0.5, 0.3)
            Ellipse(
                pos=(cx-core, cy-core),
                size=(core*2, core*2)
            )

            Color(0.1, 1, 0.65, 1)
            Ellipse(
                pos=(cx-core*0.6, cy-core*0.6),
                size=(core*1.2, core*1.2)
            )

            Color(0.8, 1, 0.9, 1)
            Ellipse(
                pos=(cx-core*0.25, cy-core*0.25),
                size=(core*0.5, core*0.5)
            )

    def on_touch_down(self, touch):

        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        touch.grab(self)
        self.touches[touch.uid] = touch.pos

        if len(self.touches) == 2:
            p = list(self.touches.values())
            self.last_distance = hypot(
                p[0][0]-p[1][0],
                p[0][1]-p[1][1]
            )

        elif len(self.touches) == 1:

            cx = self.center_x + self.offset_x
            cy = self.center_y + self.offset_y
            d = hypot(touch.x-cx, touch.y-cy)

            touch.ud["mode"] = (
                "move" if d < min(self.width, self.height)*0.12*self.zoom
                else "rotate"
            )

        return True

    def on_touch_move(self, touch):

        if touch.grab_current is not self:
            return super().on_touch_move(touch)

        self.touches[touch.uid] = touch.pos

        if len(self.touches) >= 2:

            p = list(self.touches.values())
            d = hypot(
                p[0][0]-p[1][0],
                p[0][1]-p[1][1]
            )

            if self.last_distance and self.last_distance > 0:
                self.zoom *= d/self.last_distance
                self.zoom = max(0.5, min(2.5, self.zoom))

            self.last_distance = d

        else:

            if touch.ud.get("mode") == "move":
                self.offset_x += touch.dx
                self.offset_y += touch.dy
            else:
                self.angle += touch.dx*0.025
                self.tilt = max(
                    -2.5,
                    min(2.5, self.tilt+touch.dy*0.018)
                )

        self.redraw()
        return True

    def on_touch_up(self, touch):

        if touch.grab_current is self:

            touch.ungrab(self)
            self.touches.pop(touch.uid, None)

            if len(self.touches) < 2:
                self.last_distance = None

            return True

        return super().on_touch_up(touch)


# ---------------- CALCULATOR ----------------

def calculate(expression):

    expression = expression.strip()

    if len(expression) > 50:
        raise ValueError("Expression too long")

    tree = ast.parse(expression, mode="eval")

    operations = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow
    }

    unary_operations = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg
    }

    def solve(node):

        if isinstance(node, ast.Expression):
            return solve(node.body)

        if isinstance(node, ast.Constant):
            if type(node.value) in (int, float):
                return node.value
            raise ValueError("Invalid number")

        if isinstance(node, ast.BinOp):

            operation = operations.get(type(node.op))

            if operation is None:
                raise ValueError("Invalid operator")

            left = solve(node.left)
            right = solve(node.right)

            if isinstance(node.op, ast.Pow) and abs(right) > 5:
                raise ValueError("Power too large")

            result = operation(left, right)

            if abs(result) > 1000000000:
                raise ValueError("Result too large")

            return result

        if isinstance(node, ast.UnaryOp):

            operation = unary_operations.get(type(node.op))

            if operation is None:
                raise ValueError("Invalid operation")

            return operation(solve(node.operand))

        raise ValueError("Invalid expression")

    return solve(tree)


# ---------------- JARVIS APP ----------------

class JarvisApp(App):

    def build(self):

        self.title = "JARVIS AI"
        self.voice_enabled = True

        root = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(7)
        )

        # HEADER

        header = BoxLayout(
            size_hint_y=None,
            height=dp(48)
        )

        header.add_widget(
            Label(
                text="[b]J.A.R.V.I.S[/b]",
                markup=True,
                font_size="25sp",
                color=CYAN
            )
        )

        self.status_label = Label(
            text="● ONLINE",
            font_size="12sp",
            color=GREEN,
            size_hint_x=0.4
        )

        header.add_widget(self.status_label)
        root.add_widget(header)

        # STATUS CARDS

        info = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            spacing=dp(5)
        )

        for name, value in [
            ("SYSTEM", "READY"),
            ("CORE", "ACTIVE"),
            ("VOICE", "ENABLED")
        ]:

            card = BoxLayout(
                orientation="vertical",
                padding=dp(4)
            )

            with card.canvas.before:
                Color(0.02, 0.12, 0.22, 1)
                card.bg = Rectangle(
                    pos=card.pos,
                    size=card.size
                )

            card.bind(
                pos=lambda w, p: setattr(w.bg, "pos", p),
                size=lambda w, s: setattr(w.bg, "size", s)
            )

            card.add_widget(
                Label(
                    text=name,
                    font_size="10sp",
                    color=CYAN
                )
            )

            card.add_widget(
                Label(
                    text=value,
                    font_size="12sp",
                    color=GREEN
                )
            )

            info.add_widget(card)

        root.add_widget(info)

        root.add_widget(
            Label(
                text="[b]REACTOR CORE[/b]",
                markup=True,
                size_hint_y=None,
                height=dp(25),
                font_size="13sp",
                color=CYAN
            )
        )

        root.add_widget(Reactor(size_hint_y=0.48))

        # TABS

        tabs = TabbedPanel(
            do_default_tab=False,
            tab_width=dp(110),
            size_hint_y=0.30
        )

        chat_tab = TabbedPanelItem(text="AI CHAT")

        chat_box = BoxLayout(
            orientation="vertical",
            padding=dp(7),
            spacing=dp(5)
        )

        self.chat_scroll = ScrollView(do_scroll_x=False)

        self.chat_log = Label(
            text=(
                "JARVIS: System ready.\n"
                "வணக்கம்! உங்கள் கட்டளைக்காக காத்திருக்கிறேன்."
            ),
            color=(0.65, 0.9, 1, 1),
            halign="left",
            valign="top",
            size_hint_y=None
        )

        self.chat_log.bind(
            width=self.update_chat_width,
            texture_size=self.update_chat_height
        )

        self.chat_scroll.add_widget(self.chat_log)
        chat_box.add_widget(self.chat_scroll)
        chat_tab.add_widget(chat_box)
        tabs.add_widget(chat_tab)

        # SYSTEM TAB

        system_tab = TabbedPanelItem(text="SYSTEM")

        system_box = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(5)
        )

        for line in [
            "SYSTEM STATUS       ONLINE",
            "REACTOR CORE        ACTIVE",
            "OFFLINE ENGINE      READY",
            "VOICE ENGINE        PLYER TTS",
            "NETWORK             NOT CONNECTED",
            "AI ENGINE           OFFLINE MODE",
            "VOICE INPUT         GBOARD"
        ]:

            system_box.add_widget(
                Label(
                    text=line,
                    color=CYAN,
                    font_size="12sp"
                )
            )

        system_tab.add_widget(system_box)
        tabs.add_widget(system_tab)

        root.add_widget(tabs)

        # INPUT ROW

        input_row = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            spacing=dp(5)
        )

        self.command = TextInput(
            hint_text="Enter command / கட்டளை...",
            multiline=False,
            font_size="14sp",
            foreground_color=(0.8, 1, 1, 1),
            background_color=(0.02, 0.08, 0.14, 1),
            cursor_color=CYAN,
            size_hint_x=0.55
        )

        mic = Button(
            text="🎙 MIC",
            size_hint_x=0.22,
            background_normal="",
            background_color=(0.0, 0.45, 0.35, 1)
        )

        mic.bind(on_release=self.open_voice_input)

        send = Button(
            text="SEND",
            size_hint_x=0.23,
            background_normal="",
            background_color=(0.0, 0.35, 0.55, 1)
        )

        send.bind(on_release=self.send_command)
        self.command.bind(on_text_validate=self.send_command)

        input_row.add_widget(self.command)
        input_row.add_widget(mic)
        input_row.add_widget(send)

        root.add_widget(input_row)

        return root

    # ---------------- MIC BUTTON FIX ----------------

    def open_voice_input(self, instance):

        self.add_chat(
            "JARVIS: Keyboard voice typing ready. "
            "இப்போது Keyboard MIC அழுத்திப் பேசுங்கள்."
        )

        # Reset focus so Android opens the keyboard again.
        self.command.focus = False

        Clock.schedule_once(
            self.focus_command_input,
            0.35
        )

    def focus_command_input(self, dt):

        self.command.focus = True
        self.command.cursor = (
            len(self.command.text), 0
        )

    # ---------------- VOICE OUTPUT ----------------

    def speak(self, message):

        if not self.voice_enabled or tts is None:
            return

        try:
            tts.speak(message)
        except Exception as error:
            print("TTS Error:", error)

    # ---------------- CHAT DISPLAY ----------------

    def update_chat_width(self, instance, width):
        instance.text_size = (max(0, width-dp(10)), None)

    def update_chat_height(self, instance, size):
        instance.height = size[1] + dp(15)

    def add_chat(self, message):

        self.chat_log.text += "\n\n" + message

        Clock.schedule_once(
            self.scroll_chat_bottom,
            0.1
        )

    def scroll_chat_bottom(self, dt):
        self.chat_scroll.scroll_y = 0

    # ---------------- COMMAND ENGINE ----------------

    def send_command(self, instance):

        message = self.command.text.strip()

        if not message:
            return

        self.add_chat("YOU: " + message)

        reply = self.process_command(message)

        self.add_chat("JARVIS: " + reply)

        self.speak(reply)

        self.command.text = ""
        self.command.focus = False

    def process_command(self, original_message):

        message = original_message.lower().strip()
        now = datetime.now()

        # GREETING

        if any(word in message for word in [
            "hello", "hi", "hey",
            "வணக்கம்", "ஹலோ"
        ]):

            return (
                "Hello! I am JARVIS. "
                "வணக்கம்! நான் உங்கள் JARVIS உதவியாளர்."
            )

        # TIME

        if any(word in message for word in [
            "time", "மணி", "நேரம்"
        ]):

            return (
                "Current time is "
                + now.strftime("%I:%M %p")
            )

        # DATE

        if any(word in message for word in [
            "date", "today", "தேதி", "நாள்"
        ]):

            return (
                "Today's date is "
                + now.strftime("%d-%m-%Y")
            )

        # IDENTITY

        if any(word in message for word in [
            "who are you",
            "your name",
            "உன் பெயர்",
            "நீ யார்"
        ]):

            return "I am JARVIS, your personal assistant."

        # STATUS

        if any(word in message for word in [
            "status", "system",
            "நிலைமை", "சிஸ்டம்"
        ]):

            return (
                "System online. "
                "Reactor active. "
                "Offline engine ready."
            )

        # HELP

        if any(word in message for word in [
            "help", "commands",
            "உதவி", "கட்டளைகள்"
        ]):

            return (
                "Available commands. "
                "Hello. Time. Date. Status. "
                "Calculate 10 plus 20. Help."
            )

        # CALCULATOR

        if (
            message.startswith("calculate ")
            or message.startswith("calc ")
            or message.startswith("கணக்கிடு ")
        ):

            expression = re.sub(
                r"^(calculate|calc|கணக்கிடு)\s*",
                "",
                message
            )

            try:
                result = calculate(expression)
                return "The result is " + str(result)

            except Exception:
                return "Invalid calculation."

        return (
            "Sorry, I don't know this command yet. "
            "Please type help."
        )


# ---------------- RUN ----------------

if __name__ == "__main__":
    JarvisApp().run()
