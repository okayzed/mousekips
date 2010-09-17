import gconf
import math
import time
import threading
import traceback

import pango
import cairo
import gobject
import gtk
from gtk import gdk

import Xlib
from Xlib.display import Display
from Xlib import X

import dbus, dbus.glib, dbus.service


GCONF_DIR       = "/apps/mousekips"
LAUNCH_KEY      = "launch"
LAYOUT_KEY      = "%s/layout" % (GCONF_DIR)
MOVEMENT_KEY    = "%s/movement" % (GCONF_DIR)
FONT_NAME_KEY   = "%s/font_name" % (GCONF_DIR)
FONT_SIZE_KEY   = "%s/font_size" % (GCONF_DIR)
BLOCK_HINT_KEY  = "%s/block_hint" % (GCONF_DIR)

DEFAULT_MVMT    = { "h" : "left",
                    "j" : "down",
                    "k" : "up",
                    "l" : "right" }

DEFAULT_MAP     = [ "1234567890",
                    "!@#$%^&*()",
                    "qwertyuiop",
                    "QWERTYUIOP",
                    "asdfghjkl;",
                    "ASDFGHJKL:",
                    "zxcvbnm,./",
                    "ZXCVBNM<>?" ]
FONT_NAME       = "sans"
FONT_SIZE       = 25

class Overlay:
  def __init__(self, keymapping_array):
    self.keymapping_array = keymapping_array
    self.font_name = FONT_NAME
    self.font_size = FONT_SIZE
    self.old_h = None
    self.old_w = None

    self.overlay_window = gtk.Window()
    self.overlay_window.set_decorated(False)
    self.overlay_window.set_keep_above(True)
    self.overlay_window.stick()

    self.drawing_area = gtk.DrawingArea()
    self.drawing_area.connect('configure-event', self.overlay_cb)
    self.drawing_area.connect('expose-event', self.expose_cb)
    self.overlay_window.add(self.drawing_area)

    self.show_block_hint = True

    self.overlay_window.show_all()

  def setup_fonts(self, font_name, font_size):
    if font_name:
      self.font_name = font_name
    if font_size:
      self.font_size = int(font_size)

  def set_block_hint(self, boo):
    self.show_block_hint = boo

  def hide(self):
    print 'Hiding Overlay'
    self.overlay_window.hide()

  def show(self, w, h):
    print 'Showing Overlay'

    if h != self.old_h or w != self.old_w:
      self.reshape_overlay(w, h)

    print "Presenting Overlay"
    self.overlay_window.window.show()
    self.overlay_window.present()
    self.overlay_window.move(0, 0)
    self.overlay_window.window.set_override_redirect(True)
    self.overlay_window.window.move_resize(0, 0, w, h)

  def reshape_overlay(self, w, h):
      print "Rebuilding Overlay"
      self.old_h = h
      self.old_w = w

      self.overlay_bitmap = gtk.gdk.Pixmap(None, w, h, 1)
      cr = self.overlay_bitmap.cairo_create()

      # Clear the self.overlay_bitmap
      cr.set_source_rgb(0, 0, 0)
      cr.set_operator(cairo.OPERATOR_DEST_OUT)
      cr.paint()

      # Draw our shape into the self.overlay_bitmap using cairo
      cr.set_operator(cairo.OPERATOR_OVER)
      # generally width > height, so let's see:
      # 25px looks good on my 1280x800, which is about... 2% of the screen size.
      # Let's do it.
      hf = self.font_size/5.0
      cr.set_font_size(self.font_size)
      h_block = float(h) / len(self.keymapping_array)
      for y in xrange(len(self.keymapping_array)):
        row_width = len(self.keymapping_array[y])
        if row_width == 0:
          continue

        w_block = float(w) / row_width
        for x in xrange(row_width):
          if self.show_block_hint:
            bh_y =  y*h_block
            bh_y += (h_block/2)

            bh_x =  x*w_block
            bh_x += (w_block/2)
            cr.move_to(bh_x, bh_y)
            cr.arc(bh_x, bh_y, 10.0, 0, 2 * math.pi);

            bh_y += self.font_size / 4
            bh_x -= self.font_size / 4
            cr.rectangle(bh_x, bh_y, self.font_size*1.5, self.font_size*1.5)
          else:
            cr.move_to(x * w_block+(w_block/2), y * h_block+(h_block/2))
            layout = cr.create_layout()
            layout.set_text(self.keymapping_array[y][x])
            desc = pango.FontDescription("%s %s" % (self.font_name, self.font_size))
            layout.set_font_description(desc)
            cr.layout_path(layout)
      cr.set_line_width(1.0)
      cr.fill_preserve()
      cr.set_source_rgb(1, 1, 1)
      cr.stroke()

      # Set the window shape
      self.overlay_window.shape_combine_mask(self.overlay_bitmap, 0, 0)

  def overlay_cb(self, win, event):
    return self.build_pixmap(win)

  def build_pixmap(self, win):
    x, y, w, h = win.get_allocation()
    self.pixmap = gtk.gdk.Pixmap(win.window, w, h)
    cr = self.pixmap.cairo_create()

    # Clear the self.overlay_bitmap
    cr.set_source_rgb(0, 0, 0)
    cr.set_operator(cairo.OPERATOR_DEST_OUT)
    cr.paint()

    # Draw our shape into the self.overlay_bitmap using cairo
    cr.set_operator(cairo.OPERATOR_OVER)
    cr.set_source_rgb(0, 0, 0)
    cr.paint()
    # generally width > height, so let's see:
    # 25px looks good on my 1280x800, which is about... 2% of the screen size.
    # Let's do it.
    border_width = 2

    cr.set_font_size(self.font_size)
    h_block = float(h) / len(self.keymapping_array)
    print self.keymapping_array
    for y in xrange(len(self.keymapping_array)):
      row_width = len(self.keymapping_array[y])
      if row_width == 0:
        continue

      w_block = float(w) / row_width
      for x in xrange(row_width):
        fr_y =  y*h_block
        fr_y += (h_block/2)

        fr_x =  x*w_block
        fr_x += (w_block/2)

        # Draw some text
        cr.move_to(fr_x, fr_y)
        layout = cr.create_layout()
        layout.set_text(self.keymapping_array[y][x])
        desc = pango.FontDescription("%s %s" % (self.font_name, self.font_size))
        layout.set_font_description(desc)
        cr.layout_path(layout)

        cr.set_source_rgb(1, 1, 1)
        cr.fill_preserve()
        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(1.0)
        cr.stroke()


  def expose_cb(self, win, event):
    x , y, width, height = event.area
    win.window.draw_drawable(win.get_style().bg_gc[gtk.STATE_NORMAL],
                                self.pixmap, x, y, x, y, width, height)
    return False

  def destroy(self):
    self.overlay_window.destroy()

