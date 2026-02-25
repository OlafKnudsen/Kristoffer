from time import monotonic
from textual.app import App
from textual.events import Key
from textual.widgets import Static


class MyApp(App):
    CSS = """
    Screen { background: black; }
    Screen.held { background: green; }
    """

    LONG_PRESS_TIME = 0.5          # seconds until we consider it a "long press"
    RELEASE_GAP = 0.20             # seconds without repeats => treat as released
    CHECK_INTERVAL = 0.05          # poll rate

    def compose(self):
        yield Static("Tap SPACE = prints 'tap'. Hold SPACE = screen green while held.")

    def on_mount(self) -> None:
        self._pressed = False
        self._long_active = False
        self._press_started_at = 0.0
        self._last_key_seen_at = 0.0

        self._long_timer = None
        self.set_interval(self.CHECK_INTERVAL, self._check_release)

    def on_key(self, event: Key) -> None:
        if event.key != "space":
            return

        event.prevent_default()
        now = monotonic()

        # First press
        if not self._pressed:
            self._pressed = True
            self._press_started_at = now
            self._long_active = False

            # Start long-press timer
            self._long_timer = self.set_timer(self.LONG_PRESS_TIME, self._on_long_press)

        # Any key event (press or repeat) updates "last seen"
        self._last_key_seen_at = now

    def _on_long_press(self) -> None:
        # Only activate if still pressed
        if self._pressed and not self._long_active:
            self._long_active = True
            self.screen.add_class("held")  # <-- this is the crucial part

    def _check_release(self) -> None:
        if not self._pressed:
            return

        now = monotonic()

        # If we haven't seen repeats recently, assume release
        if (now - self._last_key_seen_at) >= self.RELEASE_GAP:
            # Stop pending long-press timer if it hasn't fired
            if self._long_timer is not None:
                self._long_timer.stop()
                self._long_timer = None

            if self._long_active:
                # End long-hold visual state
                self.screen.remove_class("held")
            else:
                # It was a tap
                self.log("tap")

            # Reset state
            self._pressed = False
            self._long_active = False


if __name__ == "__main__":
    MyApp().run()

