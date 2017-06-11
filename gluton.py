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
s = None
#try: s = serial.Serial(port='/dev/cu.wchusbserial1420', baudrate=115200)
try: s = serial.Serial(port='/dev/cu.usbmodem1411', baudrate=115200)
except: pass
#"""

def _str(s): return str.encode(str(s));

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
        self.servoNames = ['Left Ankle', 'Left Knee', 'Left Hip', 'Left Shoulder', 'Left Elbow', 'Left Wrist',
                           'Right Ankle', 'Right Knee', 'Right Hip', 'Right Shoulder', 'Right Elbow', 'Right Wrist',
                           'time']

        self.poses = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        self.mins = [150, 160, 170, 0, 0, 150, 150, 150, 150, 0, 645, 150, 150, 150, 150, 150]
        self.maxs = [560, 570, 580, 570, 367, 550, 550, 550, 550, 603, 179, 550, 550, 550, 550, 550]
        self.offsets = [0.0341796875, 0.0, -0.1591796875, 0.0009765625, -0.07666015625, -0.013671875, -0.115234375,
                        0.115234375, 0.0341796875, -0.0029296875, -0.03759765625, 0.0, 0, 0, 0, 0]

        self.mins = [137, 160, 170, 0, 0, 150, 150, 150, 150, 0, 645, 150, 150, 150, 150, 150]
        self.maxs = [414, 570, 580, 570, 367, 550, 550, 550, 550, 603, 179, 550, 550, 550, 550, 550]
        self.offsets = [0.0, 0.0, -0.1591796875, 0.0009765625, -0.07666015625, -0.013671875, -0.115234375, 0.115234375, 0.0341796875, -0.0029296875, -0.03759765625, 0.0, 0, 0, 0, 0]

        self.mins = [137, 197, 125, 0, 0, 150, 150, 150, 150, 0, 645, 150, 150, 150, 150, 150]
        self.maxs = [414, 527, 558, 570, 367, 550, 550, 550, 550, 603, 179, 550, 550, 550, 550, 550]
        self.offsets = [0.0, 0.0, 0.0, 0.0009765625, -0.07666015625, -0.013671875, -0.115234375, 0.115234375, 0.0341796875, -0.0029296875, -0.03759765625, 0.0, 0, 0, 0, 0]

        self.mins = [137, 197, 125, 120, 0, 150, 150, 150, 150, 0, 645, 150, 150, 150, 150, 150]
        self.maxs = [414, 527, 558, 525, 367, 550, 550, 550, 550, 603, 179, 550, 550, 550, 550, 550]
        self.offsets = [0.0, 0.0, 0.0, 0.0, -0.07666015625, -0.013671875, -0.115234375, 0.115234375, 0.0341796875, -0.0029296875, -0.03759765625, 0.0, 0, 0, 0, 0]

        self.mins = [137, 197, 125, 120, 157, 131, 150, 150, 150, 0, 645, 150, 150, 150, 150, 150]
        self.maxs = [414, 527, 558, 525, 593, 560, 550, 550, 550, 603, 179, 550, 550, 550, 550, 550]
        self.offsets = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.115234375, 0.115234375, 0.0341796875, -0.0029296875, -0.03759765625, 0.0, 0, 0, 0, 0]

        self.mins = [137, 197, 125, 120, 157, 131, 279, 171, 150, 0, 645, 150, 150, 150, 150, 150]
        self.maxs = [414, 527, 558, 525, 593, 560, 531, 547, 550, 603, 179, 550, 550, 550, 550, 550]
        self.offsets = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0341796875, -0.0029296875, -0.03759765625, 0.0, 0, 0, 0, 0]

        self.mins = [137, 197, 125, 120, 157, 131, 279, 171, 144, 167, 645, 150, 150, 150, 150, 150]
        self.maxs = [414, 527, 558, 525, 593, 560, 531, 547, 581, 550, 179, 550, 550, 550, 550, 550]
        self.offsets = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.03759765625, 0.0, 0, 0, 0, 0]

        self.mins = [137, 197, 125, 120, 157, 131, 279, 171, 144, 167, 135, 150, 150, 150, 150, 150]
        self.maxs = [414, 527, 558, 525, 593, 560, 531, 547, 581, 550, 577, 550, 550, 550, 550, 550]
        self.offsets = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0, 0]

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

        self.animation = {0: [0, 35, 66, 89, 108, 127, 148, 164, 187, 209, 228, 256],
                          256: [0, 35, 66, 89, 108, 127, 148, 164, 187, 209, 228, 255],
                          132: [7, 30, 56, 82, 101, 118, 141, 159, 183, 200, 224, 247]}

        #self.curves =  [[[0, 256], [0, 0]], [[0, 256], [35, 35]], [[0, 256], [66, 66]], [[0, 256], [89, 89]], [[0, 256], [108, 108]], [[0, 256], [127, 127]], [[0, 256], [148, 148]], [[0, 256], [164, 164]], [[0, 256], [187, 187]], [[0, 256], [209, 209]], [[0, 256], [228, 228]], [[0, 256], [256, 255]]]
        self.curves = [[[0, 256], [128, 128]], [[0, 256], [128, 128]], [[0, 256], [128, 128]], [[0, 256], [128, 128]],
                       [[0, 256], [128, 128]], [[0, 256], [128, 128]], [[0, 256], [128, 128]], [[0, 256], [128, 128]],
                       [[0, 256], [128, 128]], [[0, 256], [128, 128]], [[0, 256], [128, 128]], [[0, 256], [128, 128]]]

        self.curves = [[[0, 256], [128, 128]],
                       [[0, 42, 80, 108, 135, 169, 206, 235, 256], [128, 109, 28, 11, 127, 47, 127, 127, 128]],
                       [[0, 42, 80, 108, 135, 169, 206, 235, 256], [83, 76, 143, 222, 169, 184, 121, 96, 83]],
                       [[0, 256], [128, 128]], [[0, 256], [128, 128]], [[0, 256], [128, 128]], [[0, 256], [128, 128]],
                       [[0, 42, 80, 108, 135, 169, 206, 235, 256], [128, 96, 128, 127, 124, 87, 28, 0, 128]],
                       [[0, 42, 80, 108, 135, 206, 235, 256], [170, 179, 121, 99, 88, 150, 217, 169]],
                       [[0, 256], [128, 128]], [[0, 256], [128, 128]], [[0, 256], [128, 128]]]

        self.curves = [[[0, 256], [143, 132]], [[0, 256], [209, 206]], [[0, 256], [127, 119]], [[0, 256], [200, 206]], [[0, 256], [137, 134]], [[0, 256], [193, 190]], [[0, 256], [184, 188]], [[0, 256], [192, 193]], [[0, 256], [126, 135]],
                       [[0, 256], [45, 47]], [[0, 256], [127, 129]], [[0, 256], [192, 190]]]

        self.curves = [[[0, 256], [148, 132]], [[0, 256], [209, 206]], [[0, 256], [130, 119]], [[0, 256], [206, 201]], [[0, 256], [68, 71]], [[0, 256], [193, 190]], [[0, 256], [171, 188]], [[0, 256], [195, 193]], [[0, 256], [126, 135]],
                       [[0, 256], [40, 48]], [[0, 256], [177, 180]], [[0, 256], [192, 190]]]

        self.curves = [[[0, 256], [148, 132]], [[0, 256], [209, 206]], [[0, 39, 100, 147, 256], [130, 192, 64, 108, 119]], [[0, 256], [206, 201]], [[0, 256], [68, 71]], [[0, 256], [193, 190]], [[0, 256], [171, 188]], [[0, 256], [195, 193]],
                       [[0, 39, 100, 147, 256], [126, 214, 69, 105, 135]], [[0, 256], [40, 48]], [[0, 256], [177, 180]], [[0, 256], [192, 190]]]

        self.curves = [[[0, 256], [148, 132]], [[0, 256], [209, 206]], [[0, 39, 100, 147, 256], [130, 192, 64, 108, 129]], [[0, 256], [206, 201]], [[0, 256], [68, 71]], [[0, 256], [193, 190]], [[0, 256], [171, 188]], [[0, 256], [195, 193]],
                       [[0, 39, 100, 147, 256], [126, 214, 69, 105, 125]], [[0, 256], [40, 48]], [[0, 256], [177, 180]], [[0, 256], [192, 190]]]

        self.curves = [[[0, 256], [153, 132]], [[0, 256], [209, 206]], [[0, 256], [130, 129]], [[0, 256], [205, 201]], [[0, 256], [73, 71]], [[0, 256], [193, 190]], [[0, 256], [190, 188]], [[0, 256], [195, 193]], [[0, 256], [126, 125]],
                       [[0, 256], [41, 48]], [[0, 256], [177, 180]], [[0, 256], [192, 190]]]

        self.curves = [[[0, 6, 12, 17, 46, 54, 75, 86, 99, 110, 120, 128, 139, 144, 160, 165, 169, 182, 256], [157, 115, 128, 144, 180, 182, 137, 119, 127, 159, 185, 185, 168, 124, 167, 190, 188, 153, 132]],
                       [[0, 17, 22, 63, 99, 130, 135, 149, 155, 169, 177, 182, 256], [209, 188, 179, 224, 181, 205, 230, 196, 172, 207, 232, 237, 206]],
                       [[0, 17, 22, 63, 99, 130, 135, 149, 155, 169, 177, 256], [130, 147, 157, 106, 155, 134, 112, 148, 157, 134, 113, 129]], [[0, 256], [205, 201]], [[0, 256], [73, 71]], [[0, 256], [193, 190]],
                       [[0, 6, 12, 36, 46, 54, 75, 86, 99, 110, 120, 128, 139, 144, 155, 160, 165, 169, 182, 256], [180, 196, 211, 185, 137, 170, 195, 207, 207, 173, 124, 166, 182, 210, 206, 173, 150, 159, 177, 188]],
                       [[0, 17, 22, 63, 99, 130, 149, 155, 177, 256], [195, 176, 178, 203, 184, 216, 196, 185, 216, 193]], [[0, 22, 63, 99, 130, 149, 155, 169, 177, 256], [126, 149, 118, 137, 102, 125, 147, 121, 102, 125]], [[0, 256], [41, 48]],
                       [[0, 256], [177, 180]], [[0, 256], [192, 190]]]

        self.curves = [[[0, 6, 12, 17, 46, 54, 75, 86, 99, 110, 120, 128, 139, 144, 160, 165, 169, 182, 256], [157, 115, 128, 144, 180, 182, 137, 119, 127, 159, 185, 185, 168, 124, 167, 190, 188, 153, 132]],
                       [[0, 17, 22, 63, 99, 130, 135, 149, 155, 169, 177, 182, 256], [209, 188, 179, 224, 181, 205, 230, 196, 172, 207, 232, 237, 206]],
                       [[0, 17, 22, 63, 99, 130, 135, 149, 155, 169, 177, 256], [130, 147, 157, 106, 155, 134, 112, 148, 157, 134, 113, 129]], [[0, 256], [205, 201]], [[0, 256], [73, 71]], [[0, 256], [193, 190]],
                       [[0, 6, 12, 36, 46, 54, 75, 86, 99, 110, 120, 128, 139, 144, 155, 160, 165, 169, 182, 256], [180, 196, 211, 185, 137, 170, 195, 207, 207, 173, 124, 166, 182, 210, 206, 173, 150, 159, 177, 188]],
                       [[0, 17, 22, 63, 99, 130, 149, 155, 177, 256], [195, 176, 178, 203, 184, 216, 196, 185, 216, 193]], [[0, 22, 63, 99, 130, 149, 155, 169, 177, 256], [126, 149, 118, 137, 102, 125, 147, 121, 102, 125]], [[0, 256], [41, 48]],
                       [[0, 256], [177, 180]], [[0, 256], [192, 190]]]

        self.curves = [[[0, 256], [153, 132]], [[0, 256], [209, 206]], [[0, 256], [130, 129]], [[0, 256], [205, 201]], [[0, 256], [73, 71]], [[0, 256], [193, 190]], [[0, 256], [190, 188]], [[0, 256], [195, 193]], [[0, 256], [126, 125]],
                       [[0, 256], [41, 48]], [[0, 256], [177, 180]], [[0, 256], [192, 190]]]

        self.curves = [[[0, 6, 15, 35, 39, 256], [155, 186, 186, 135, 186, 132]], [[0, 35, 256], [209, 204, 206]], [[0, 26, 35, 256], [130, 129, 119, 129]], [[0, 256], [205, 201]], [[0, 256], [73, 71]], [[0, 256], [193, 190]],
                       [[0, 6, 10, 15, 35, 256], [180, 98, 165, 165, 217, 188]], [[0, 26, 35, 256], [195, 232, 246, 193]], [[0, 26, 256], [126, 89, 125]], [[0, 256], [41, 48]], [[0, 256], [177, 180]], [[0, 256], [192, 190]]]

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

            values = self.getServoValues(pair[0])
            for i in range(len(self.curves)): self.servoPositionSliders[i].setValue(values[i])

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
        self.ui.pushButtonNextKey.clicked.connect(lambda: jumpToKey(self.getCurrKeyPair(cmp='>')[1]))

        def copy():
            self.copyBuffer = []
            for slider in self.sliders: self.copyBuffer += [slider.value()]

        self.ui.copyButton.clicked.connect(copy)

        def paste():
            if self.copyBuffer is None: return
            for i in range(len(self.copyBuffer)): self.sliders[i].setValue(self.copyBuffer[i])

        self.ui.pasteButton.clicked.connect(paste)

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

    def servoSliderChanged(self, index: int, value: int):

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
                """
                self.servoNames = ['Left Ankle', 'Left Knee', 'Left Hip', 'Left Shoulder', 'Left Elbow', 'Left Wrist',
                           'Right Ankle', 'Right Knee', 'Right Hip', 'Right Shoulder', 'Right Elbow', 'Right Wrist',
                           'time']
                """
                if (self.servoNames[index] == 'Left Hip') or (self.servoNames[index] == 'Right Hip'):
                    #self.setServo(index, (value / 255.0) - 0.5)
                    pass
                #self.setServo(index, (value / 255.0) - 0.5)

                if not self.servoPosGraphShowServo[index]: self.setServo(index, (value / 255.0) - 0.5)

                #self.glutonCanvas.servos[self.names[index]].setAngle(v)
                self.glutonCanvas.servos[self.servoNames[index]].setAngle(((value / 255.0) - 0.5) * 180.0)
                if self.allowGlutonCanvasRedraw: self.glutonCanvas.glDraw()

            except:
                pass

            if self.inTime:
                self.inServoOrTimeSliderChange = False
                return

            t = self.timeSlider.value()

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

            self.animation[t] = []

            values = []

            for i in self.servoPositionSliders: values += [i.value()]

            self.animation[t] = values

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



        c = "1 " + str(int(i)) + " " + str(int(v)) + "\r\n"
        #print(c)

        #"""

        try:
            if s is None: return

            s.write(_str(c))

            s.write(_str('2 1\r\n'))
            r = str(s.readline()).strip()
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