class KeyPointer:
  def __init__(self):
    self.display = Display ()
    self.screen = self.display.screen()
    self.overlay = None
    self.root = self.screen.root
    self.keymap = gtk.gdk.keymap_get_default()
    self.finish_keyval = gtk.keysyms.Return
    self.finish_keycode = self.keymap.get_entries_for_keyval(self.finish_keyval)[0][0]

    self.setup_movementkeys(DEFAULT_MVMT)
    self.setup_keymapping(DEFAULT_MAP)

    self.init_gconf(GCONF_DIR)
    self.launch_cb()

  def init_gconf(self, app_dir):
    self.gconf = gconf.client_get_default ()
    self.gconf.add_dir (app_dir, gconf.CLIENT_PRELOAD_NONE)
    self.gconf.notify_add (LAYOUT_KEY, self.gconf_cb)
    self.gconf.notify_add (MOVEMENT_KEY, self.gconf_cb)

    self.read_gconf(app_dir)

  def read_gconf(self, app_dir):
    gconf_keymappings = self.gconf.get_list(LAYOUT_KEY, gconf.VALUE_STRING)
    gconf_font_size = self.gconf.get_int(FONT_SIZE_KEY)
    gconf_font_name = self.gconf.get_string(FONT_NAME_KEY)
    gconf_block_hint = self.gconf.get_bool(BLOCK_HINT_KEY)


    keymappings = []
    for line in gconf_keymappings:
      keymappings.append(line.strip())

    self.setup_keymapping(keymappings)
    self.overlay.setup_fonts(gconf_font_name, gconf_font_size)
    self.overlay.set_block_hint(gconf_block_hint)

  def setup_movementkeys(self, mapping_dict):
    self.movement_dict = mapping_dict
    self.movement_keycodes = {}
    for key in mapping_dict:
      keyval = gtk.gdk.unicode_to_keyval(ord(key))
      keycode = self.keymap.get_entries_for_keyval(keyval)[0][0]
      self.movement_keycodes[keycode] = mapping_dict[key]

  def setup_keymapping(self, mapping_array):
    # Map the keys to an x,y pair of where the key falls on the keyboard
    self.keyboard_keyvals = {}
    self.keymapping_array = mapping_array
    self.max_height = len(mapping_array)
    self.max_width = max([ len(x) for x in mapping_array ])
    for y in xrange(len(mapping_array)):
      for x in xrange(len(mapping_array[y])):
        keyval = gtk.gdk.unicode_to_keyval(ord(mapping_array[y][x]))
        self.keyboard_keyvals[keyval] = (x, y)

    if self.overlay:
      self.overlay.destroy()
    self.overlay = Overlay(mapping_array)

  def gconf_cb(self, *args):
    # One of our settings changed, probably should re-read gconf data
    self.read_gconf(GCONF_DIR)

  def launch_cb(self, keybinding=None):
    t = threading.Thread(target=self.handle_screen)
    t.start()

  def handle_screen(self):
    w = self.screen.width_in_pixels
    h = self.screen.height_in_pixels
    gobject.idle_add(self.overlay.show, w, h)
    print 'Grabbing Keyboard Focus'
    key_grab = self.root.grab_keyboard(True, X.GrabModeAsync, X.GrabModeAsync, X.CurrentTime)
    print key_grab
    print 'Placing pointer'
    try:
      self.handle_keypresses()
      self.display.ungrab_keyboard(X.CurrentTime)
      self.display.flush()
      print 'Finished placing pointer'
    except:
      print "Couldn't handle keypresses"
      gtk.main_quit()
    gobject.idle_add(self.overlay.hide)


  def handle_keypress(self, e):
    # Find the coordinates of the key pressed
    # Check if this is a keypress event (not a release or button, etc)
    if e.__class__ is not Xlib.protocol.event.KeyPress:
      print "Not a KeyPress event"
      return
    # Check if this a movement or absolute mapping.
    print "QRS"
    print e.detail, e.state, e.type
    gtk.gdk.threads_enter()
    keyval_tuple = self.keymap.translate_keyboard_state(e.detail, e.state, e.type)
    gtk.gdk.threads_leave()
    print "LMNO"
    keyval, group, level, modifiers = keyval_tuple
    print keyval
    print "HIJ"
    keycode = e.detail
    print "DEF"
    state = e.state
    print "ABC"

    if keyval not in self.keyboard_keyvals and \
       keycode not in self.movement_keycodes:
      print "Keycode and keyval not in dictionary"
      return e.detail == self.finish_keycode

    w = self.screen.width_in_pixels
    h = self.screen.height_in_pixels
    print "012"
    # Find out if there are any modifiers being pressed
    # If ctrl + movement key is being pressed, move over by some amount
    if state & X.ControlMask and keycode in self.movement_keycodes:
      print "Control Hold Movement Keys"
      movement = self.movement_keycodes[keycode]
      # move the cursor a little
      # Not sure how to calculate the amount to move by?
      # Maybe take the smallest h_block, w_block we have and divide into thirds?
      h_block = float(h) / self.max_height / 3
      w_block = float(w) / self.max_width / 3

      cursor_position = self.root.query_pointer()
      x = cursor_position.root_x
      y = cursor_position.root_y
      to_x, to_y = x, y
      if movement == 'left':
        to_x = x - w_block
      if movement == 'down':
        to_y = y + h_block
      if movement == 'up':
        to_y = y - w_block
      if movement == 'right':
        to_x = x + w_block
    else:
      print 'Moving Pointer'
      x, y = self.keyboard_keyvals[keyval]
      h_block = float(h) / len(self.keymapping_array)
      w_block = float(w) / len(self.keymapping_array[y])
    # divide the width by the number of rows we have and multiply by x to
    # figure out where the cursor goes

      to_x = w_block * x + (w_block / 2)
      to_y = h_block * y + (h_block / 2)

    print to_x, to_y
    self.root.warp_pointer(to_x, to_y)
    return e.detail == self.finish_keycode

  def handle_keypresses(self):
    self.root.change_attributes(event_mask = X.KeyPressMask)
    self.screen = self.display.screen()

    while True:
      print "Handling Keyboard Event"
      event = self.root.display.next_event()
      print event
      try:
        if self.handle_keypress(event):
          break
      except Exception, e:
        traceback.print_exc()
        break
    self.root.change_attributes(event_mask = X.NoEventMask)
    self.display.allow_events(X.AsyncKeyboard, X.CurrentTime)

class Server (dbus.service.Object):
    def __init__(self, *args, **kwargs):
      self.kp = KeyPointer()
      dbus.service.Object.__init__(self, *args, **kwargs)

    @dbus.service.method(dbus_interface='mousekips.Events',
                         in_signature='', out_signature='')
    def show (self):
        self.kp.launch_cb()
        return

class InstanceManager:
  def __init__(self):
    gtk.gdk.threads_init()
    self.bus = dbus.SessionBus()

  def start_server(self):
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    name = dbus.service.BusName('mousekips.Server', bus=self.bus)
    obj = Server(name, '/')
    loop = gobject.MainLoop()
    print 'Listening'
    loop.run()

  def call_server(self):
    server = dbus.Interface(self.bus.get_object('mousekips.Server', '/'),
                            'mousekips.Events')
    server.show()


  def run(self):
    try:
      self.bus.get_name_owner('mousekips.Server')
      # There is already a mousekips instance running, let's get it to show
      # itself
      self.call_server()
    except dbus.exceptions.DBusException:
      self.start_server()

if __name__ == "__main__":
  im = InstanceManager()
  im.run()



