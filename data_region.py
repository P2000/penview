# encoding: utf-8

from Tkinter import *
from itertools import chain
from functools import partial

from penview import *
from recipe_52266 import MultiListbox

class DataRegion(Frame):
    def __init__(self, parent, pvconf, ctrl):
        Frame.__init__(self, parent)

        self.conf = pvconf
        self.controller = ctrl

        pvconf.add_viewmode_listener(self.viewmode_update)

        self.controls_region = PlotControls(self, self.conf)
        self.plot_region = ScrollRegion(self)

        self.xy_plot = XYPlot(pvconf, self.plot_region, 800, 600)
        self.xy_plot.pack(fill=BOTH, expand=1)

#        self.table_region = PVTable(self, self.conf)

    def show_table(self):
        raise Exception("Sorry, table view is not yet implemented")

        self.plot_region.pack_forget()          # FIXME: on the first call the widgets are not yet packed
        self.controls_region.pack_forget()

        self.table_region.pack(fill=BOTH, expand=YES)

    def show_plot(self):
#        self.table_region.pack_forget()          # FIXME: on the first call the widget is not yet packed

        # urk - use the pack-regions-that-should-stay-visible-on-window-resize-first hack
        self.controls_region.pack(side=BOTTOM, fill=X, expand=0)
        self.plot_region.pack(fill=BOTH, expand=1)

    def viewmode_update(self, conf):
        show = { XYPlot: self.show_plot,
                 PVTable: self.show_table}
        show[conf.viewmode]()

