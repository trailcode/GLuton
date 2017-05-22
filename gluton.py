import os
import sys
import PyQt4
from PyQt4.QtGui import QMainWindow
from PyQt4.QtOpenGL import *
from OpenGL.GL import *
from PyQt4 import uic, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from scipy.interpolate import interp1d
from scipy.interpolate import splrep, splev
from itertools import product
from ServosPosGraph import ServosPosGraph
from ConsoleWidget import ConsoleWidget
from SpyderConsoleWidget import SpyderConsoleWidget
from spyderlib.widgets import internalshell
import numpy as np
from guiUtils import guirestore, guisave
#from projexui.widgets.xconsoleedit import XConsoleEdit

#from python_qt_binding.QtGui import QFont
from PyQt4.QtGui import QFont

import sys
sys.path.append('/anaconda/lib/python3.5/site-packages')
import serial

"""
s = None
try: s = serial.Serial(port='/dev/cu.wchusbserial1420', baudrate=115200)
except: pass
"""

def _str(s): return str.encode(str(s));

import operator

def get_truth(inp, relate, cut):
    ops = {'>': operator.gt,
           '<': operator.lt,
           '>=': operator.ge,
           '<=': operator.le,
           '=': operator.eq}
    return ops[relate](inp, cut)

class ServoAdjustment(QMainWindow):
    def __init__(self):
        super(ServoAdjustment, self).__init__()
        self.ui = uic.loadUi("gluton.ui", self)
        self.ui.show()

        self.setWindowTitle('Gluton')

        self.ui.spinBoxServo.valueChanged.connect(self.servoChanged)
        self.sliders = []
        self.canvas = ServosPosGraph(self)
        self.ui.canvasLayout.addWidget(self.canvas)

        self.background_pixmap = QPixmap('logo.png')

        def saveFile():
            print('Save')

        self.ui.actionSave.triggered.connect(saveFile)

        self.currBeingEdited = 0

        self.names = ['Left Ankle', 'Left Knee', 'Left Hip', 'Left Shoulder', 'Left Elbow', 'Left Wrist',
                      'Right Ankle', 'Right Knee', 'Right Hip', 'Right Shoulder', 'Right Elbow', 'Right Wrist', 'time']

        self.servoValueSliders = []
        self.servoValueLabels = []
        self.center()

        self.interpolationMode = 0
        self.ui.interpolationComboBox.addItems(['B-Spline', '1D'])

        def setMode(mode): self.interpolationMode = mode

        self.ui.interpolationComboBox.activated.connect(setMode)

        for i,index in zip(self.names, range(0, len(self.names))):
            exec('ServoAdjustment.f' + str(index) + ' = lambda self, value: self.servoSliderChanged(' + str(index) + ', value)')
            label = QLabel()
            label.setText(i + ':')
            label.setFixedWidth(100)
            label.setAlignment(Qt.AlignRight)
            class MySlider(QSlider):
                def __init__(self, c, servoAdjustment, direction, parent=None):
                    super(MySlider, self).__init__(direction, parent)
                    self.setMouseTracking(True)
                    self.number = index
                    self.servoAdjustment = servoAdjustment

                def enterEvent(self, event):

                    self.servoAdjustment.currBeingEdited = self.number
                    self.servoAdjustment.canvas.paintGL()
                    self.servoAdjustment.canvas.swapBuffers()
                    self.servoAdjustment.canvas.repaint()
                    #self.setStyleSheet("background-color:#45b545;")

            slider = MySlider(index, self, Qt.Horizontal)
            slider.setMaximum(256)
            self.sliders += [slider]
            valueLabel = QLabel()
            valueLabel.setText(str(slider.value()))
            valueLabel.setFixedWidth(100)

            global _self
            _self = self
            exec('slider.valueChanged.connect(lambda x: _self.f' + str(index) + '(x))')

            box = QHBoxLayout()
            box.addWidget(label)
            label.setMaximumHeight(15)
            slider.setMaximumHeight(15)
            valueLabel.setMaximumHeight(15)
            box.addWidget(slider)
            box.addWidget(valueLabel)
            box.setContentsMargins(0,0,0,0)

            if i != 'time':
                self.servoValueSliders.append(slider)
                self.servoValueLabels.append(valueLabel)
                self.ui.verticalLayoutServoPositions.addLayout(box)

            else:
                self.timeSlider = slider
                self.timeLabel = valueLabel
                self.ui.horizontalLayoutTime.addLayout(box)

        self.poses = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

        """
        self.animations = [{0: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 18: [18, 38, 56, 0, 0, 0, 0, 0, 0, 0, 0, 0], 76: [80, 0, 30, 0, 0, 0, 0, 0, 0, 0, 0, 0]},

                           {0: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                            256: [256, 256, 256, 256, 256, 256, 256, 256, 256, 256, 256, 256],
                            18: [18, 38, 56, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                            165: [113, 101, 71, 126, 34, 126, 126, 126, 126, 126, 126, 126],
                            151: [153, 106, 124, 106, 0, 106, 106, 106, 106, 106, 106, 106],
                            177: [131, 121, 95, 143, 95, 113, 173, 95, 167, 60, 220, 89],
                            76: [80, 0, 30, 0, 0, 0, 0, 0, 0, 0, 0, 0]}
                           ]


        self.animation = self.animations[1]

        self.mins = [150, 160, 170, 0, 0, 150, 150, 150, 150, 0, 645, 150, 150, 150, 150, 150]
        self.maxs = [560, 570, 580, 570, 367, 550, 550, 550, 550, 603, 179, 550, 550, 550, 550, 550]
        self.offsets = [0.0341796875, 0.0, -0.1591796875, 0.0009765625, -0.07666015625, -0.013671875, -0.115234375,
                        0.115234375, 0.0341796875, -0.0029296875, -0.03759765625, 0.0, 0, 0, 0, 0]
        """

        self.mins = [150, 160, 170, 0, 0, 150, 150, 150, 150, 0, 645, 150, 150, 150, 150, 150]
        self.maxs = [560, 570, 580, 570, 367, 550, 550, 550, 550, 603, 179, 550, 550, 550, 550, 550]
        self.offsets = [0.0341796875, 0.0, -0.1591796875, 0.0009765625, -0.07666015625, -0.013671875, -0.115234375,
                        0.115234375, 0.0341796875, -0.0029296875, -0.03759765625, 0.0, 0, 0, 0, 0]
        self.animation = {0: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                          256: [256, 256, 256, 256, 256, 256, 256, 256, 256, 256, 256, 256],
                          177: [131, 121, 95, 143, 95, 113, 173, 95, 167, 60, 220, 89]}

        self.ui.horizontalSliderMin.valueChanged.connect(self.minChanged)
        self.ui.horizontalSliderMax.valueChanged.connect(self.maxChanged)
        self.ui.horizontalSliderOffset.valueChanged.connect(self.offsetChanged)
        self.ui.horizontalSliderPos.valueChanged.connect(self.posChanged)
        self.ui.pushButtonDumpValues.clicked.connect(self.dumpValues)
        self.ui.pushButtonZeroPos.clicked.connect(lambda : self.ui.horizontalSliderPos.setValue(1024))
        self.ui.pushButtonDeleteKey.clicked.connect(self.deleteCurrKey)

        for i in range(len(self.mins)): self.servoChanged(i)

        self.servoChanged(0)

        def save():
            print('  self.mins =', self.mins)
            print('  self.maxs =', self.maxs)
            print('  self.offsets =', self.offsets)
            print('  self.animation =', self.animation)

        def reset():
            print('reset')

        self.ui.pushButtonSave.clicked.connect(save)
        self.ui.pushButtonReset.clicked.connect(reset)

        self.ui.pushButtonPrevKey.clicked.connect(lambda : self.timeSlider.setValue(self.getCurrKeyPair()[0]))
        self.ui.pushButtonNextKey.clicked.connect(lambda : self.timeSlider.setValue(self.getCurrKeyPair(cmp='>')[1]))

        self.inTime = False

        for i in range(len(self.servoValueSliders)): self.servoSliderChanged(i, 0)

        # self.consoleVariables = {"canvas": self.canvas, "animation": self.animation}
        # self.console = ConsoleWidget(self, self.consoleVariables)
        # self.ui.consoleLayout.addWidget(self.console)

        global gui
        gui = self
        self.pythonshell = internalshell.InternalShell(self, namespace=globals(), commands=[], multithreaded=False,light_background=False)
        self.ui.consoleLayout.addWidget(self.pythonshell)

        """
        file = open('perspective', 'r')
        self.state = file.read()
        print(self.state)
        print('ret', self.restoreState(QByteArray(self.state)))
        file.close()
        """
        try:
            dasd
            UI_VERSION = 1
            programname = os.path.basename(__file__)
            programbase, ext = os.path.splitext(programname)

            print(programbase)

            settings = QSettings("company", programbase)  # http://pyqt.sourceforge.net/Docs/PyQt4/pyqt_qsettings.html

            #self.restoreGeometry(settings.value("geometryMain"))
            self.ui.restoreGeometry(settings.value("geometry"))
            self.ui.restoreState(settings.value("state"), UI_VERSION)
            self.ui.keyValueGrapDockWidget.restoreGeometry(settings.value("keyValueGrapDockWidget"))

        except: pass

        print(self.geometry())



        #self.showMaximized()


    def closeEvent(self, event):
        """
        file = QFile('perspective')
        file.open(QIODevice.WriteOnly)
        file.write(self.saveState())
        file.close()
        """
        UI_VERSION = 1  # increment this whenever the UI changes significantly

        programname = os.path.basename(__file__)
        programbase, ext = os.path.splitext(programname)  # extract basename and ext from filename
        settings = QSettings("company", programbase)
        #settings.setValue("geometryMain", self.saveGeometry())  # save window geometry
        settings.setValue("geometry", self.ui.saveGeometry())  # save window geometry
        settings.setValue("state", self.ui.saveState(UI_VERSION))  # save settings (UI_VERSION is a constant you should increment when your UI changes significantly to prevent attempts to restore an invalid state.)
        settings.setValue("keyValueGrapDockWidget", self.ui.keyValueGrapDockWidget.saveGeometry())
        #settings.setValue("mainWinGeom", self.get)



    def deleteCurrKey(self):
        self.animation.pop(self.getClosestKey())
        self.canvas.paintGL()
        self.canvas.swapBuffers()
        self.canvas.repaint()

    def center(self):
        frameGm = self.frameGeometry()
        screen = QtGui.QApplication.desktop().screenNumber(QtGui.QApplication.desktop().cursor().pos())
        centerPoint = QtGui.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def getCurrKeyPair(self, value=None, cmp = '>=', justIndex = False):
        if value is None: value = self.timeSlider.value()
        keys = list(self.animation.keys())
        keys.sort() #@TODO store keys in self already sorted!
        for i in range(len(keys)):
            if get_truth(keys[i], cmp, value):
                if justIndex: return i
                return (keys[i - 1], keys[i])

    def getClosestKey(self, value=None, cmp = '>='):
        if value is None: value = self.timeSlider.value()
        pair = self.getCurrKeyPair(value=value)
        if pair is None: return None
        if value - pair[0] < pair[1] - value: return pair[0]
        return pair[1]

    def getOrderedKeysValues(self):
        # """ Code duplication, also in ServosPosGraph
        keys = list(self.animation.keys())
        if keys == []: return (None, None)
        values = list(self.animation.values())
        s = sorted(zip(keys, values))
        valuesOrdered = []
        for p in list(s)[0][1]: valuesOrdered += [[]]
        for (t, y) in s:
            for i in range(len(y)): valuesOrdered[i] += [y[i]]
        keys.sort()
        return (keys, valuesOrdered)

    def servoSliderChanged(self, index, value):
        t = self.timeSlider.value()

        if index == self.names.index('time'):

            self.timeLabel.setText(str(value))

            self.ui.labelKey.setText('Key: ' + str(self.getCurrKeyPair(justIndex = True)))

            keyPair = self.getCurrKeyPair()
            if keyPair is None: return
            self.inTime = True
            A = self.animation[keyPair[0]]
            B = self.animation[keyPair[1]]

            keys, values = self.getOrderedKeysValues()

            if self.interpolationMode == 0:

                for i in range(len(A)):

                    try:
                        s = splrep(np.ndarray(shape=(len(keys),), buffer=np.array(keys), dtype=int),
                                   np.ndarray(shape=(len(keys),), buffer=np.array(values[i]), dtype=int))

                        self.servoValueSliders[i].setValue(splev(t, s))

                    except:

                        intp = interp1d((keyPair[0], keyPair[1]), (A[i], B[i]))
                        self.servoValueSliders[i].setValue(intp(t))
            else:
                for i in range(len(A)):
                    intp = interp1d((keyPair[0], keyPair[1]), (A[i], B[i]))
                    self.servoValueSliders[i].setValue(intp(t))

            self.inTime = False

        else:
            #print('self.inTime', self.inTime)
            if self.inTime: return

            self.servoValueLabels[index].setText(str(value))
            self.animation[t] = []

            values = []

            for i in self.servoValueSliders: values += [i.value()]

            self.animation[t] = values

        self.canvas.paintGL()
        self.canvas.swapBuffers()
        self.canvas.repaint()

    def minChanged(self, value):
        self.ui.labelMin.setText('Min: ' + str(value))
        self.mins[self.currServo] = value
        self.setServo()

    def maxChanged(self, value):
        self.ui.labelMax.setText('Max: ' + str(value))
        self.maxs[self.currServo] = value
        self.setServo()

    def servoChanged(self, value):
        #print('Servo ', value)
        self.currServo = value
        self.ui.horizontalSliderMin.setValue(self.mins[value])
        self.ui.horizontalSliderMax.setValue(self.maxs[value])
        self.ui.horizontalSliderOffset.setValue(int((float(self.offsets[self.currServo]) + 0.5) * float(self.ui.horizontalSliderOffset.maximum())))
        self.ui.horizontalSliderPos.setValue((self.poses[self.currServo] + 0.5) * float(self.ui.horizontalSliderPos.maximum()))
        self.setServo()

    def offsetChanged(self, value):
        v = float(value) / float(self.ui.horizontalSliderOffset.maximum()) - 0.5
        self.offsets[self.currServo] = v
        self.ui.labelOffset.setText('Offset: ' + str(v))
        self.setServo()

    def posChanged(self, value):
        self.v = float(value) / float(self.ui.horizontalSliderPos.maximum()) - 0.5
        self.ui.labelPos.setText('Pos: ' + str(self.v))
        self.poses[self.currServo] = self.v
        self.setServo()

    def setServo(self, i=None, u=None):
        i = self.currServo
        u = self.poses[i]
        o = 0.5 + u + self.offsets[i]
        #print('o' + str(o))
        u = max(0, min(1.0, o))
        v = self.mins[i] + float(self.maxs[i] - self.mins[i]) * (1.0 + u) * 0.5;

        try:
            self.ui.labelServoName.setText(self.names[self.currServo] + ' value: ' + str(int(v)))
        except:
            pass

        c = "1 " + str(int(i)) + " " + str(int(v)) + "\r\n"
        #print(c)

        """

        try:
            if s is None: return

            s.write(_str(c))

            s.write(_str('2 1\r\n'))
            r = str(s.readline()).strip()
            print('r', r)

        except: pass
        """
        #s.write(_str('3 0\r\n'))

        #s.write("1 " + _str(int(i)) + " " + _str(int(v)) + "\r\n")


    def dumpValues(self):
        print('self.mins =', self.mins)
        print('self.maxs =', self.maxs)
        print('self.offsets =', self.offsets)
        print('self.poses =',self.poses)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = ServoAdjustment()
    window.show()
    window.raise_()

    sys.exit(app.exec_())
