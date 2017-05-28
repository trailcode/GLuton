import os
from PyQt4 import uic, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from scipy.interpolate import interp1d
from scipy.interpolate import splrep, splev, UnivariateSpline
from ServosPosGraph import ServosPosGraph
from glutonView import GlutonView
from spyderlib.widgets import internalshell
import numpy as np
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


class _Event(QEvent):
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, callback):
        # thread-safe
        QEvent.__init__(self, _Event.EVENT_TYPE)
        self.callback = callback

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
        self.glutonCanvas = GlutonView(self)
        self.ui.glutonViewLayout.addWidget(self.glutonCanvas)

        self.background_pixmap = QPixmap('logo.png')
        self.settingKeyPos = False
        self.inServoOrTimeSliderChange = False
        self.closestKeyValue = None
        self.allowGlutonCanvasRedraw = True
        def save():
            print('  self.mins =', self.mins)
            print('  self.maxs =', self.maxs)
            print('  self.offsets =', self.offsets)
            print('  self.animation =', self.animation)

        self.ui.actionSave.triggered.connect(save)

        def copyPrevKey():
            pair = self.getCurrKeyPair()
            if pair is None: return
            ani = self.animation[pair[0]]
            for i in range(len(ani)):
                self.servoValueSliders[i].setValue(ani[i])


        self.ui.copyPrevKeyButton.clicked.connect(copyPrevKey)

        def keyPosChanged(value):
            if self.settingKeyPos: return
            self.animation[value] = self.animation.pop(self.canvas.closestKey)
            self.canvas.glDraw()
            self.timeSlider.setValue(value)

        self.ui.keyPosSlider.valueChanged.connect(keyPosChanged)

        self.currBeingEdited = 0

        self.names = ['Left Ankle', 'Left Knee', 'Left Hip', 'Left Shoulder', 'Left Elbow', 'Left Wrist',
                      'Right Ankle', 'Right Knee', 'Right Hip', 'Right Shoulder', 'Right Elbow', 'Right Wrist', 'time']

        self.servoValueSliders = []
        self.servoValueLabels = []
        self.center()

        self.interpolationMode = 0
        self.ui.interpolationComboBox.addItems(['B-Spline', 'Univariate Spline', 'Interpolated Univariate Spline', '1D'])

        def setMode(mode):
            self.interpolationMode = mode
            self.glutonCanvas.glDraw()
            self.canvas.glDraw()

        self.ui.interpolationComboBox.activated.connect(setMode)

        for i,index in zip(self.names, range(0, len(self.names))):
            exec('ServoAdjustment.servoSliderChanged' + str(index) + ' = lambda self, value: self.servoSliderChanged(' + str(index) + ', value)')
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
                    #self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

                def enterEvent(self, event):

                    self.servoAdjustment.currBeingEdited = self.number
                    self.servoAdjustment.canvas.paintGL()
                    self.servoAdjustment.canvas.swapBuffers()
                    self.servoAdjustment.canvas.repaint()
                    #self.setStyleSheet("background-color:#45b545;")

            slider = MySlider(index, self, Qt.Horizontal)
            slider.setMaximum(256)
            self.sliders += [slider]
            spinBox = QSpinBox()
            spinBox.setValue(slider.value())
            spinBox.setMaximum(255)
            spinBox.setFixedWidth(45)

            slider.valueChanged.connect(lambda value, box = spinBox : box.setValue(value))

            def valueChanged(s, value):
                if self.inServoOrTimeSliderChange: return
                s.setValue(value)

            spinBox.valueChanged.connect(lambda value, s = slider: valueChanged(s, value))

            global _self
            _self = self
            exec('slider.valueChanged.connect(lambda x: _self.servoSliderChanged' + str(index) + '(x))')

            box = QHBoxLayout()
            box.addWidget(label)
            label.setMaximumHeight(15)
            slider.setMaximumHeight(15)
            spinBox.setMaximumHeight(15)
            box.addWidget(slider)
            box.addWidget(spinBox)
            box.setContentsMargins(0,0,0,0)

            if i != 'time':
                self.servoValueSliders.append(slider)
                self.servoValueLabels.append(spinBox)
                self.ui.verticalLayoutServoPositions.addLayout(box)

            else:
                self.timeSlider = slider
                self.timeLabel = spinBox
                self.ui.horizontalLayoutTime.addLayout(box)

        self.poses = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

        """
        self.mins = [150, 160, 170, 0, 0, 150, 150, 150, 150, 0, 645, 150, 150, 150, 150, 150]
        self.maxs = [560, 570, 580, 570, 367, 550, 550, 550, 550, 603, 179, 550, 550, 550, 550, 550]
        self.offsets = [0.0341796875, 0.0, -0.1591796875, 0.0009765625, -0.07666015625, -0.013671875, -0.115234375,
                        0.115234375, 0.0341796875, -0.0029296875, -0.03759765625, 0.0, 0, 0, 0, 0]
        self.animation = {0: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                          256: [256, 256, 256, 256, 256, 256, 256, 256, 256, 256, 256, 256],
                          124: [84, 76, 54, 95, 54, 69, 120, 68, 115, 39, 160, 49],
                          62: [45, 42, 33, 50, 33, 39, 60, 56, 58, 21, 77, 31],
                          177: [131, 121, 95, 143, 95, 113, 173, 95, 167, 60, 220, 89]}
                          """

        """
        self.mins = [150, 160, 170, 0, 0, 150, 150, 150, 150, 0, 645, 150, 150, 150, 150, 150]
        self.maxs = [560, 570, 580, 570, 367, 550, 550, 550, 550, 603, 179, 550, 550, 550, 550, 550]
        self.offsets = [0.0341796875, 0.0, -0.1591796875, 0.0009765625, -0.07666015625, -0.013671875, -0.115234375,
                        0.115234375, 0.0341796875, -0.0029296875, -0.03759765625, 0.0, 0, 0, 0, 0]
        self.animation = {0: [128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128],
                          256: [128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128, 128]}
        """

        self.mins = [150, 160, 170, 0, 0, 150, 150, 150, 150, 0, 645, 150, 150, 150, 150, 150]
        self.maxs = [560, 570, 580, 570, 367, 550, 550, 550, 550, 603, 179, 550, 550, 550, 550, 550]
        self.offsets = [0.0341796875, 0.0, -0.1591796875, 0.0009765625, -0.07666015625, -0.013671875, -0.115234375,
                        0.115234375, 0.0341796875, -0.0029296875, -0.03759765625, 0.0, 0, 0, 0, 0]

        self.animation = {0: [127, 126, 159, 89, 127, 127, 125, 126, 91, 165, 127, 127],
                          256: [127, 126, 159, 89, 127, 127, 125, 126, 91, 165, 127, 127],
                          226: [126, 62, 206, 85, 126, 126, 124, 125, 86, 161, 126, 126],
                          42: [128, 124, 119, 142, 128, 128, 127, 21, 162, 110, 128, 128],
                          75: [128, 126, 85, 162, 128, 128, 126, 128, 169, 89, 128, 128],
                          205: [127, 24, 216, 95, 127, 127, 126, 125, 93, 169, 127, 127],
                          110: [122, 100, 90, 161, 122, 122, 125, 127, 131, 89, 122, 122],
                          84: [128, 125, 83, 165, 128, 128, 126, 129, 149, 85, 128, 128],
                          22: [128, 54, 179, 128, 128, 128, 127, 90, 96, 128, 128, 128],
                          60: [127, 125, 93, 162, 127, 127, 127, 19, 232, 89, 127, 127],
                          159: [128, 11, 136, 128, 128, 128, 127, 125, 109, 128, 128, 128]}

        self.ui.horizontalSliderMin.valueChanged.connect(self.minChanged)
        self.ui.horizontalSliderMax.valueChanged.connect(self.maxChanged)
        self.ui.horizontalSliderOffset.valueChanged.connect(self.offsetChanged)
        self.ui.horizontalSliderPos.valueChanged.connect(self.posChanged)
        self.ui.pushButtonZeroPos.clicked.connect(lambda : self.ui.horizontalSliderPos.setValue(1024))
        self.ui.zeroOffsetButton.clicked.connect(lambda : self.ui.horizontalSliderOffset.setValue(1024))
        self.ui.pushButtonDeleteKey.clicked.connect(self.deleteCurrKey)

        for i in range(len(self.mins)): self.servoChanged(i)

        self.servoChanged(0)

        def jumpToKey(key):
            self.canvas.closestKey = key
            self.timeSlider.setValue(key)

        self.ui.pushButtonPrevKey.clicked.connect(lambda : jumpToKey(self.getCurrKeyPair()[0]))
        self.ui.pushButtonNextKey.clicked.connect(lambda : jumpToKey(self.getCurrKeyPair(cmp='>')[1]))

        self.inTime = False

        global gui
        gui = self
        self.pythonshell = internalshell.InternalShell(self, namespace=globals(), commands=[], multithreaded=False,light_background=False)
        self.ui.consoleLayout.addWidget(self.pythonshell)

        try:
            #dsads

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

        self.updateServoSliders()

        self.timer = QTimer()
        self.timer.timeout.connect(lambda : self.timeSlider.setValue((self.timeSlider.value() + 1) % self.timeSlider.maximum()))

        self.playing = False
        def playPause():
            if self.playing:
                self.timer.stop()
                self.ui.playButton.setText(">")
            else:
                self.timer.start(10)
                self.ui.playButton.setText("||")
            self.playing = not self.playing


        self.ui.playButton.clicked.connect(playPause)

        self.copyBuffer = None
        def copy():
            self.copyBuffer = []
            for slider in self.sliders: self.copyBuffer += [slider.value()]

        self.ui.copyButton.clicked.connect(copy)

        def paste():
            if self.copyBuffer is None: return
            for i in range(len(self.copyBuffer)): self.sliders[i].setValue(self.copyBuffer[i])

        self.ui.pasteButton.clicked.connect(paste)

        self.showMaximized()

    def customEvent(self, event):
        # process idle_queue_dispatcher events
        event.callback()

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

    def updateServoSliders(self):
        keyPair = self.getCurrKeyPair()
        if keyPair is None: return
        self.inTime = True

        A = self.animation[keyPair[0]]
        B = self.animation[keyPair[1]]

        keys, values = self.getOrderedKeysValues()

        t = self.timeSlider.value()

        if self.interpolationMode == 0:

            for i in range(len(A)):

                try:
                    s = splrep(np.ndarray(shape=(len(keys),), buffer=np.array(keys), dtype=int),
                               np.ndarray(shape=(len(keys),), buffer=np.array(values[i]), dtype=int))

                    self.servoValueSliders[i].setValue(splev(t, s))

                except:

                    intp = interp1d((keyPair[0], keyPair[1]), (A[i], B[i]))
                    self.servoValueSliders[i].setValue(intp(t))
        elif self.interpolationMode == 1:
            for i in range(len(A)):

                try:
                    s = UnivariateSpline(np.ndarray(shape=(len(keys),), buffer=np.array(keys), dtype=int),
                                         np.ndarray(shape=(len(keys),), buffer=np.array(i), dtype=int), s=100)

                    self.servoValueSliders[i].setValue(s(t))

                except:

                    intp = interp1d((keyPair[0], keyPair[1]), (A[i], B[i]))
                    self.servoValueSliders[i].setValue(intp(t))
        else:
            for i in range(len(A)):
                intp = interp1d((keyPair[0], keyPair[1]), (A[i], B[i]))
                self.servoValueSliders[i].setValue(intp(t))

        self.inTime = False

    def servoSliderChanged(self, index, value):

        self.inServoOrTimeSliderChange = True

        if index == self.names.index('time'):

            self.settingKeyPos = True

            self.ui.keyPosSlider.setValue(self.canvas.closestKey)

            self.closestKeyValue = self.canvas.closestKey

            self.settingKeyPos = False

            self.timeLabel.setValue(value)

            self.ui.labelKey.setText('Key: ' + str(self.getCurrKeyPair(justIndex = True)))

            self.allowGlutonCanvasRedraw = False

            self.updateServoSliders()

            self.glutonCanvas.glDraw()

            self.canvas.glDraw()

        else:

            try:
                v= self.getServoValue(index, value / 255.0) / 700.0 * 360.0
                #self.glutonCanvas.servos[self.names[index]].setAngle(v)
                self.glutonCanvas.servos[self.names[index]].setAngle(((value / 255.0) - 0.5) * 180.0)
                if self.allowGlutonCanvasRedraw: self.glutonCanvas.glDraw()

            except:
                pass

            if self.inTime:
                self.inServoOrTimeSliderChange = False
                return

            t = self.timeSlider.value()

            self.servoValueLabels[index].setValue(value)

            self.animation[t] = []

            values = []

            for i in self.servoValueSliders: values += [i.value()]

            self.animation[t] = values

        self.inServoOrTimeSliderChange = False

        if self.allowGlutonCanvasRedraw : self.canvas.glDraw()

        self.allowGlutonCanvasRedraw = True

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
        self.ui.labelOffset.setText('Offset: ' + "{0:.4f}".format(v))
        self.setServo()

    def posChanged(self, value):
        v = float(value) / float(self.ui.horizontalSliderPos.maximum()) - 0.5
        self.ui.labelPos.setText('Pos: ' + "{0:.4f}".format(v))
        self.poses[self.currServo] = v
        self.setServo()

    def getServoValue(self, i, u):
        o = 0.5 + u + self.offsets[i]
        u = max(0, min(1.0, o))
        return self.mins[i] + float(self.maxs[i] - self.mins[i]) * u

    def setServo(self, i=None, u=None):

        v = self.getServoValue(self.currServo, self.poses[self.currServo])

        try: self.ui.labelServoName.setText(self.names[self.currServo] + ' value: ' + str(int(v)))
        except: pass



        c = "1 " + str(int(self.currServo)) + " " + str(int(v)) + "\r\n"
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

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = ServoAdjustment()
    window.show()
    window.raise_()

    sys.exit(app.exec_())
