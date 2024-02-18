import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from data_prepare import get_final_date, get_price_data_from_json, get_fund_names, extract_fund_prices
from data_prepare import check_sync_requirement, update_price_json

class prepareGUI(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        master.title('Mutual Funds Progress')
        self.instantiate_variables()
        self.createFrames()
        self.draw_canvas()
        self.draw_widgets()
        master.mainloop()


    def instantiate_variables(self):
        self.data_dict = get_price_data_from_json()
        self.current_date = get_final_date(self.data_dict)
        self.fund_names = get_fund_names(self.data_dict)
        self.sync_required = check_sync_requirement(self.current_date)


    def createFrames(self):
        window = self.master
        self.frame1 = tk.LabelFrame(master=window, text='Controls', relief=tk.RIDGE, borderwidth=5)
        self.frame2 = tk.LabelFrame(master=window, text='Graphics', relief=tk.RIDGE, borderwidth=5)
        self.frame3 = tk.LabelFrame(master=window, text='Info', relief=tk.RIDGE, borderwidth=5)

        self.frame11 = tk.Frame(master=self.frame1)
        self.frame12 = tk.Frame(master=self.frame1)
        self.frame13 = tk.Frame(master=self.frame1)

        self.frame1.pack(side=tk.TOP, fill=tk.X, padx=1, pady=1)
        self.frame2.pack(side=tk.TOP, fill=tk.BOTH, padx=1, pady=1, expand=True)
        self.frame3.pack(side=tk.TOP, fill=tk.X, padx=1, pady=1)

        self.frame11.pack(side=tk.LEFT, fill=tk.X, padx=10, pady=1)
        self.frame13.pack(side=tk.RIGHT, fill=tk.X, padx=10, pady=1)
        self.frame12.pack(side=tk.RIGHT, fill=tk.X, padx=50, pady=1)


    def draw_canvas(self):
        self.figure_graph = plt.Figure(figsize=(4., 2.), dpi=300)
        paddingx = 0.07
        paddingy = 0.1
        self.graph_ax = self.figure_graph.add_axes([paddingx, paddingy, 1 - 1.5 * paddingx, 1 - 1.5 * paddingy], frameon=True)
        self.graph_ax.tick_params(axis='y', which='major', labelsize=3)
        self.graph_ax.tick_params(axis='x', which='major', labelsize=3)

        self.line_selling, = self.graph_ax.plot_date([], [], 'k-', linewidth=0.5, zorder=3, label='Selling')
        self.line_buying, = self.graph_ax.plot_date([], [], 'r-', linewidth=0.5, zorder=4, label='Buying')

        self.graph_ax.legend(fontsize=4)
        self.graph_ax.grid(True, linewidth=0.5)

        self.graph_chart = FigureCanvasTkAgg(self.figure_graph, self.frame2)
        self.zoomtoolbar = NavigationToolbar2Tk(self.graph_chart, window=self.frame2)
        self.zoomtoolbar.pack(side=tk.TOP)
        self.graph_chart.get_tk_widget().pack(fill=tk.BOTH, expand=True)


    def draw_widgets(self):
        self.lbl_fund_meta = tk.Label(master=self.frame11, text='Fund: ')
        self.lbl_fund_meta.pack(side=tk.LEFT)
        value_inside = tk.StringVar()
        value_inside.set('')
        self.dropdwn_list = tk.OptionMenu(self.frame11, value_inside, *self.fund_names, command=self.handle_optionmenu)
        self.dropdwn_list.configure(width=100, anchor='w', justify='left')
        self.dropdwn_list.pack(side=tk.LEFT)

        self.lbl_date_meta = tk.Label(master=self.frame12, text='Date: ')
        self.lbl_date_meta.pack(side=tk.LEFT)
        self.lbl_date = tk.Label(master=self.frame12, text=self.current_date, width=10)
        self.lbl_date.pack(side=tk.LEFT)

        self.btn_sync = tk.Button(master=self.frame13, text='Sync', width =20, command=self.handle_sync)
        self.btn_sync.pack(side=tk.TOP)

        self.lbl_status = tk.Label(master=self.frame3, text='')
        self.lbl_status.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.update_buttons()


    def handle_optionmenu(self, event):
        self.price_array = extract_fund_prices(self.data_dict, event)
        self.update_figure()


    def update_figure(self):
        date_array = np.array(self.price_array[:, 0], dtype='datetime64[ms]')
        selling = self.price_array[:, 1].astype(float)
        buying = self.price_array[:, 2].astype(float)

        self.line_selling.set_xdata(date_array)
        self.line_selling.set_ydata(selling)
        self.line_buying.set_xdata(date_array)
        self.line_buying.set_ydata(buying)

        self.graph_ax.set_xlim(min(date_array), max(date_array))
        self.graph_ax.set_ylim(min(min(selling), min(buying))-1, max(max(selling), max(buying))+1)

        self.graph_chart.draw()
        self.graph_chart.flush_events()


    def update_buttons(self):
        if(self.sync_required):
            self.btn_sync['state'] = tk.NORMAL
            self.lbl_status['text'] = 'Database outdated! Please sync the database'
        else:
            self.btn_sync['state'] = tk.DISABLED
            self.lbl_status['text'] = 'Database upto date!'


    def handle_sync(self, event):
        update_price_json(self)
        self.lbl_status['text'] = 'Database upto date!'