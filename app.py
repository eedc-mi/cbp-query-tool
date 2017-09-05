from PyQt4 import QtGui
from PyQt4.QtCore import QThread, SIGNAL
import sys
import os
import sqlalchemy as sql

import ui.design as design
from lib.query import Query

class App(QtGui.QMainWindow, design.Ui_MainWindow):
    def __init__(self, query):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.query = query
        self.run_query_thread = None

        self.progressBar.setRange(0, 1)

        self.comboBoxTgtGeoLvl.addItems(self.query.target_geo_level_list)
        self.comboBoxTgtGeoLvl.currentIndexChanged.connect(self.on_select_tgt_geo_lvl)

        self.comboBoxPrtGeoLvl.addItems(self.query.parent_geo_level_list)
        self.comboBoxPrtGeoLvl.currentIndexChanged.connect(self.on_select_prt_geo_lvl)

        self.comboBoxNcsLvl.addItems(map(str, list(range(2, 7))))
        self.comboBoxNcsLvl.currentIndexChanged.connect(self.on_select_ncs_lvl)

        self.lineEditPrtGeoName.textEdited.connect(self.on_parent_edit_finished)

        self.buttonRunQuery.clicked.connect(self.on_run_query_clicked)

        self.buttonExportQuery.setEnabled(False)
        self.buttonExportQuery.clicked.connect(self.on_export_query_clicked)

    def on_select_tgt_geo_lvl(self, i):
        self.query.set_target_geo_level(self.query.target_geo_level_list[i])
        self.buttonExportQuery.setEnabled(False)

    def on_select_prt_geo_lvl(self, i):
        self.query.set_parent_geo_level(self.query.parent_geo_level_list[i])
        self.buttonExportQuery.setEnabled(False)

    def on_select_ncs_lvl(self, i):
        self.query.set_naics_level(i + 2)
        self.buttonExportQuery.setEnabled(False)

    def on_parent_edit_finished(self, string):
        self.query.set_parent_geo(str(string))
        self.buttonExportQuery.setEnabled(False)

    def on_run_query_clicked(self):
        self.buttonRunQuery.setEnabled(False)

        self.run_query_thread = RunQueryThread(self.query)
        self.connect(self.run_query_thread, SIGNAL('query_done(QString)'), self.finished)
        self.run_query_thread.start()
        self.progressBar.setRange(0, 0)

    def on_export_query_clicked(self):
        filepath = QtGui.QFileDialog.getSaveFileName(filter='CSV (Comma delimited) (*.csv)')
        self.query.df.to_csv(filepath, index=False)

    def finished(self, string):
        self.progressBar.setRange(0, 1)
        QtGui.QMessageBox.information(self, "Finished", string)
        self.buttonRunQuery.setEnabled(True)
        self.buttonExportQuery.setEnabled(True)
    

class RunQueryThread(QThread):
    def __init__(self, query):
        QThread.__init__(self)
        self.query = query

    def __del__(self):
        self.quit()
        self.wait()

    def run(self):
        string = ""
        stopped = False
        
        if not self.query.is_complete():
            string = 'One or more query terms are not selected or blank.\n\nPlease edit your query.'
            self.emit(SIGNAL('query_done(QString)'), string)
            stopped = True

        try:
            self.query.get_df()
        except MemoryError:
            string = 'Your query returned too many results. Please refine your query.'
            self.emit(SIGNAL('query_done(QString)'), string)
            stopped = True

            #TODO: fix when parent geo is wrong

        if not stopped:
            nrows = self.query.df.shape[0]
            if nrows == 0: 
                string = 'Your query returned 0 results, please check it for errors.'
            else:
                string = 'Your query returned %s results.' % nrows

            if nrows > 1048576:
                string += '\n\nWarning! You have more results than the Excel row limit.'

            self.emit(SIGNAL('query_done(QString)'), string)

def find_data_file(filename):
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable) + filename

    return 'data' + filename

def main():
    app = QtGui.QApplication(sys.argv)

    path = find_data_file('/data.db')
    engine = sql.create_engine('sqlite:///' + path)
    q = Query(engine)
    form = App(q)
    
    form.show()
    app.exec_()

if __name__ == '__main__':
    main()
