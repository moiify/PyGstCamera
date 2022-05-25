#!/usr/bin/env python

import sys, os, time
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, Gtk

class GTK_Main:
    def __init__(self):
        window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        window.set_title("MyCamera-Viewer")
        window.set_default_size(600, 650)
        window.connect("destroy", Gtk.main_quit, "WM destroy")
        vbox = Gtk.VBox()
        window.add(vbox)
        window.set_resizable(False)
        self.movie_window = Gtk.DrawingArea()
        vbox.add(self.movie_window)
        hbox = Gtk.HBox()
        vbox.pack_start(hbox, False, False, 0)
        hbox.set_border_width(10)
        hbox.pack_start(Gtk.Label(), False, False, 0)

        self.button = Gtk.Button("Shot")
        self.button.connect("clicked", self.do_shot)
        hbox.pack_start(self.button, False, False, 0)

        self.button1 = Gtk.Button("Record")
        self.button1.connect("clicked", self.do_record)
        hbox.pack_start(self.button1, False, False, 0)

        self.button2 = Gtk.Button("Quit")
        self.button2.connect("clicked", self.exit)
        hbox.pack_start(self.button2, False, False, 0)


        hbox.add(Gtk.Label())
        window.show_all()

        # Set up the gstreamer pipeline
        self.player = Gst.parse_launch ("v4l2src device=/dev/video1 io-mode=4 ! videoconvert ! video/x-raw,format=NV12,width=576,height=432 ! rkximagesink")
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)
        bus.connect("sync-message::element", self.on_sync_message)
        
        self.player.set_state(Gst.State.PLAYING)

    def do_record(self, w):
        global recordplayer
        if self.button1.get_label() == "Record":
            self.button1.set_label("Stop")
            recordplayer = Gst.parse_launch ("v4l2src device=/dev/video0 num-buffers=100 ! video/x-raw,format=NV12,width=864,height=648,framerate=30/1 ! videoconvert ! mpph264enc ! h264parse ! mp4mux ! filesink location=/home/linaro/Videos/h264.mp4")
            recordplayer.set_state(Gst.State.PLAYING)
        else:
            recordplayer.set_state(Gst.State.NULL)
            self.button1.set_label("Record")

    def do_shot(self, w):
        player = Gst.parse_launch ("v4l2src device=/dev/video0 num-buffers=1 ! video/x-raw,format=NV12,width=864,height=648 ! mppjpegenc ! multifilesink location=/home/linaro/Pictures/test%01d.jpg")
        player.set_state(Gst.State.PLAYING)

    def exit(self, widget, data=None):
        Gtk.main_quit()

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.player.set_state(Gst.State.NULL)
            self.button.set_label("Start")
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print ("Error: %s" % err, debug)
            self.player.set_state(Gst.State.NULL)
            self.button.set_label("Start")

    def on_sync_message(self, bus, message):
        struct = message.get_structure()
        if not struct:
            return
        message_name = struct.get_name()
        if message_name == "prepare-xwindow-id":
            # Assign the viewport
            imagesink = message.src
            imagesink.set_property("force-aspect-ratio", True)
            imagesink.set_xwindow_id(self.movie_window.window.xid)

Gst.init(None)
GTK_Main()
GObject.threads_init()
Gtk.main()