class ScrollRegion(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.xscrollbar = Scrollbar(self, orient=HORIZONTAL)
        self.yscrollbar = Scrollbar(self, orient=VERTICAL)
        self.xscrollbar.grid(row=1, column=0, sticky=E+W)
        self.yscrollbar.grid(row=0, column=1, sticky=N+S)

    def child_added(self, child_widget):
        self.child_widget = child_widget
        self.xscrollbar.config(command=child_widget.xview)
        self.yscrollbar.config(command=child_widget.yview)
        child_widget.grid(row=0, column=0, sticky=N+S+E+W)
        child_widget.config(scrollregion=(0, 0, child_widget.width, child_widget.height),
                            xscrollcommand=self.xscrollbar.set, yscrollcommand=self.yscrollbar.set)

        child_widget.bind("<Button-4>", self.ywheel_handler)
        child_widget.bind("<Button-5>", self.ywheel_handler)
#        child_widget.bind("<Button-6>", self.xwheel_handler)    # FIXME: fix tkinter ?
#        child_widget.bind("<Button-7>", self.xwheel_handler)

    def ywheel_handler(self, e):
        self.child_widget.yview_scroll({4: -1, 5: 1 }[e.num], 'units') # button 4 => up; button 5 => down
    def xwheel_handler(self, e):
        self.child_widget.xview_scroll({6: -1, 7: 1 }[e.num], 'units') # button 6 => left; button 7 => right # FIXME: correct ???

# a custom canvas to display xy-plots
class XYPlot(Canvas):
    """
    """
    class Origin:
        def __init__(self, x, y):
            self.x = x
            self.y = y
        def set_origin(self, x, y):
            self.x = x
            self.y = y

    def __init__(self, pvconf, parent, width, height):
        self.origin = XYPlot.Origin(0, 0)
        self.upd = 1                                # units per division
        self.ppd = 100                              # pixel per division
        self.parent = parent
        self.width, self.height = width, height

        self.fgcolor = "black"
        self.bgcolor = "#EEEEEE"
        Canvas.__init__(self, self.parent, bg=self.bgcolor,
                              width=self.width, height=self.height)

        self.draw_axes(self.fgcolor)
        self.bind('<Configure>', self.resize_handler)

        self.lines = {}                             # a dictionaray containing all lines we have ever plotted
                                                    # the keys are 2-tuples of (references to) x- and y-value arrays 

        pvconf.add_ox_listener(self.update_ox)
        pvconf.add_scale_listener(self.update_scale)

    def add_line(self, view, index):
        # plot a line for the values at index, against view.x_values and keep track of it
        #
        #  color is determined by the view
        #  values_upd is determined by the conf
        #  values are taken from the experiment associated with the view
        #
        data = (view.experiment.values[view.x_values], view.experiment.values[index])
        if data not in self.lines:
#                self.data_line(view.experiment.values[view.x_values], view.experiment.values[index],
            self.lines[data] = \
                self.data_line(*data,
                               x_upd=view.ui.conf.values_upd[view.x_values], y_upd=view.ui.conf.values_upd[index], fill=view.colors[index])

    def update_ox(self, conf):
        ox, oy = conf.reset_upd(self.ppd, self.width, self.height)

        self.origin.set_origin(ox, oy)             # initialize scale to a sane default (all data visible)

        for ox in conf.open_experiments:
            for index in ox.view.y_values:
                self.add_line(ox.view, index)
            if self.update_view not in ox.view.listeners:
                ox.view.add_listener(self.update_view)

    def update_scale(self, conf):
        pass

    def update_view(self, view):
        for index in view.y_values:
            line = view.experiment.values[index]
            if line not in self.lines:                           # if we haven't dreawn it yet, do it now
                self.add_line(view, index)
            elif view.colors[index] != self.itemcget(self.lines[line], "fill"):    # otherwise, change the color if it has changed
                self.itemconfigure(self.lines[line], fill=view.colors[index])

    def pack(self, *args, **kwargs):
        Canvas.pack(self,  *args, **kwargs)
        if self.parent.__class__ == ScrollRegion:
            self.parent.child_added(self)

    def line(self, points, **kwargs):
        """
        draw a line along a list of point coordinates
        :parameters:
            points    list of point coordinates in the form: ((x1, y1), (x2, y2))
        """

        args = []
        for p in points:
            args.append(p[0])          
            args.append(self.height - p[1])

        return self.create_line(*args, **kwargs)

    def data_line(self, x, y, x_upd, y_upd, **kwargs):
        x = map(lambda v: v / float(x_upd) * self.ppd + self.origin.x, x)
        y = map(lambda v: v / float(y_upd) * self.ppd + self.origin.y, y)
        return self.line(zip(x, y), **kwargs)

    def draw_axes(self, color="black"):
#        self.delete(ALL)
        O = self.origin
        # positive axes
        self.line(((O.x, O.y), (self.width, O.y)), width=1, fill=color)
        self.line(((O.x, O.y), (O.x, self.height)), width=1, fill=color)
        for x in range(O.x, self.width, self.ppd):
            self.line(((x, O.y - 3), (x, O.y + 3)))
        for y in range(O.y, self.height, self.ppd):
            self.line(((O.x - 3, y), (O.x + 3, y)))
        # negative axes
        self.line(((O.x, O.y), (0, O.y)), width=1, fill=color)
        self.line(((O.x, O.y), (O.x, 0)), width=1, fill=color)
        for x in range(O.x, 0, -self.ppd):
            self.line(((x, O.y - 3), (x, O.y + 3)))
        for y in range(O.y, 0, -self.ppd):
            self.line(((O.x - 3, y), (O.x + 3, y)))

    def resize_handler(self, event):
        pass
#        print "w: %d" % self.winfo_width()
#        print "W: %d" % self.parent.winfo_width()
#        print "h: %d" % self.winfo_height()
#        print "H: %d" % self.parent.winfo_height()
#        self.repaint(self.bgcolor)
#        self.width = event.width
#        self.height = event.height
#        self.canvas.configure(width=self.width, height=self.height)
#        self.repaint(self.fgcolor)

class PlotControls(Frame):
    def __init__(self, parent, conf):
        Frame.__init__(self, parent)
        
        self.labels = {}
        self.scalers = {}
        self.xchooser = None

        conf.add_ox_listener(self.update_ox)
        conf.add_scale_listener(self.update_scales)

    def update_ox(self, conf):
        if len(conf.open_experiments):
            self.update_controls(conf)

    def update_scales(self, conf):
        for i in conf.values_upd:
            self.scalers[i].v.set(conf.values_upd[i])

    def update_controls(self, conf):
        # controls_region setup - keep pack()ing order !
        # y-axis controls

        for l in self.labels.values(): l.pack_forget()           # FIXME: uuuurg - we should reuse those widgets - shouldn't we ?
        for s in self.scalers.values(): s.pack_forget()          #        but currently I have no time to code the housekeeping logic
        if self.xchooser:
            self.xchooser.pack_forget()

        view = conf.open_experiments[0].view

        # y-axis controls
        for i in range(conf.nvalues):
            v = StringVar()
            v.trace("w", partial(self.controls_handler, v))
            sb = Spinbox(self, from_=0, width=5, textvariable=v)
            sb.v = v
            sb.pack(side=LEFT)
            self.scalers[i+1] = sb

            ul = Label(self, text=conf.units[i])
            ul.pack(side=LEFT)
            self.labels[i+1] = ul

        # x-axis controls
        if view.x_values == 0:      # time on x-axis
            xlabel = "s"
        else:
            xlabel = conf.units[view.x_values-1]    # because time is allways "s", view.units key "0" is v1_unit

        self.labels[0] = Label(self, text="s")
        self.labels[0].pack(side=RIGHT)

        v = StringVar()
        v.trace("w", partial(self.controls_handler, v))
        self.scalers[0] = Spinbox(self, from_=0, width=5, textvariable=v)
        self.scalers[0].v = v
        self.scalers[0].pack(side=RIGHT)

        v = StringVar()
        v.set("Zeit")
        v.trace("w", partial(self.controls_handler, v))
        x_values_list = ["Zeit"]
  
        for i in range(min([ox.get_nvalues() for ox in conf.open_experiments])):
            desc = ""
            for vdesc in [ox.get_desc(i + 1) for ox in conf.open_experiments]:
                if not desc.startswith(vdesc):
                    desc += " (%s)" % vdesc
            x_values_list.append(vdesc)

        self.xchooser = OptionMenu(self, v, *x_values_list)
        self.xchooser.v = v
        self.xchooser.pack(side=RIGHT)

    def controls_handler(self, v, *ign):
#        debug( v.get() )
        pass
    
class PVTable(MultiListbox):
    def __init__(self, parent, conf):
        self.parent = parent
        MultiListbox.__init__(self, self.parent, ("No Data",)) # Workaround for first call error: "AttributeError: PVTable instance has no attribute 'tk'"
        conf.add_ox_listener(self.update_ox)
 
    def update_ox(self, conf):
        debug()
        headers = ["Zeit",]
        data = []
        for ox in conf.open_experiments:
            # HEADER
            ox.header = self.get_header(ox)
            print "ox.header: %s" % ox.header
            for header in ox.header:
                headers.append(header)
            # DATA(s)
            print len(self.get_data(ox))
            for j in range(len(self.get_data(ox))):
#                print "self.get_data(ox)[%d]:" % j
#                print self.get_data(ox)[j]
                data.append(self.get_data(ox)[j])
#        print "calling update_table(headers, data): %s, %s" % (headers, data)
        self.update_table(headers, data)
        
    def get_header(self, ox):
        # Add Description (Table Header)
        header = []
        for i in range(ox.get_nvalues()):
            header.append( ox.get_desc(i), )
        return header

    def get_data(self, ox):
        data = []
        self.cols = ox.get_nvalues() # get the count of columns
        self.rows = len(ox.values[1]) # get the length of v1 values (v1 exists!)
        # Add Data from Experiment Table
        for row in range(self.rows):
#            print "ox.sqlvalues[%s]: %s " % ( row, ox.sqlvalues[row] )
            data.append(ox.sqlvalues[row],)
        return data
                
    def update_table(self, header, data):
        MultiListbox.__init__(self, self.parent, header)
#        print "data: %s" % data
        for row in range(len(data)):
#            print "row: %s " % row
            self.insert(END, data[row])
