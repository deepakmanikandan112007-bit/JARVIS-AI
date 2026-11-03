
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, Line
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from math import sin, cos, pi, hypot

# Android Native Text-to-Speech
from jnius import autoclass, PythonJavaClass, java_method
from android.runnable import run_on_ui_thread

Window.clearcolor = (0.005, 0.012, 0.012, 1)


class TTSListener(PythonJavaClass):

    __javainterfaces__ = [
        'android/speech/tts/TextToSpeech$OnInitListener'
    ]
    __javacontext__ = 'app'

    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method('(I)V')
    def onInit(self, status):
        self.app.tts_ready = (status == 0)

        if self.app.tts_ready:
            try:
                Locale = autoclass('java.util.Locale')
                self.app.tts_engine.setLanguage(Locale.US)
                print("JARVIS TTS READY")
            except Exception as e:
                print("TTS Language Error:", e)


class Reactor(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.angle = 0.0
        self.tilt = 0.35
        self.zoom = 1.0

        self.offset_x = 0
        self.offset_y = 0

        self.time = 0
        self.auto_speed = 0.35

        self.touches = {}
        self.last_distance = None

        Clock.schedule_interval(self.animate, 1 / 30)

    def animate(self, dt):
        self.time += dt
        self.angle += self.auto_speed * dt
        self.redraw()

    def rotate_3d(self, x, y, z):

        x1 = x * cos(self.angle) + z * sin(self.angle)
        z1 = -x * sin(self.angle) + z * cos(self.angle)

        y2 = y * cos(self.tilt) - z1 * sin(self.tilt)
        z2 = y * sin(self.tilt) + z1 * cos(self.tilt)

        return x1, y2, z2

    def get_orbit_point(self, t, radius, plane):

        if plane == 0:
            x = radius * cos(t)
            y = radius * sin(t)
            z = 0

        elif plane == 1:
            x = radius * cos(t)
            y = 0
            z = radius * sin(t)

        elif plane == 2:
            x = 0
            y = radius * cos(t)
            z = radius * sin(t)

        elif plane == 3:
            x = radius * cos(t)
            y = radius * sin(t) * 0.7
            z = radius * sin(t) * 0.7

        elif plane == 4:
            x = radius * cos(t) * 0.7
            y = radius * sin(t)
            z = radius * cos(t) * 0.7

        else:
            x = radius * cos(t) * 0.7
            y = radius * cos(t) * 0.7
            z = radius * sin(t)

        return self.rotate_3d(x, y, z)

    def redraw(self):

        self.canvas.clear()

        cx = self.center_x + self.offset_x
        cy = self.center_y + self.offset_y

        radius = min(self.width, self.height) * 0.31
        radius *= self.zoom

        with self.canvas:

            Color(0, 1, 0.5, 0.04)
            Ellipse(
                pos=(cx - radius * 1.6, cy - radius * 1.6),
                size=(radius * 3.2, radius * 3.2)
            )

            for plane in range(6):

                points = []

                for step in range(181):

                    t = step * 2 * pi / 180

                    x, y, z = self.get_orbit_point(
                        t, radius, plane
                    )

                    perspective = 1 + z / (radius * 5)

                    px = cx + x * perspective
                    py = cy + y * perspective

                    points.extend([px, py])

                Color(0, 1, 0.45, 0.12)
                Line(
                    points=points,
                    width=dp(7),
                    joint="round"
                )

                Color(0, 1, 0.55, 0.85)
                Line(
                    points=points,
                    width=dp(1.5),
                    joint="round"
                )

                particle_t = (
                    self.time * (0.8 + plane * 0.15)
                ) % (2 * pi)

                px, py, pz = self.get_orbit_point(
                    particle_t, radius, plane
                )

                Color(0.65, 1, 0.85, 1)

                Ellipse(
                    pos=(
                        cx + px - dp(4),
                        cy + py - dp(4)
                    ),
                    size=(dp(8), dp(8))
                )

            core = radius * 0.38

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
            return False

        touch.grab(self)
        self.touches[touch.uid] = touch.pos

        if len(self.touches) == 2:

            positions = list(self.touches.values())

            self.last_distance = hypot(
                positions[0][0] - positions[1][0],
                positions[0][1] - positions[1][1]
            )

        elif len(self.touches) == 1:

            cx = self.center_x + self.offset_x
            cy = self.center_y + self.offset_y

            distance = hypot(
                touch.x - cx,
                touch.y - cy
            )

            core_radius = (
                min(self.width, self.height)
                * 0.12 * self.zoom
            )

            if distance < core_radius:
                touch.ud["mode"] = "move"
            else:
                touch.ud["mode"] = "rotate"

        return True

    def on_touch_move(self, touch):

        if touch.grab_current is not self:
            return super().on_touch_move(touch)

        self.touches[touch.uid] = touch.pos

        if len(self.touches) >= 2:

            positions = list(self.touches.values())

            distance = hypot(
                positions[0][0] - positions[1][0],
                positions[0][1] - positions[1][1]
            )

            if self.last_distance is not None:
                if self.last_distance > 0:

                    factor = distance / self.last_distance

                    self.zoom *= factor
                    self.zoom = max(0.5, min(self.zoom, 2.5))

            self.last_distance = distance
            self.redraw()

            return True

        dx = touch.dx
        dy = touch.dy

        mode = touch.ud.get("mode")

        if mode == "rotate":

            self.angle += dx * 0.025
            self.tilt += dy * 0.018

            self.tilt = max(-2.5, min(self.tilt, 2.5))

        elif mode == "move":

            self.offset_x += dx
            self.offset_y += dy

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


class JarvisApp(App):

    def build(self):

        self.tts_engine = None
        self.tts_listener = None
        self.tts_ready = False

        main = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(8)
        )

        title = Label(
            text="[b]J.A.R.V.I.S[/b]",
            markup=True,
            font_size="32sp",
            color=(0, 1, 0.6, 1),
            size_hint_y=0.12
        )

        status = Label(
            text="ARTIFICIAL INTELLIGENCE SYSTEM",
            font_size="12sp",
            color=(0.2, 0.9, 0.7, 1),
            size_hint_y=0.06
        )

        reactor = Reactor(size_hint=(1, 0.68))

        activate = Button(
            text="ACTIVATE JARVIS",
            size_hint=(1, 0.12),
            background_normal="",
            background_color=(0, 0.35, 0.2, 1),
            color=(0.5, 1, 0.8, 1),
            font_size="18sp"
        )

        activate.bind(on_press=self.activate_jarvis)

        main.add_widget(title)
        main.add_widget(status)
        main.add_widget(reactor)
        main.add_widget(activate)

        Clock.schedule_once(self.initialize_tts, 1)

        return main

    @run_on_ui_thread
    def initialize_tts(self, dt):

        try:
            PythonActivity = autoclass(
                'org.kivy.android.PythonActivity'
            )

            TextToSpeech = autoclass(
                'android.speech.tts.TextToSpeech'
            )

            activity = PythonActivity.mActivity

            self.tts_listener = TTSListener(self)

            self.tts_engine = TextToSpeech(
                activity,
                self.tts_listener
            )

            print("JARVIS TTS INITIALIZING")

        except Exception as e:
            print("TTS Initialization Error:", e)

    @run_on_ui_thread
    def activate_jarvis(self, instance):

        message = "Hello. I am Jarvis. How can I help you?"

        try:
            if self.tts_engine is not None and self.tts_ready:

                TextToSpeech = autoclass(
                    'android.speech.tts.TextToSpeech'
                )

                self.tts_engine.speak(
                    message,
                    TextToSpeech.QUEUE_FLUSH,
                    None
                )

                print("JARVIS SPEAKING")

            else:
                print("JARVIS TTS IS NOT READY")

        except Exception as e:
            print("Voice Error:", e)


if __name__ == "__main__":
    JarvisApp().run()
        
