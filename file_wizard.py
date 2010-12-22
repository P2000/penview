impl = "tkinter"
try:
    import gtk
    impl = "gtk"
except:
    from Tkinter import *
    from tkFileDialog import *

from itertools import count

from penview import *
from data_import import *
from penview_model import *

class OpenWizard:

    xi = count()
    examples = (
                'examples/Chaotische Schwingung (Chaos4).sqlite',
                'examples/Doppelte nicht- Chaotische Schwingung (Chaos3.6).sqlite',
                'examples/abklingkonstante.sqlite',
                'examples/eigenfrequenz_chaos2.sqlite',
                'examples/motorkalibrierung.sqlite',
    )

    @classmethod
    def get_path(cls):
        if debug_flag:
            return cls.examples[cls.xi.next()]

        return askopenfilename(filetypes=(("Experiment Files", "*.sqlite"),))
    
    @classmethod
    def open_experiment(cls):
        return OpenExperiment(ExperimentFile(cls.get_path()))

class ImportWizard:

    xi = count()
    examples = 'examples/Abklingkonstante.csv'

    @classmethod
    def get_csv_path(cls):
        if debug_flag:
            return cls.examples[cls.xi.next()]

        return askopenfilename(filetypes=(("CSV Files", "*.csv"),))
    
    @classmethod
    def get_experiment_path(cls):
        if debug_flag:
            return cls.examples[cls.xi] + ".imported.sqlite"

        return asksaveasfilename(filetypes=(("Experiment Files", "*.sqlite"),))
    
    @classmethod
    def open_experiment(cls):
        csv = CSVImporter(cls.get_csv_path())
        ex_file = ExperimentFile(cls.get_experiment_path(), csv.rowsize-1)
        
        ex_file.store_values(1, csv.values)
        ex_file.store_metadata(csv.metadata)
        
        return OpenExperiment(ex_file)

if impl == "gtk":

    gtk.gdk.threads_init()

    def askopenfilename(filetypes):
        dialog = gtk.FileChooserDialog("Open..", None,
                                       gtk.FILE_CHOOSER_ACTION_OPEN,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        return _run_dialog(dialog, filetypes)

    def asksaveasfilename(filetypes):
        dialog = gtk.FileChooserDialog("Save..", None,
                                       gtk.FILE_CHOOSER_ACTION_SAVE,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        ret = _run_dialog(dialog, filetypes)
        if ret and not ret.endswith(".sqlite"):
            ret += ".sqlite"
        return ret

    def _run_dialog(dialog, filetypes):
        filter = gtk.FileFilter()
        filter.set_name(filetypes[0][0])
        filter.add_pattern(filetypes[0][1])
        dialog.add_filter(filter)
        dialog.set_default_response(gtk.RESPONSE_OK)

# aaaw on
#
# urk - this took a bit long (~10hrs)
#
# initial problems because of metacity (the gnome window manager) focus-stealing-prevention kicking in:
#  starting from the second time selecting creating an open/save dialog, it was not focused initially under ubuntu lucid (10.04)
#  (at least not with gconf:/apps/metacity/general/focus_mode set to "sloppy")
#
# salvation came through studying metacity source code, running metacity in debug/verbose mode
# ("$ METACITY_VERBOSE=1 METACITY_USE_LOGFILE=1 metacity --replace"), reading delelopper mailing list threads etc...
#
# verbose mode revealed that the problem is provoked by some code in http://git.gnome.org/browse/metacity/tree/src/core/window.c#n1904
# in intervening_user_event_occurred() (line 1905: ... "focus prevented by other activity" ...):
#  i assume that "import gtk" causes the creation of a hidden window which records a timestamp for user activity in any gtk window
#  this timestamp is not updated any after the first gtk_file_cooser dialog is closed (because there are no other visible gtk windows)
#  when metacity initially maps a NEW window on the screen, it checks if there was any user activity the CURRENTLY focused window AFTER
#  the application mapping the new window was started OR has seen user any activity
#  because the application (the gtk tooklit) was started (import gtk) long time back and the last user activity was also recorded
#  BEFORE the the last user activity in the CURRENT application (tkinter) was recorded, it decides that this is a case where
#  focus-stealing-preventionshould kick in and doesn't activate/focus/raise the new dialog window. In fact it will be a "case 1)", as
#  described here: http://git.gnome.org/browse/metacity/tree/doc/how-to-get-focus-right.txt#n58
#
# some references:
#  on focus-stealing-prevention:
#   - http://standards.freedesktop.org/wm-spec/latest/ar01s05.html#id2569834
#   - http://git.gnome.org/browse/metacity/plain/doc/how-to-get-focus-right.txt
#  on the gtk methods used to circumvent the problem:
#   - http://www.pygtk.org/docs/pygtk/class-gtkwidget.html#method-gtkwidget--realize
#   - http://www.pygtk.org/docs/pygtk/class-gtkwidget.html#method-gtkwidget--get-window
#   - http://www.pygtk.org/docs/pygtk/class-gdkwindow.html#method-gdkwindow--property-change
#
        dialog.realize()
        dialog.get_window().property_delete("_NET_WM_USER_TIME")
        dialog.get_window().property_delete("_NET_WM_USER_TIME_WINDOW")
#
# aaaw off
        
        ret = None
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            ret = dialog.get_filename()
        dialog.hide()
        while gtk.events_pending():
            gtk.main_iteration()
        return ret
