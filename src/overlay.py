import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

import threading
import requests
import logging

logger = logging.getLogger(__name__)

PORT = 36000
STEP = 5
BASE = f"http://127.0.0.1:{PORT}"

CSS = b"""
window {
    background-color: #ffffff;
    border: 1px solid #d0d7e2;
    border-radius: 12px;
}
.title-label {
    color: #0078d4;
    font-weight: bold;
    font-size: 13px;
}
.angle-label {
    color: #0078d4;
    font-size: 26px;
    font-weight: bold;
}
.tilt-btn {
    background: #f0f2f5;
    border: 1px solid #d0d7e2;
    border-radius: 8px;
    padding: 10px;
    font-size: 13px;
    font-weight: 600;
    color: #1a1a2a;
    box-shadow: none;
}
.tilt-btn:hover {
    background: #e4eaf3;
    border-color: #0078d4;
}
.tilt-btn:active {
    background: #d0dced;
}
.level-btn {
    background: #f0f2f5;
    border: 1px solid #d0d7e2;
    border-radius: 8px;
    padding: 7px;
    font-size: 12px;
    color: #6b7280;
    box-shadow: none;
}
.level-btn:hover {
    border-color: #0078d4;
    color: #0078d4;
}
"""


class KinectOverlay(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.set_title("KinectCam")
        self.set_keep_above(True)
        self.set_resizable(False)
        self.set_decorated(False)
        self.set_default_size(170, -1)

        # Apply CSS
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self._tilt = 0

        # Drag support (no title bar)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect("button-press-event", self._on_drag)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        outer.set_margin_top(14)
        outer.set_margin_bottom(14)
        outer.set_margin_start(14)
        outer.set_margin_end(14)
        self.add(outer)

        # Title row
        title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        title_row.set_halign(Gtk.Align.CENTER)
        icon = Gtk.Label(label="⬤")
        icon.get_style_context().add_class("title-label")
        title = Gtk.Label(label="KinectCam")
        title.get_style_context().add_class("title-label")
        title_row.pack_start(icon, False, False, 0)
        title_row.pack_start(title, False, False, 0)
        outer.pack_start(title_row, False, False, 0)

        outer.pack_start(Gtk.Separator(), False, False, 10)

        # Up button
        self._btn_up = Gtk.Button(label="▲  Up")
        self._btn_up.get_style_context().add_class("tilt-btn")
        self._btn_up.connect("clicked", self._on_up)
        outer.pack_start(self._btn_up, False, False, 0)

        # Angle display
        self._angle_label = Gtk.Label(label="0°")
        self._angle_label.get_style_context().add_class("angle-label")
        self._angle_label.set_margin_top(6)
        self._angle_label.set_margin_bottom(6)
        outer.pack_start(self._angle_label, False, False, 0)

        # Down button
        self._btn_down = Gtk.Button(label="▼  Down")
        self._btn_down.get_style_context().add_class("tilt-btn")
        self._btn_down.connect("clicked", self._on_down)
        outer.pack_start(self._btn_down, False, False, 0)

        outer.pack_start(Gtk.Label(label=""), False, False, 2)

        # Level button
        btn_level = Gtk.Button(label="Level")
        btn_level.get_style_context().add_class("level-btn")
        btn_level.connect("clicked", self._on_level)
        outer.pack_start(btn_level, False, False, 0)

        self.show_all()

        # Poll state every 1.5s
        GLib.timeout_add(1500, self._poll)

    def _on_drag(self, widget, event):
        if event.button == 1:
            self.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)

    def _poll(self):
        def fetch():
            try:
                state = requests.get(f"{BASE}/api/state", timeout=1).json()
                GLib.idle_add(self._set_angle, state["tilt"])
            except Exception:
                pass
        threading.Thread(target=fetch, daemon=True).start()
        return True

    def _set_angle(self, tilt):
        self._tilt = float(tilt)
        self._angle_label.set_text(f"{int(self._tilt)}°")

    def _send_tilt(self, angle):
        angle = max(-30, min(30, angle))
        def post():
            try:
                requests.post(f"{BASE}/api/tilt", json={"angle": angle}, timeout=1)
                GLib.idle_add(self._set_angle, angle)
            except Exception:
                pass
        threading.Thread(target=post, daemon=True).start()

    def _on_up(self, _):
        self._send_tilt(self._tilt + STEP)

    def _on_down(self, _):
        self._send_tilt(self._tilt - STEP)

    def _on_level(self, _):
        self._send_tilt(0)


def main():
    win = KinectOverlay()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    main()
