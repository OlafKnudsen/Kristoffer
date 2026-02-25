# serial_io.py
import threading
import serial


class SerialManager:
    def __init__(self, app, port: str, baud: int = 115200):
        self.app = app
        self.port = port
        self.baud = baud

        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._ser: serial.Serial | None = None

    def start(self) -> None:
        self._ser = serial.Serial(self.port, self.baud, timeout=0.2)
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        if self._ser and self._ser.is_open:
            self._ser.close()

    def send_line(self, text: str) -> None:
        if not self._ser or not self._ser.is_open:
            return
        if not text.endswith("\n"):
            text += "\n"
        self._ser.write(text.encode("utf-8"))

    def _loop(self) -> None:
        assert self._ser is not None, "Serial port lukket"
        while not self._stop.is_set():
            try:
                raw = self._ser.readline()
            except serial.SerialException as e:
                self.app.call_from_thread(
                    self.app.on_serial_error, str(e)
                )
                break

            if not raw:
                continue

            line = raw.decode("utf-8", errors="replace").rstrip("\r\n")

            if line[0] == "<": #da er meldingen status
                #Finner x, y, z:
                i = 0
                number = ""
                pos_array = []
                for k in line:
                    i += 1
                    if k == ":":
                        for symbol in line[i:i+30]:
                            if symbol != "," and symbol != "|":
                                number += symbol
                            elif symbol == "|":
                                pos_array.append(number[:-1])
                                break
                            else:
                                pos_array.append(number[:-1])
                                number = ""
                        break               

                self.app.call_from_thread(self.app.on_status_recieved, pos_array)
                #self.app.call_from_thread(self.app.app_log, line)

            else:    
                self.app.call_from_thread(self.app.on_serial_line, line)