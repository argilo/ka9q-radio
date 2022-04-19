#!/usr/bin/env python3

import cairo
import math
import socket
import struct
import threading
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GObject


COLORS = []

for i in range(256):
    if i < 20:
        COLORS.append(bytes(reversed([
            0,
            0,
            0,
            0
        ])))
    elif (i >= 20) and (i < 70):
        COLORS.append(bytes(reversed([
            0,
            0,
            0,
            140*(i-20)//50
        ])))
    elif (i >= 70) and (i < 100):
        COLORS.append(bytes(reversed([
            0,
            60*(i-70)//30,
            125*(i-70)//30,
            115*(i-70)//30 + 140
        ])))
    elif (i >= 100) and (i < 150):
        COLORS.append(bytes(reversed([
            0,
            195*(i-100)//50 + 60,
            130*(i-100)//50 + 125,
            255-(255*(i-100)//50)
        ])))
    elif (i >= 150) and (i < 250):
        COLORS.append(bytes(reversed([
            0,
            255,
            255-255*(i-150)//100,
            0
        ])))
    elif i >= 250:
        COLORS.append(bytes(reversed([
            0,
            255,
            255*(i-250)//5,
            255*(i-250)//5
        ])))


class Screen(Gtk.DrawingArea):
    """ This class is a Drawing Area"""
    def __init__(self):
        super(Screen, self).__init__()
        self.connect("draw", self.on_draw)
        self.wf = None
        self.image = cairo.ImageSurface(cairo.Format.RGB24, 1000, 800)

    def tick(self, data):
        self.wf = data
        rect = self.get_allocation()
        if self.get_window():
            self.get_window().invalidate_rect(rect, True)
            return True
        else:
            return False

    def on_draw(self, widget, event):
        self.cr = self.get_window().cairo_create()
        geom = self.get_window().get_geometry()
        self.draw(geom.width, geom.height)


class MyStuff(Screen):
    """This class is also a Drawing Area, coming from Screen."""
    def __init__(self):
        Screen.__init__(self)

    def draw(self, width, height):
        data = self.image.get_data()
        data[4*1000:] = data[:-4*1000]

        if not self.wf:
            return

        for i, bin in enumerate(self.wf):
            color = int(math.log10(bin) * 30 + 30)
            color = min(color, 255)
            color = max(0, color)
            data[4*i:4*(i+1)] = COLORS[color]

        self.cr.set_source_surface(self.image)
        self.cr.paint()


def run(Widget):
    window = Gtk.Window()
    window.connect("destroy", Gtk.main_quit)
    window.set_size_request(1000, 800)
    widget = Widget()

    t = threading.Thread(target=receive_waterfall, args=(widget,))
    t.start()

    widget.show()
    window.add(widget)
    window.present()
    Gtk.main()

    t.join()


def receive_waterfall(da):
    MCAST_GRP = "239.43.210.220"
    MCAST_PORT = 5007
    IS_ALL_GROUPS = False

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if IS_ALL_GROUPS:
        # on this port, receives ALL multicast groups
        sock.bind(('', MCAST_PORT))
    else:
        # on this port, listen ONLY to MCAST_GRP
        sock.bind((MCAST_GRP, MCAST_PORT))
    mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    success = True
    while success:
        data = sock.recv(10240)
        result = struct.unpack("f"*1000, data)
        success = da.tick(result)


run(MyStuff)
