from PySide6.QtCore import Signal, QThread
from PySide6.QtWidgets import (
    QMainWindow,
    QApplication,
    QFileDialog,
    QMessageBox,
    QVBoxLayout
)

import sys
import os
import json
import source_Misc as mc
import source_Forecast as fc

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form_main import Ui_MainWindow
from uicode_CreateModelWindow import CreateModelWindow
from uisource_GraphWidget import GraphWidget

# helper worker thread class to run the forecast function
class ForecastWorker(QThread):
    finished = Signal(object)

    def __init__(self, df, layers_config, target_var, training_cols, forecast_period, epochs, step_future, step_past, dropout, optimizer, loss):
        super().__init__()
        self.df = df
        self.layers_config = layers_config
        self.target_var = target_var
        self.training_cols = training_cols
        self.forecast_period = forecast_period
        self.epochs = epochs
        self.step_future = step_future
        self.step_past = step_past
        self.dropout = dropout
        self.optimizer = optimizer
        self.loss = loss

    def run(self):
        forecast_df = None
        try:
            forecast_df = fc.forecast(self.df, self.layers_config, self.target_var, training_cols=self.training_cols,
                forecast_period=self.forecast_period, epochs=self.epochs, step_future=self.step_future, step_past=self.step_past,
                dropout=self.dropout, optimizer=self.optimizer, loss=self.loss)
            self.finished.emit(forecast_df)
        except Exception as e:
            self.finished.emit(e)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.df = None
        self.data_loaded = False
        # self.layer_data = None
        self.model_params = None

        # setup combobox
        for ticker in mc.list_sp500_tickers():
            self.ui.ticker_combobox.addItem(ticker, ticker)
        self.ui.ticker_combobox.setCurrentIndex(-1)

        self.ui.import_button.setEnabled(False)
        self.ui.back_button.setEnabled(False)
        self.ui.forecast_progress_label.setVisible(False)

        self.ui.createmodel_button.setEnabled(False)
        self.ui.forecast_button.setEnabled(False)

        # adding the graph widget
        self.graph_widget = GraphWidget()
        self.ui.graph_layout = QVBoxLayout(self.ui.graph_placeholder_widget)
        self.ui.graph_layout.addWidget(self.graph_widget)

        # ---- CONNECT SIGNALS ----

        # data import stuff
        self.ui.ticker_combobox.currentIndexChanged.connect(self.on_ticker_combobox_changed)
        self.ui.fileexplorer_button.clicked.connect(self.on_fileexplorer_button_clicked)
        self.ui.import_button.clicked.connect(self.on_import_button_clicked)
        self.ui.back_button.clicked.connect(self.on_back_button_clicked)

        # model stuff
        self.ui.createmodel_button.clicked.connect(self.on_createmodel_button_clicked)
        self.ui.forecast_button.clicked.connect(self.on_forecast_button_clicked)

        # graph stuff
        self.ui.window10_button.clicked.connect(self.on_timewindow10_changed)
        self.ui.window50_button.clicked.connect(self.on_timewindow50_changed)
        self.ui.window100_button.clicked.connect(self.on_timewindow100_changed)
        self.ui.window500_button.clicked.connect(self.on_timewindow500_changed)
        self.ui.window1000_button.clicked.connect(self.on_timewindow1000_changed)
        self.ui.windowmax_button.clicked.connect(self.on_timewindowmax_changed)


    # ---- SLOT FUNCTIONS ----

    #
    # data import stuff
    #
    def on_ticker_combobox_changed(self):
        ticker = self.ui.ticker_combobox.currentText()
        self.ui.currentdata_label.setText("Current Data: " + ticker)
        self.df = mc.get_data(ticker)
        self.ui.import_button.setEnabled(True)

    def on_fileexplorer_button_clicked(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)")

        if file_name:
            file_base = os.path.basename(file_name)
            self.ui.currentdata_label.setText("Current Data: " + file_base)

            self.df = mc.read_csv(file_name)

            self.ui.import_button.setEnabled(True)
            self.ui.ticker_combobox.blockSignals(True)
            self.ui.ticker_combobox.setCurrentIndex(-1)
            self.ui.ticker_combobox.blockSignals(False)

            if self.df is None:
                message = "Failed to read the CSV file"
                warning_box = QMessageBox(QMessageBox.Warning, "File Read Error", message, QMessageBox.Ok, self)
                warning_box.exec()
        else:
            self.ui.currentdata_label.setText("Current Data: None")
            message = "No file selected"
            warning_box = QMessageBox(QMessageBox.Warning, "No File Selected", message, QMessageBox.Ok, self)
            warning_box.exec()

    def on_import_button_clicked(self):
        if self.df is not None:
            self.ui.ticker_combobox.setEnabled(False)
            self.ui.fileexplorer_button.setEnabled(False)
            self.ui.import_button.setEnabled(False)
            self.ui.back_button.setEnabled(True)
            self.ui.createmodel_button.setEnabled(True)

            self.data_loaded = True

            self.graph_widget.set_data(self.df, 'open')

    def on_back_button_clicked(self):
        self.df = None
        self.ui.ticker_combobox.setEnabled(True)
        self.ui.fileexplorer_button.setEnabled(True)
        self.ui.createmodel_button.setEnabled(False)

        self.ui.back_button.setEnabled(False)
        self.ui.ticker_combobox.blockSignals(True)
        self.ui.ticker_combobox.setCurrentIndex(-1)
        self.ui.ticker_combobox.blockSignals(False)
        self.ui.currentdata_label.setText("Current Data: None")
        self.data_loaded = False

        self.graph_widget.clear_graph()


    #
    # graph stuff
    #
    def on_timewindow10_changed(self):
        if self.df is not None:
            self.graph_widget.set_params(10)
    def on_timewindow50_changed(self):
        if self.df is not None:
            self.graph_widget.set_params(50)
    def on_timewindow100_changed(self):
        if self.df is not None:
            self.graph_widget.set_params(100)
    def on_timewindow500_changed(self):
        if self.df is not None:
            self.graph_widget.set_params(500)
    def on_timewindow1000_changed(self):
        if self.df is not None:
            self.graph_widget.set_params(1000)
    def on_timewindowmax_changed(self):
        if self.df is not None:
            self.graph_widget.set_params('max')


    #
    # forecast model stuff
    #

    def on_createmodel_button_clicked(self):
        filtered_df = self.df.drop(columns=['date'], errors='ignore')
        column_names = filtered_df.columns.tolist()  # Get column names as a list
        self.window = CreateModelWindow(column_names)
        # for data recieved
        self.window.data_submitted.connect(self.data_from_create_model)
        self.window.show()
    def data_from_create_model(self, serialized_data):
        self.model_params = json.loads(serialized_data)
        self.ui.forecast_button.setEnabled(True)

    def on_forecast_button_clicked(self):
        layer_data = self.model_params['layer_widgets_dict']
        # create layer config and initialize dropout (dropout is in the layer_widgets_dict)
        layer_neuron_list = []
        layer_type_list = []
        layer_return_list = []
        dropout = 0
        for i, layer in enumerate(layer_data):
            if i != len(layer_data)-1:
                layer_neuron_list.append(layer['neuron_spinbox'])
                layer_type_list.append(layer['type_combobox'])
                layer_return_list.append(layer['rseq'])
            else:
                dropout = layer['dropout_spinbox'] / 100
        layer_count = len(layer_data) - 1 # not including the last dropout layer
        layers_config = mc.create_layer_config(layer_count, layer_neuron_list, layer_type_list, layer_return_list)

        # run the forecast in a separate thread
        self.ui.forecast_progress_label.setVisible(True)

        self.forecast_worker = ForecastWorker(self.df, layers_config, self.model_params['target_variable'], self.model_params['training_cols'],
            self.model_params['forecast_period'], self.model_params['epochs'], self.model_params['step_future'], self.model_params['step_past'],
            dropout, self.model_params['optimizer'], self.model_params['loss'])

        self.forecast_worker.finished.connect(self.on_forecast_complete)
        self.forecast_worker.start()

    def enableb_forecast(self, bool):
        self.ui.createmodel_button.setEnabled(bool)
        self.ui.forecast_button.setEnabled(bool)
        self.ui.back_button.setEnabled(bool)

    def on_forecast_complete(self, result):
        self.ui.forecast_progress_label.setVisible(False)
        self.enableb_forecast(True) # enable all the buttons here where the thread finishes

        if isinstance(result, Exception):
            # Handle the exception
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setWindowTitle("Forecast Error")
            error_dialog.setText("An error occurred while forecasting.")
            print(result)
            error_dialog.setInformativeText(str(result))  # Show the exception message
            error_dialog.exec()
        else:
            # TODOOOOOOOOOO Handle the forecasted DataFrame
            print(result)  # Replace this with further processing or updating the UI


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())
