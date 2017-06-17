import os
import operator
import time
from time import sleep
from PyQt4 import uic, QtGui
from PyQt4.QtCore import Qt, QTimer, QSettings, QEvent
from PyQt4.QtGui import QMainWindow, QHBoxLayout, QLabel, QSpinBox, QSlider, QCheckBox, QDockWidget
from scipy.interpolate import interp1d
from scipy.interpolate import splrep, splev, UnivariateSpline
from ServosPosGraph import ServosPosGraph
from GlutonView import GlutonView
from spyderlib.widgets import internalshell
import numpy as np
import sys
sys.path.append('/anaconda/lib/python3.5/site-packages')
import serial

#"""
servoOut = None
#try: s = serial.Serial(port='/dev/cu.wchusbserial1420', baudrate=115200)
#try: s = serial.Serial(port='/dev/cu.usbmodem1411', baudrate=115200)
#try: s = serial.Serial(port='/dev/cu.usbserial-A700JNGX', baudrate=115200)
try: servoOut = serial.Serial(port='/dev/cu.usbserial-AI041TLS', baudrate=115200)
except: pass
#"""

def _str(s): return str.encode(str(s))

gui = None

splash = None
progressBar = None

class GLuton(QMainWindow):
    """GLuton is here!"""

    def __init__(self):
        super(GLuton, self).__init__()
        self.ui = uic.loadUi("gluton.ui", self)
        self.ui.show()

        self.setWindowTitle('Gluton')
        self.sliders = []
        self.glutonCanvas = GlutonView(self)
        self.canvas = ServosPosGraph(self)
        self.ui.canvasLayout.addWidget(self.canvas)
        self.ui.glutonViewLayout.addWidget(self.glutonCanvas)

        self.settingKeyPos = False
        self.inServoOrTimeSliderChange = False
        self.closestKeyValue = None
        self.allowGlutonCanvasRedraw = True
        self.inTime = False
        self.copyBuffer = None # type: list
        self.playing = False
        self.interpolationMode = 0
        self.currBeingEdited = 0
        """The index of the slider currently being edited or having the mouse over the key value slider"""
        self.servoPositionSliders = []
        self.timeSlider = None  # type: QSlider
        self.timeLabel = None   # type: QSlider
        self.timer = None       # type: QTimer
        self.servoPosGraphShowServo = []
        self.servoEnabledState = []
        self.servoNames = ['Left Ankle', 'Left Knee', 'Left Hip', 'Left Shoulder', 'Left Elbow', 'Left Wrist',
                           'Right Ankle', 'Right Knee', 'Right Hip', 'Right Shoulder', 'Right Elbow', 'Right Wrist',
                           'time']

        self.maxTime = 128

        self.poses = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        self.mins = [137, 197, 125, 120, 157, 131, 279, 171, 144, 167, 135, 150, 150, 150, 150, 150]
        self.maxs = [414, 527, 558, 525, 593, 560, 531, 547, 581, 550, 577, 550, 550, 550, 550, 550]
        self.offsets = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0, 0]

        self.curves = [[[0, 256], [137, 134]], [[0, 45, 256], [209, 180, 206]], [[0, 45, 256], [130, 149, 129]], [[0, 256], [205, 201]], [[0, 256], [73, 71]], [[0, 256], [193, 190]], [[0, 256], [205, 205]], [[0, 45, 256], [195, 175, 193]],
                       [[0, 45, 256], [126, 159, 125]], [[0, 256], [41, 48]], [[0, 256], [177, 180]], [[0, 256], [192, 190]]]

        # Walks, a little wobbeling
        self.curves = [[[0, 89, 124, 139, 161, 183, 203, 216, 226, 256], [132, 143, 181, 182, 182, 190, 147, 131, 130, 134]], [[0, 45, 89, 139, 161, 183, 203, 216, 256], [209, 180, 177, 183, 212, 227, 227, 227, 206]],
                       [[0, 45, 89, 139, 161, 183, 203, 216, 256], [123, 149, 150, 145, 122, 97, 115, 117, 123]], [[0, 89, 139, 161, 183, 203, 216, 256], [205, 204, 203, 203, 203, 203, 203, 201]],
                       [[0, 89, 139, 161, 183, 203, 216, 256], [73, 72, 71, 71, 71, 71, 71, 71]], [[0, 89, 139, 161, 183, 203, 216, 256], [193, 192, 191, 191, 191, 191, 191, 190]],
                       [[0, 89, 124, 139, 161, 183, 203, 216, 256], [211, 192, 123, 169, 169, 169, 190, 209, 211]], [[0, 45, 89, 139, 161, 183, 203, 216, 256], [195, 175, 163, 169, 198, 233, 221, 233, 201]],
                       [[0, 45, 89, 124, 139, 161, 183, 203, 216, 256], [135, 167, 167, 167, 167, 137, 116, 104, 96, 135]], [[0, 89, 139, 161, 183, 203, 216, 256], [41, 42, 43, 43, 43, 43, 43, 48]],
                       [[0, 89, 139, 161, 183, 203, 216, 256], [177, 177, 177, 177, 177, 177, 177, 180]], [[0, 89, 139, 161, 183, 203, 216, 256], [192, 191, 190, 190, 190, 190, 190, 190]]]

        self.curves = [[[0, 45, 89, 124, 139, 161, 183, 203, 216, 226, 256], [132, 149, 143, 181, 182, 182, 190, 147, 131, 130, 134]], [[0, 45, 89, 139, 161, 183, 203, 216, 256], [205, 172, 177, 183, 212, 227, 227, 227, 205]],
                       [[0, 45, 89, 139, 161, 183, 203, 216, 256], [130, 149, 150, 145, 122, 97, 115, 117, 130]], [[0, 45, 89, 139, 161, 183, 203, 216, 256], [205, 175, 163, 203, 203, 203, 203, 203, 201]],
                       [[0, 45, 89, 139, 161, 183, 203, 216, 256], [73, 59, 72, 71, 71, 71, 71, 71, 71]], [[0, 89, 139, 161, 183, 203, 216, 256], [193, 192, 191, 191, 191, 191, 191, 190]],
                       [[0, 22, 89, 124, 139, 161, 183, 203, 216, 256], [237, 232, 192, 123, 169, 169, 169, 190, 209, 237]], [[0, 45, 89, 139, 161, 183, 203, 216, 256], [195, 175, 163, 169, 198, 233, 221, 233, 201]],
                       [[0, 45, 89, 124, 139, 161, 183, 203, 216, 256], [129, 167, 167, 167, 167, 137, 116, 104, 96, 129]], [[0, 45, 89, 139, 161, 183, 203, 216, 256], [41, 3, 16, 43, 43, 43, 43, 43, 48]],
                       [[0, 45, 89, 139, 161, 183, 203, 216, 256], [177, 149, 157, 177, 177, 177, 177, 177, 180]], [[0, 89, 139, 161, 183, 203, 216, 256], [192, 191, 190, 190, 190, 190, 190, 190]]]

        self.setupMenuBarEvents()

        self.setupServos()

        self.setupKeyManagementEvents()

        self.setupServoAdjustmentEvents()

        self.updateServoSliders()

        self.setupPlayAnimationEvents()

        self.setupInterpolationEvents()

        self.setupPythonConsole()

        self.setupGlutonCanvasEvents()

        try:

            UI_VERSION = 1
            programname = os.path.basename(__file__)
            programbase, ext = os.path.splitext(programname)

            print(programbase)

            settings = QSettings("company", programbase)  # http://pyqt.sourceforge.net/Docs/PyQt4/pyqt_qsettings.html

            # self.restoreGeometry(settings.value("geometryMain"))
            self.ui.restoreGeometry(settings.value("geometry"))
            self.ui.restoreState(settings.value("state"), UI_VERSION)
            self.ui.keyValueGrapDockWidget.restoreGeometry(settings.value("keyValueGrapDockWidget"))

        except:
            pass

        self.showMaximized()

        QtGui.qApp.installEventFilter(self)

        #splash.hide()

    def setupMenuBarEvents(self):

        def save():
            print('  self.mins =', self.mins)
            print('  self.maxs =', self.maxs)
            print('  self.offsets =', self.offsets)
            #print('  self.animation =', self.animation)
            print('  self.curves = ', self.curves)

        self.ui.actionSave.triggered.connect(save)

        def showHideKeyValueGraph():
            if self.ui.actionKeyValueGraph.isChecked(): self.ui.keyValueGrapDockWidget.show()
            else:                                       self.ui.keyValueGrapDockWidget.hide()

        self.ui.actionKeyValueGraph.triggered.connect(showHideKeyValueGraph)

        self.ui.keyValueGrapDockWidget.visibilityChanged.connect(lambda visiable: self.ui.actionKeyValueGraph.setChecked(visiable))

        def showHideKeyFrameEditor():
            if self.actionKeyFrameEditor.isChecked():   self.ui.keyFrameEditorDockWidget.show()
            else:                                       self.ui.keyFrameEditorDockWidget.hide()

        self.ui.actionKeyFrameEditor.triggered.connect(showHideKeyFrameEditor)

        self.ui.keyFrameEditorDockWidget.visibilityChanged.connect(lambda visiable: self.ui.actionKeyFrameEditor.setChecked(visiable))

        def showHideConsole():
            if self.actionConsole.isChecked():  self.ui.consoleDockWidget.show()
            else:                               self.ui.consoleDockWidget.hide()

        self.ui.actionConsole.triggered.connect(showHideConsole)

        self.ui.consoleDockWidget.visibilityChanged.connect(lambda visiable: self.ui.actionConsole.setChecked(visiable))

        def showHideServoAdjustment():
            if self.actionConsole.isChecked():  self.ui.servoAdjustmentDockWidget.show()
            else:                               self.ui.servoAdjustmentDockWidget.hide()

        self.ui.actionServoAdjustment.triggered.connect(showHideServoAdjustment)

        self.ui.servoAdjustmentDockWidget.visibilityChanged.connect(lambda visiable: self.ui.actionServoAdjustment.setChecked(visiable))

    def setupServos(self):
        """Create the sliders for the servos and time slider, labels and spin boxes. Connect events to glue logic"""
        for sliderName in self.servoNames: self.servoPosGraphShowServo += [True]

        # Loop over all the servos and add the key value slides, labels, spin boxes, and key value graph pos enabled checkboxes
        for sliderName, index in zip(self.servoNames, range(0, len(self.servoNames))):

            class ServoSlider(QSlider):
                """Servo slider object"""
                def __init__(self, gluton: GLuton, direction, parent=None):
                    super(ServoSlider, self).__init__(direction, parent)
                    self.setMouseTracking(True)
                    self.number = index
                    self.gluton = gluton

                def enterEvent(self, event: QEvent):
                    """Take note of the current servo being edit when the mouse enters this widget and update display"""
                    self.gluton.currBeingEdited = self.number
                    self.gluton.glutonCanvas.highlightServo(self.gluton.servoNames[self.number])
                    self.gluton.glutonCanvas.glDraw()
                    self.gluton.canvas.glDraw()

                def leaveEvent(self, event: QEvent):
                    self.gluton.glutonCanvas.unhighlightLastServo()
                    self.gluton.glutonCanvas.glDraw()

            slider = ServoSlider(self, Qt.Horizontal)  # Create the slider

            slider.setMaximum(256)

            slider.valueChanged.connect(lambda value, _index = index: self.servoSliderChanged(_index, value))

            self.sliders += [slider]

            # Create a spin box which is connected to the slider
            spinBox = QSpinBox()
            spinBox.setValue(slider.value())
            spinBox.setMaximum(256)
            spinBox.setFixedWidth(45)

            # When the slider is changed, reflect the change in the associated spin box
            slider.valueChanged.connect(lambda value, box=spinBox: box.setValue(value))

            # When the spin box is changed reflect the change in the assoicated slider
            def valueChanged(s, value: int):
                if self.inServoOrTimeSliderChange: return
                s.setValue(value)

            # Connect spin box to above function
            spinBox.valueChanged.connect(lambda value, s=slider: valueChanged(s, value))

            box = QHBoxLayout()

            if sliderName != 'time':
                servoEnabled = QCheckBox()
                servoEnabled.setChecked(False)
                box.addWidget(servoEnabled)
                self.servoEnabledState += [servoEnabled]

            label = QLabel()
            label.setText(sliderName + ':')
            label.setFixedWidth(100)
            label.setMaximumHeight(15)
            label.setAlignment(Qt.AlignRight)
            box.addWidget(label)

            slider.setMaximumHeight(15)
            spinBox.setMaximumHeight(15)
            box.addWidget(slider)
            box.addWidget(spinBox)
            box.setContentsMargins(0, 0, 0, 0)

            # Time slider is different from the servo sliders, it does not need the show in position graph check box
            if sliderName != 'time':
                showInPosGraph = QCheckBox()
                showInPosGraph.setChecked(True)

                def stateChanged(sliderIndex, state):
                    self.servoPosGraphShowServo[sliderIndex] = state != 0
                    self.canvas.glDraw()

                showInPosGraph.stateChanged.connect(lambda state, sliderName=sliderName: stateChanged(self.servoNames.index(sliderName), state))

                box.addWidget(showInPosGraph)
                self.servoPositionSliders.append(slider)
                self.ui.verticalLayoutServoPositions.addLayout(box)

            else:
                #Handle time slider case
                self.timeSlider = slider
                self.timeLabel = spinBox
                self.ui.horizontalLayoutTime.addLayout(box)

    def setupServoAdjustmentEvents(self):
        """Setup servo range adjustment events and glue logic"""

        def servoChanged(value: int):
            self.currServo = value
            self.ui.horizontalSliderMin.setValue(self.mins[value])
            self.ui.horizontalSliderMax.setValue(self.maxs[value])
            self.ui.horizontalSliderOffset.setValue(int((float(self.offsets[self.currServo]) + 0.5) * float(self.ui.horizontalSliderOffset.maximum())))
            self.ui.horizontalSliderPos.setValue((self.poses[self.currServo] + 0.5) * float(self.ui.horizontalSliderPos.maximum()))
            self.setServo()

        self.ui.spinBoxServo.valueChanged.connect(servoChanged)

        """
        for i in range(len(self.mins)):
            servoChanged(i)
            sleep(0.2)

        servoChanged(0)
        """

        def minChanged(value: int):
            self.ui.labelMin.setText('Min: ' + str(value))
            self.mins[self.currServo] = value
            self.setServo()

        self.ui.horizontalSliderMin.valueChanged.connect(minChanged)

        def maxChanged(value: int):
            self.ui.labelMax.setText('Max: ' + str(value))
            self.maxs[self.currServo] = value
            self.setServo()

        self.ui.horizontalSliderMax.valueChanged.connect(maxChanged)

        def offsetChanged(value: int):
            v = float(value) / float(self.ui.horizontalSliderOffset.maximum()) - 0.5
            self.offsets[self.currServo] = v
            self.ui.labelOffset.setText('Offset: ' + "{0:.4f}".format(v))
            self.setServo()

        self.ui.horizontalSliderOffset.valueChanged.connect(offsetChanged)

        def posChanged(value: int):
            v = float(value) / float(self.ui.horizontalSliderPos.maximum()) - 0.5
            self.ui.labelPos.setText('Pos: ' + "{0:.4f}".format(v))
            self.poses[self.currServo] = v
            self.setServo()

        self.ui.horizontalSliderPos.valueChanged.connect(posChanged)

        self.ui.pushButtonZeroPos.clicked.connect(lambda: self.ui.horizontalSliderPos.setValue(1024))
        self.ui.zeroOffsetButton.clicked.connect(lambda: self.ui.horizontalSliderOffset.setValue(1024))

    def setupKeyManagementEvents(self):

        def copyPrevKey():
            """Copies key previous to the current time and inserts it at the current time."""
            pair = self.getCurrKeyPair()
            if pair is None: return
            print(pair)
            values = self.getServoValues(pair[0])
            for i in range(len(self.curves)):
                self.servoPositionSliders[i].setValue(values[i])
                self.servoSliderChanged(i, values[i])

        self.ui.copyPrevKeyButton.clicked.connect(copyPrevKey)

        def keyPosChanged(newTimePos: int):
            """
            Moves the current closest key to a new position
            :param newTimePos: The time to move the key to
            :type newTimePos: int
            """
            if self.settingKeyPos: return
            self.animation[newTimePos] = self.animation.pop(self.canvas.closestKey)
            self.canvas.glDraw()
            self.timeSlider.setValue(newTimePos)  # Updating the time slider will update the state of everything

        self.ui.keyPosSlider.valueChanged.connect(keyPosChanged)

        def deleteCurrKey():
            closestKey = self.getClosestKey()
            for curve in self.curves:
                xValues = curve[0]
                yValues = curve[1]
                for i in range(len(xValues)):
                    if xValues[i] != closestKey: continue
                    del xValues[i]
                    del yValues[i]
                    break

            self.canvas.glDraw()

        self.ui.pushButtonDeleteKey.clicked.connect(deleteCurrKey)

        def jumpToKey(key: int):
            self.canvas.closestKey = key
            self.timeSlider.setValue(key)

        self.ui.pushButtonPrevKey.clicked.connect(lambda: jumpToKey(self.getCurrKeyPair()[0]))

        def next():
            pair = self.getCurrKeyPair(cmp='>')
            if pair is None:    jumpToKey(0)
            else:               jumpToKey(pair[1])

        self.ui.pushButtonNextKey.clicked.connect(next)

        def copy():
            self.copyBuffer = []
            for slider in self.sliders: self.copyBuffer += [slider.value()]

        self.ui.copyButton.clicked.connect(copy)

        def paste():
            if self.copyBuffer is None: return
            for i in range(len(self.copyBuffer)): self.sliders[i].setValue(self.copyBuffer[i])

        self.ui.pasteButton.clicked.connect(paste)

        def keyAll():
            for i in range(len(self.curves)): self.servoSliderChanged(i, self.servoPositionSliders[i].value())

        self.ui.keyAllButton.clicked.connect(keyAll)

        def moveKeys(delta):
            t = self.timeSlider.value()
            for curve in self.curves:
                xValues = curve[0]
                yValues = curve[1]
                for i in range(len(xValues) - 1):
                    if xValues[i] < t: continue
                    xValues[i] += delta
            self.updateServoSliders()
            self.canvas.glDraw()

        self.ui.moveLeftButton.clicked.connect(lambda : moveKeys(-2))
        self.ui.moveRightButton.clicked.connect(lambda : moveKeys(2))

    def playPause(self):
        if self.playing:
            self.timer.stop()
            self.ui.playButton.setText(">")
        else:
            self.timer.start(self.ui.intervalSpinBox.value())
            self.ui.playButton.setText("||")
        self.playing = not self.playing

    def eventFilter(self, source, event):
        if self.pythonshell.underMouse() and self.pythonshell.hasFocus(): return super(GLuton, self).eventFilter(source,
                                                                                                                 event)

        if event.type() == QEvent.KeyPress and event.key() == 32: self.playPause()

        return super(GLuton, self).eventFilter(source, event)

    def setupPlayAnimationEvents(self):

        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self.timeSlider.setValue((self.timeSlider.value() + self.ui.stepSpinBox.value()) % self.timeSlider.maximum()))

        self.ui.playButton.clicked.connect(self.playPause)

        self.ui.intervalSpinBox.valueChanged.connect(lambda value: self.timer.setInterval(value))

        def servosEnabled(state):
            for i in self.servoEnabledState: i.setCheckState(state)

        self.ui.servosEnabledCheckBox.stateChanged.connect(servosEnabled)

    def setupInterpolationEvents(self):

        self.ui.interpolationComboBox.addItems(['B-Spline', 'Univariate Spline', 'Interpolated Univariate Spline', '1D'])

        def setMode(mode: int):
            self.interpolationMode = mode
            self.glutonCanvas.glDraw()
            self.canvas.glDraw()

        self.ui.interpolationComboBox.activated.connect(setMode)

    def setupPythonConsole(self):
        global gui
        gui = self
        self.pythonshell = internalshell.InternalShell(self, namespace=globals(), commands=[], multithreaded=False,
                                                       light_background=False)
        self.ui.consoleLayout.addWidget(self.pythonshell)

    def setupGlutonCanvasEvents(self):
        self.ui.sideButton  .clicked.connect(lambda : self.glutonCanvas.setSide())
        self.ui.frontButton .clicked.connect(lambda : self.glutonCanvas.setFront())
        self.ui.topButton   .clicked.connect(lambda : self.glutonCanvas.setTop())
        self.ui.angledButton.clicked.connect(lambda : self.glutonCanvas.setAngled())

        self.ui.perspectiveCheckBox.stateChanged.connect(lambda state: self.glutonCanvas.setRenderPerspective(state))
        self.ui.moveGridCheckBox.stateChanged.connect(lambda state: self.glutonCanvas.setMoveGrid(state))

    def closeEvent(self, event: QEvent):
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

    def center(self):
        frameGm = self.frameGeometry()
        screen = QtGui.QApplication.desktop().screenNumber(QtGui.QApplication.desktop().cursor().pos())
        centerPoint = QtGui.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def getCurrKeyPair(self, value=None, cmp = '>=', justIndex = False):

        def getTruth(inp, relate, cut):
            ops = {'>': operator.gt,
                   '<': operator.lt,
                   '>=': operator.ge,
                   '<=': operator.le,
                   '=': operator.eq}
            return ops[relate](inp, cut)

        if value is None: value = self.timeSlider.value()
        keys = set()
        for i in self.curves:
            for j in i[0]: keys.add(j)

        keys = list(keys)
        keys.sort()
        for i in range(len(keys)):
            if getTruth(keys[i], cmp, value):
                if justIndex: return i
                return (keys[i - 1], keys[i])

    def getClosestKey(self, value=None):
        if value is None: value = self.timeSlider.value()
        pair = self.getCurrKeyPair(value=value)
        if pair is None: return None
        if value - pair[0] < pair[1] - value: return pair[0]
        return pair[1]

    def getServoValues(self, t):
        ret = []
        for i in range(len(self.curves)):
            curve = self.curves[i]
            xValues = curve[0]
            yValues = curve[1]
            try:
                ddd
                s = splrep(np.ndarray(shape=(len(xValues),), buffer=np.array(xValues), dtype=int),
                           np.ndarray(shape=(len(xValues),), buffer=np.array(yValues), dtype=int))

                ret += [splev(t, s)]

            except:
                for j in range(len(xValues)):
                    if xValues[j] < t: continue
                    intp = interp1d((xValues[j - 1], xValues[j]), (yValues[j - 1], yValues[j]))
                    ret += [intp(t)]
                    break
        return ret

    def updateServoSliders(self):

        self.inTime = True

        t = self.timeSlider.value()

        values = self.getServoValues(t)

        for i in range(len(self.curves)): self.servoPositionSliders[i].setValue(values[i])

        self.inTime = False

    def servoSliderChanged(self, index: int, value: int, t = None):

        self.inServoOrTimeSliderChange = True

        if index == self.servoNames.index('time'):

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

                if self.servoEnabledState[index].isChecked(): self.setServo(index, (value / 255.0) - 0.5)

                self.glutonCanvas.servos[self.servoNames[index]].setAngle(((value / 255.0) - 0.5) * 180.0)

                if self.allowGlutonCanvasRedraw: self.glutonCanvas.glDraw()

            except:
                pass

            if self.inTime:
                self.inServoOrTimeSliderChange = False
                return

            if t is None: t = self.timeSlider.value()

            curve = self.curves[index]

            xValues = curve[0]
            yValues = curve[1]

            foundIt = False

            for i in range(len(xValues)):
                if xValues[i] != t: continue
                foundIt = True
                yValues[i] = self.servoPositionSliders[index].value()
                break

            if not foundIt:
                for i in range(len(xValues)):
                    if xValues[i] < t: continue
                    xValues.insert(i, t)
                    yValues.insert(i, self.servoPositionSliders[index].value())
                    break

            if t == 0: self.servoSliderChanged(index, value, 256)

        self.inServoOrTimeSliderChange = False

        if self.allowGlutonCanvasRedraw : self.canvas.glDraw()

        self.allowGlutonCanvasRedraw = True

    def getServoValue(self, i: int, u: float):
        o = 0.5 + u + self.offsets[i]
        u = max(0, min(1.0, o))
        return self.mins[i] + float(self.maxs[i] - self.mins[i]) * u

    def setServo(self, i=None, u=None):
        if i is None: i = self.currServo
        if u is None: u = self.poses[i]
        v = self.getServoValue(i, u)

        try: self.ui.labelServoName.setText(self.servoNames[i] + ' value: ' + str(int(v)))
        except: pass



        #c = "1 " + str(int(i)) + " " + str(int(v)) + "\r\n"
        c = "1 " + str(int(i)) + " " + str(int(v)) + "\n"
        #print(c)

        #"""

        try:
            if servoOut is None: return

            servoOut.write(_str(c))

            #s.write(_str('2 1\r\n'))
            #s.write(_str('2 1\n'))
            #r = str(s.readline()).strip()
            #print('r', r)

        except: pass
        #"""
        #s.write(_str('3 0\r\n'))

        #s.write("1 " + _str(int(i)) + " " + _str(int(v)) + "\r\n")

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    """
    # Create and display the splash screen
    splash_pix = QPixmap('logo.png')
    global splash
    global progressBar
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    # adding progress bar
    progressBar = QProgressBar(splash)

    splash.setMask(splash_pix.mask())

    print('before')
    splash.show()

    print('after')
    """

    window = GLuton()

    """
    for i in range(0, 100):
        progressBar.setValue(i)
        t = time.time()
        while time.time() < t + 0.1:
            app.processEvents()
            """

    # Simulate something that takes time
    #time.sleep(2)

    window.show()
    window.raise_()

    sys.exit(app.exec_())
