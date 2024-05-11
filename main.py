import os
import sys
import numpy as np
import math
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
from scipy.optimize import least_squares
import numpy as np

# Check operating system
CURR_OS = 0
if os.name == "nt":
    CURR_OS = 1

class GraphWidget(QWidget):
    def __init__(self, parent=None):
        super(GraphWidget, self).__init__(parent)

        self._load_start()

    def _load_start(self):
        # Set initial layout for reading file
        self._layout = QGridLayout(self)
        
        self.logo_label = QLabel(self)
        pixmap = QtGui.QPixmap('fenix.png')
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self.logo_label, 0, 0, 1, 2)  # Adjust the position as needed

        self.parent().setWindowTitle("BancadaInterface")

        # Receive filepath for csv file
        self._selected_file = ""
        self._is_selected = False
        self.filepath_widget = QLineEdit(self)
        self.filepath_widget.setPlaceholderText("Please insert path to data file")
        self.filepath_widget.textChanged.connect(self._check_file)
        self._layout.addWidget(self.filepath_widget, 1, 0)
        self.error_message = QLabel(self)
        self.error_message.setText(None)
        self._layout.addWidget(self.error_message, 2, 0)

        self.confirm_button = QPushButton("Confirm", self)
        self.confirm_button.setMaximumWidth(100)
        self.confirm_button.clicked.connect(self._confirm_file)
        self._layout.addWidget(self.confirm_button, 1, 1)

        # Initialize lists for graph widgets and plots
        self._plotwidgets = []
        self._plots = []
        self._stat_labels = []

    def _check_file(self, filepath):
        '''
        Updates the current entered filepath in the search bar
        '''
        if not os.path.abspath(".") in filepath:
            if CURR_OS == 0:
                filepath = os.path.abspath(".") + "/" + filepath.replace("\\", "/").strip("/")
            elif CURR_OS == 1:
                filepath = os.path.abspath(".") + "\\" + filepath.replace("/", "\\").strip("\\")

        if self._is_selected:
            self._new_filepath = filepath
        else:
            self._selected_file = filepath

    def _set_error_message(self, msg):
        '''
        Sets the content in the label for error reporting
        '''
        print(msg)
        self.error_message.setText(msg)
    
    def _confirm_file(self):
        '''
        Checks filename for errors in path and extension.
        '''
        checking_file = self._selected_file
        if self._is_selected:
            checking_file = self._new_filepath
 
        if len(checking_file) < 1:
            self._set_error_message("Please enter a file path")
        elif not os.path.isfile(checking_file):
            self._set_error_message("Please enter a valid file path")
        elif (not checking_file.lower().endswith(".txt")) and (not checking_file.lower().endswith(".csv")):
            self._set_error_message("Please enter a valid file")
        else:
            self._selected_file = checking_file
            self._remove_graphs()
            self._load_graphs()
            self._is_selected = True
            
    def _read_header(self, filepath):
        '''
        Gets the header content from the data files.
        Expected format:
        ; TEST NAME
        CLASSE Dext COMPRIMENTO P MASSA_PROPELENTE(kg) MASSA_MOTOR_COMPLETO(kg) FENIX
        '''
        with open(filepath, 'r') as report:
            header = report.readline()
            self._test_name = header.strip("; \n")
            self.parent().setWindowTitle(f"BancadaInterface - {self._test_name}")

            self._model_info = report.readline().split()

            self._columns = list(filter(None, report.readline().split()))

    def _read_data(self, filepath):
        '''
        Reads the columns data and stores in a dictionary.
        Each key corresponds to a column and contains a list of values
        for that metric.
        '''
        
        self._values = {k: [] for k in self._columns}
        with open(filepath, 'r') as report:
            for line in report.readlines()[3:]:
                row = list(filter(None, line.split()))   
                
                for i, val in enumerate(row):
                    self._values[self._columns[i]].append(float(val))
        self._preprocess_data()

    def _preprocess_data(self):
        # Filter data to use only 0.1 seconds intervals
        time_column = self._columns[0]
        time_values = np.array(self._values[time_column])
        new_time_values = np.arange(time_values[0], time_values[-1], 0.1)

        for column in self._columns[1:]:
            column_values = np.array(self._values[column])
            new_column_values = []
            for i in range(len(new_time_values) - 1):
                mask = (time_values >= new_time_values[i]) & (time_values < new_time_values[i+1])
                interval_values = column_values[mask]
                # Use the actual values instead of the mean
                new_column_values.append(np.mean(interval_values))

            self._values[column] = new_column_values

        self._values[time_column] = new_time_values[:-1].tolist()

    def _update_visualization(self):
         # Plot one graph for each column excepting the time
        time_column = self._columns[0]
        if self._start < 0:
            self._start = self._values[time_column][0]
        if self._end < 0 or self._end < self._start:
            self._end = self._values[time_column][-1]
            
        # Filter data based on time window
        mask = (np.array(self._values[time_column]) >= self._start) & (np.array(self._values[time_column]) <= self._end)
        
        for n, plot in enumerate(self._plots):
            # Display graph
            plot.setData(np.array(self._values[time_column])[mask], np.array(self._values[self._columns[n+1]])[mask])

            # Add statistics for graph
            data = np.array(self._values[self._columns[n+1]])[mask]
            mean = np.mean(data)
            median = np.median(data)
            max_val = np.max(data)
            min_val = np.min(data)

            self._stat_labels[n].setText(f"Mean: {mean:.2f}, Median: {median:.2f}, Max: {max_val:.2f}, Min: {min_val:.2f}")

    def _load_visualization(self):
        # Plot one graph for each column excepting the time
        time_column = self._columns[0]
        if self._start < 0:
            self._start = self._values[time_column][0]
        if self._end < 0 or self._end < self._start:
            self._end = self._values[time_column][-1]
            
        # Filter data based on time window
        mask = (np.array(self._values[time_column]) >= self._start) & (np.array(self._values[time_column]) <= self._end)
        
        for column in self._columns[1:]:
            # Calculate row index
            row_idx = 2 * (2 + math.floor((len(self._plotwidgets)) / 2))

            # Create widget in grid layout
            plot_widget = pg.PlotWidget(self)
            plot_widget.setTitle(f"{column} x {time_column}")
            plot_widget.setLabel('left', column)
            plot_widget.setLabel('bottom', time_column)

            # Display graph
            plot = plot_widget.plot(pen='#3d2163', symbolBrush='#3d2163', symbolSize=3)
            plot.setData(np.array(self._values[time_column])[mask], np.array(self._values[column])[mask])
            self._layout.addWidget(plot_widget, row_idx, len(self._plotwidgets) % 2)

            # Add statistics for graph
            data = np.array(self._values[column])[mask]
            mean = np.mean(data)
            median = np.median(data)
            max_val = np.max(data)
            min_val = np.min(data)

            stats_label = QLabel(self)
            stats_label.setText(f"Mean: {mean:.2f}, Median: {median:.2f}, Max: {max_val:.2f}, Min: {min_val:.2f}")
            self._layout.addWidget(stats_label, row_idx + 1, len(self._plotwidgets) % 2)

            # Add the label to the list
            self._plotwidgets.append(plot_widget)
            self._plots.append(plot)
            self._stat_labels.append(stats_label)

    def _load_window_inputs(self):
        self._start = -1
        self._end = -1
        # Create QLineEdit for start value
        self.start_input = QLineEdit(self)
        self.start_input.setPlaceholderText("Enter start time")
        self._layout.addWidget(self.start_input, 2, 0)  # Adjust the position as needed
        self.start_input.textChanged.connect(self._update_start)

        # Create QLineEdit for end value
        self.end_input = QLineEdit(self)
        self.end_input.setPlaceholderText("Enter end time")
        self._layout.addWidget(self.end_input, 2, 1)  # Adjust the position as needed
        self.end_input.textChanged.connect(self._update_end)

    def _update_start(self, text):
        try:
            self._start = float(text)
            self._update_visualization()
        except ValueError:
            if len(text) == 0:
                self._start = 0
                self._update_visualization()
            # Invalid number, ignore

    def _update_end(self, text):
        try:
            self._end = float(text)
            self._update_visualization()
        except ValueError:
            if len(text) == 0:
                self._end = -1
                self._update_visualization()
            # Invalid number, ignore

    def _load_graphs(self):
        print(f"Loading data from file {self._selected_file}")
        self._read_header(self._selected_file)
        self._read_data(self._selected_file)
        self._load_window_inputs()
        self._load_visualization()

    def _remove_graphs(self):
        for plot_widget in self._plotwidgets:
            # Remove the widget from the layout
            self._layout.removeWidget(plot_widget)
            # Optional: delete the widget
            plot_widget.setParent(None)
            plot_widget.deleteLater()

        for stat_label in self._stat_labels:
            # Remove the label from the layout
            self._layout.removeWidget(stat_label)
            # Optional: delete the label
            stat_label.setParent(None)
            stat_label.deleteLater()

        # Clear the lists
        self._plotwidgets.clear()
        self._plots.clear()
        self._stat_labels.clear()


if __name__ == "__main__":
    print("Inicializando bancada de testes...")
        
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    graph_widget = GraphWidget(main_window)
    main_window.setCentralWidget(graph_widget)
    main_window.setGeometry(100, 100, 800, 600)
    main_window.show()

    sys.exit(app.exec_())