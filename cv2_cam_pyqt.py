from unittest import result
import cv2
import sys, time, os
import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets
from Ui_main import Ui_MainWindow
from PIL import Image

class Camera(QtCore.QThread):
    rawdata = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cam = cv2.VideoCapture(0)
        if self.cam is None or not self.cam.isOpened():
            self.connect = False
            self.running = False
        else:
            self.connect = True
            self.running = False

    def run(self):
        while self.running and self.connect:
            ret, img = self.cam.read()
            if ret:
                self.rawdata.emit(img)
            else:
                print("Warning!!!")
                self.connect = False
    
    def open(self):
        if self.connect:
            self.running = True

    def stop(self):
        if self.connect:
            self.running = False

    def close(self):
        if self.connect:
            self.running = False
            time.sleep(1)
            self.cam.release()


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):    
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.viewData.setScaledContents(True)


        self.view_x = self.view.horizontalScrollBar()
        self.view_y = self.view.verticalScrollBar()
        self.view.installEventFilter(self)
        self.last_move_x = 0
        self.last_move_y = 0

        self.frame_num = 0

        self.localtime = time.localtime()

        self.RadioName =  "Normal"
        self.SaveMode = "Save"
        self.ProcessCam = Camera()
        if self.ProcessCam.connect:
            self.debugBar('Connection!!!')
            self.ProcessCam.rawdata.connect(self.getRaw)
        else:
            self.debugBar('Disconnection!!!')
        
        self.camBtn_open.clicked.connect(self.openCam)
        self.camBtn_stop.clicked.connect(self.stopCam)
        self.save_btn.clicked.connect(self.savePicture)
        self.Picture_edit.clicked.connect(self.EditPicture)
        self.Previous_btn.clicked.connect(self.DataPrevious)
        self.Next_btn.clicked.connect(self.DataNext)
        

        self.radio_Normal.toggled.connect(self.onClicked)
        self .radio_Turbid.toggled.connect(self.onClicked)
        self.radio_SmallTubid.toggled.connect(self.onClicked)
        #self.radio_SmallTubid.setChecked(True)
        #self.radio_Turbid.setChecked(True)

        self.camBtn_stop.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.radio_Normal.setEnabled(False)
        self.radio_Turbid.setEnabled(False)
        self.radio_SmallTubid.setEnabled(False)
        self.Previous_btn.setEnabled(False)
        self.Next_btn.setEnabled(False)

        self.viewCbo_roi.currentIndexChanged.connect(self.onComboBoxChanged)
        
        
    def getRaw(self, data):
        self.showData(data)

        
    def openCam(self):
        if self.ProcessCam.connect:
            self.ProcessCam.open()
            self.ProcessCam.start()
            self.Page_Label.setText("")
            self.camBtn_open.setEnabled(False)
            self.camBtn_stop.setEnabled(True)
            self.viewCbo_roi.setEnabled(True)
            self.Picture_edit.setEnabled(False)
            self.save_btn.setEnabled(True)
            self.radio_Normal.setEnabled(True)
            self.radio_Turbid.setEnabled(True)
            self.radio_SmallTubid.setEnabled(True)
            self.Previous_btn.setEnabled(False)
            self.Next_btn.setEnabled(False)
            self.SaveMode = "Save"
    def stopCam(self):
        if self.ProcessCam.connect:
            self.ProcessCam.stop()
            self.camBtn_open.setEnabled(True)
            self.camBtn_stop.setEnabled(False)
            self.viewCbo_roi.setEnabled(False)
            self.save_btn.setEnabled(False)
            self.radio_Normal.setEnabled(False)
            self.radio_Turbid.setEnabled(False)
            self.radio_SmallTubid.setEnabled(False)
            self.Picture_edit.setEnabled(True)
    
    def EditPicture(self):
        if self.ProcessCam.connect:
            self.ProcessCam.stop()
            self.camBtn_open.setEnabled(True)
            self.Picture_edit.setEnabled(False)
            self.camBtn_stop.setEnabled(False)
            self.save_btn.setEnabled(True)
            self.radio_Normal.setEnabled(True)
            self.radio_Turbid.setEnabled(True)
            self.radio_SmallTubid.setEnabled(True)
            self.Previous_btn.setEnabled(True)
            self.Next_btn.setEnabled(True)
            self.SaveMode = "Edit"
        self.dirPath = "images"
        self.files = next(os.walk(self.dirPath))[2]
        if len(self.files) != 0:
            self.ImageIndex = len(self.files)
            self.ImageIndexFinal = len(self.files)
            self.FileName = self.files[self.ImageIndex-1]
            self.RadioName = self.files[self.ImageIndex-1].split('_')[0]
            self.TimeName = self.files[self.ImageIndex-1].split('_')[1]
            self.ShowEditData()

    def DataPrevious(self):
        if self.ImageIndex > 1 :
            self.ImageIndex = self.ImageIndex - 1
        else:
            self.ImageIndex = self.ImageIndexFinal       

        self.ShowEditData()

    def DataNext(self):
        if self.ImageIndex  <  self.ImageIndexFinal:
            self.ImageIndex = self.ImageIndex + 1
        else:
            self.ImageIndex = 1      

        self.ShowEditData()

    def ShowEditData(self):
        self.Page_Label.setText(str(self.ImageIndex) + "/" + str(self.ImageIndexFinal))
        img = cv2.imread(self.dirPath + "//" + self.files[self.ImageIndex-1])
        img_new = np.zeros_like(img)
        img_new[...,0] = img[...,2]
        img_new[...,1] = img[...,1]
        img_new[...,2] = img[...,0]
        img = img_new
        self.Ny,self.Nx, _ = img.shape
        qimg = QtGui.QImage(img.data, self.Nx, self.Ny, QtGui.QImage.Format_RGB888)
        self.viewData.setScaledContents(True)
        self.viewData.setPixmap(QtGui.QPixmap.fromImage(qimg))
        file = self.files
        self.RadioName = file[self.ImageIndex-1].split("_")[0]
        self.TimeName = file[self.ImageIndex-1].split('_')[1]
        self.debugBar(file[self.ImageIndex-1])
        if self.RadioName == "Normal":
            self.radio_Normal.setChecked(True)
        elif self.RadioName == "SmallTurbid":
            self.radio_SmallTubid.setChecked(True)
        elif self.RadioName == "Turbid":
            self.radio_Turbid.setChecked(True)
        
        

    def savePicture(self):        
        if self.SaveMode == "Save":
            name = self.RadioName + "_" + self. TimeName + ".jpg" # set file name
            print(name)
            cv2.imwrite("images//"+name,self.image) # save image file
        elif self.SaveMode == "Edit":
            newName =   self.RadioName + "_" + self.TimeName
            oldName = self.FileName
            file_oldName =os.path.join("images",oldName)
            file_newName = os.path.join("images",newName)
            self.FileName = newName
            os.rename(file_oldName,file_newName)
            self.files = next(os.walk(self.dirPath))[2]
            self.debugBar(self.FileName)

    def showData(self, img):
        self.Ny, self.Nx, _ = img.shape
        self.image = img #get image
        self.TimeName = time.strftime("%Y-%m-%d-%H-%M-%S ",time.localtime()) #get time
        # 反轉顏色
        img_new = np.zeros_like(img)
        img_new[...,0] = img[...,2]
        img_new[...,1] = img[...,1]
        img_new[...,2] = img[...,0]
        img = img_new

        # qimg = QtGui.QImage(img[:,:,0].copy().data, self.Nx, self.Ny, QtGui.QImage.Format_Indexed8)
        qimg = QtGui.QImage(img.data, self.Nx, self.Ny, QtGui.QImage.Format_RGB888)
        self.viewData.setScaledContents(True)
        
        self.viewData.setPixmap(QtGui.QPixmap.fromImage(qimg))

        if self.frame_num == 0:
            self.time_start = time.time()
        if self.frame_num >= 0:
            self.frame_num += 1
            self.t_total = time.time() - self.time_start
            if self.frame_num % 100 == 0:
                self.frame_rate = float(self.frame_num) / self.t_total
                self.debugBar('FPS: %0.3f frames/sec' % self.frame_rate)

    def eventFilter(self, source, event):
        if source == self.view:
            if event.type() == QtCore.QEvent.MouseMove:
                if self.last_move_x == 0 or self.last_move_y == 0:
                    self.last_move_x = event.pos().x()
                    self.last_move_y = event.pos().y()
                distance_x = self.last_move_x - event.pos().x()
                distance_y = self.last_move_y - event.pos().y()
                self.view_x.setValue(self.view_x.value() + distance_x)
                self.view_y.setValue(self.view_y.value() + distance_y)
                self.last_move_x = event.pos().x()
                self.last_move_y = event.pos().y()
            elif event.type() == QtCore.QEvent.MouseButtonRelease:
                self.last_move_x = 0
                self.last_move_y = 0
            return QtWidgets.QWidget.eventFilter(self, source, event)
    
    def closeEvent(self, event):
        if self.ProcessCam.running:
            self.ProcessCam.close()
            self.ProcessCam.terminate()
        QtWidgets.QApplication.closeAllWindows()
        
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Q:
            if self.ProcessCam.running:
                self.ProcessCam.close()
                time.sleep(1)
                self.ProcessCam.terminate()
            QtWidgets.QApplication.closeAllWindows()
#choose radio button
    def onClicked(self):
        radioBtn = self.sender()
        if radioBtn.isChecked():        
            self.RadioName = radioBtn.text()
        
    def onComboBoxChanged(self):
        if self.viewCbo_roi.currentIndex() == 0: roi_rate = 0.5
        elif self.viewCbo_roi.currentIndex() == 1: roi_rate = 0.75
        elif self.viewCbo_roi.currentIndex() == 2: roi_rate = 1
        elif self.viewCbo_roi.currentIndex() == 3: roi_rate = 1.25
        elif self.viewCbo_roi.currentIndex() == 4: roi_rate = 1.5
        elif self.viewCbo_roi.currentIndex() == 5: roi_rate = 0.25
        else: pass
        self.viewForm.setMinimumSize(self.Nx*roi_rate, self.Ny*roi_rate)
        self.viewForm.setMaximumSize(self.Nx*roi_rate, self.Ny*roi_rate)
        self.viewData.setMinimumSize(self.Nx*roi_rate, self.Ny*roi_rate)
        self.viewData.setMaximumSize(self.Nx*roi_rate, self.Ny*roi_rate)

    def debugBar(self, msg):
        self.statusBar.showMessage(str(msg), 5000)


if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
