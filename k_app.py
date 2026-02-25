from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup
from textual.reactive import reactive
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import Digits, Static, Label, Log, Button, ListItem, ListView
from serial_io import SerialManager

#Widgets:
class PosDisplay(Digits):
    position = reactive("0.000")

    def update_position(self, pos):
        self.position = pos

    def watch_position(self, position):
        self.update(position)

class AxisDisplay(HorizontalGroup):  
    def __init__(self, axis:str):
        self.axis = axis
        super().__init__()
        
    def _on_mount(self):
        self.border_title = self.axis
        #self.border_subtitle = "feedrate: 100"

    def update_axis(self, pos):
        posdisplay = self.query_one(PosDisplay)
        posdisplay.update_position(pos)

    def compose(self):
        yield PosDisplay("0.000")
        #yield Label("mm", id = "mm")
        #yield Button(("zero " + self.axis), id = "zero")

class SerialDisplay(Log):
    def _on_mount(self):
        self.max_lines = None

class StatusBar(HorizontalGroup):
    def compose(self):
        yield(Label("status", classes = "statusitem"))
        yield(Label("feedrate: 100 mm/s", classes = "statusitem"))
        yield(Label("feed distanse: 1 mm", classes = "statusitem"))

class Meny(ListView):
    def compose(self):
        yield ListItem(Label("Zero x"))
        yield ListItem(Label("Zero y"))
        yield ListItem(Label("Zero z"))
        yield ListItem(Label("Set feedrate"))
        yield ListItem(Label("Menyknapp 5"))
        yield ListItem(Label("Menyknapp 6"))
        yield ListItem(Label("Menyknapp 7"))
        yield ListItem(Label("Menyknapp 8"))
        yield ListItem(Label("Menyknapp 9"))
    
    def _on_mount(self):
        self._handlers = [
            self._zero_x,
            self._zero_y,
            self._zero_z,
            self._set_feedrate
        ]

    def on_list_view_selected(self, event: ListView.Selected):
        index = event.index
        try:
            handler = self._handlers[index]
        except IndexError:
            return
        handler()

    def _zero_x(self):
        self.app.app_log("Nuller ut x aksen")
   
    def _zero_y(self):
        self.app.app_log("Nuller ut y aksen")
   
    def _zero_z(self):
        self.app.app_log("Nuller ut z aksen")

    def _set_feedrate(self):
        self.app.push_screen(FeedrateScreen())

class FeedDisplay(Digits):
    def _on_mount(self):
        self.feed = reactive(self.app.jog_feed)

    def watch_feed(self, feed):
        self.update(feed)

#Screens:
class FeedrateScreen(ModalScreen[int]):
    BINDINGS = [
        ("up", "increase_feed", "øk"),
        ("down", "decrease_feed", "synk"),
        ("enter", "app.pop_screen", "fjern skjerm")
        ]

    def compose(self):
        yield Digits(self.app.jog_feed, id = "feedrate")

    def action_increase_feed(self):
        display = self.query_one(Digits)
        current = int(display.value)
        display.update(str(current + 100))

    def action_decrease_feed(self):
        display = self.query_one(Digits)
        current = int(display.value)
        display.update(str(current - 100))



#Main app:
class KristofferApp(App):
    CSS_PATH = "k_styles.tcss"

    def __init__(self, port: str, **kwargs):
        super().__init__(**kwargs)
        self.serial = SerialManager(self, port = port)
        self.jog_feed = "100"
        self.jog_distance = "1"
        self.long_press_time = 0.25
        self.is_long_press = False
        self.released = True

    #Widgets:
    def compose(self):
        yield AxisDisplay("X")
        yield Meny()
        yield AxisDisplay("Y")
        yield AxisDisplay("Z")
        yield StatusBar()
        yield SerialDisplay()


    #Oppstart:
    def _on_mount(self):
        self.theme = "gruvbox"
        self.serial.start()
        self.app_log("Serial startet")
        self.serial.send_line("$Report/Interval=150")
        self.axis_displays = list(self.query(AxisDisplay))
        
        

    #Hjelpefunksjon for å skrive til appen. Kan ikke hete bare "log"
    def app_log(self, text: str) -> None:
        self.query_one(SerialDisplay).write_line(text)

    #Keyboard input:
    def on_key(self, event: Key) -> None:
        key = event.key

        if key == "r":
                self.released = True

                if self.is_long_press:
                    self.serial.send_line("!")
                    self.is_long_press = False

        if key in ["x", "y", "z", "a", "b", "c"]:
            #Jog input, håndter det riktig:
            if self.released:
                self.released = False
                self.set_timer(self.long_press_time, lambda: self.handle_jog(key))

        elif key == "i":
            self.app_log("?")
            self.serial.send_line("?")
        elif key == "escape":
            self.app_log("$Bye")
            self.serial.send_line("$Bye")


    def handle_jog(self, key):
        self.app_log("Dette funker")

        if self.released:
            self.jog(key, self.jog_distance, self.jog_feed)
        else:
            self.is_long_press = True
            self.jog(key, "1000", self.jog_feed)

    def jog(self, key, jog_distance, jog_feed):
        if key == "a":
            move = "$J=G91 x-" + jog_distance + " F" + jog_feed

        elif key == "b":
            move = "$J=G91 y-" + jog_distance + " F" + jog_feed
            
        elif key == "c":
            move = "$J=G91 z-" + jog_distance + " F" + jog_feed
            
        else:
            move = "$J=G91 " + key + jog_distance + " F" + jog_feed

        self.app_log(move)
        self.serial.send_line(move)           

    #Serialgreier
    def on_serial_line(self, line):
        self.app_log(line) 

    def on_serial_error(self, e):
        self.app_log(e)      

    def on_status_recieved(self, status_list: list):
        i = 0
        for axis_position in status_list:
            self.axis_displays[i].update_axis(axis_position)
            i += 1

#Kjør app:
if __name__ == "__main__":
    app = KristofferApp(port = "COM6")
    app.run()




