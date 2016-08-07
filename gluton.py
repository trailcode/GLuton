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
from itertools import product

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

class WfWidget(QGLWidget):
    def __init__(self, servoAdjustment, parent = None):
        super(WfWidget, self).__init__(parent)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHeightForWidth(True)
        self.setSizePolicy(sizePolicy)
        self.sliders = servoAdjustment.sliders
        self.servoAdjustment = servoAdjustment
        self.colors = [(0,0,0),(255,255,255),(255,0,0),(0,255,0),(0,0,255),(255,255,0),(0,255,255),(255,0,255),(192,192,192),(128,128,128),(128,0,0),(128,128,0),(0,128,0),(128,0,128),(0,128,128),(0,0,128)]

    def paintGL(self):
        #return

        t = self.servoAdjustment.timeSlider.value()
        glClear(GL_COLOR_BUFFER_BIT)
        glColor3f(0.0, 0.0, 1.0)
        glRectf(-5, -5, 5, 5)
        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_LINES)
        glVertex3f(t, 0, 0)
        glVertex3f(t, 256, 0)
        glEnd()
        glPointSize(4)
        glBegin(GL_POINTS)
        glColor3f(1,1,1)
        for i in self.servoAdjustment.animation:
            c = 1
            for t in self.servoAdjustment.animation[i]:
                glColor3f(self.colors[c][0],self.colors[c][1],self.colors[c][2])
                c += 1
                glVertex2d(i,t)

        glEnd()
        c = 1
        for j in range(len(self.servoAdjustment.animation[0])):
            glColor3f(self.colors[c][0], self.colors[c][1], self.colors[c][2])
            c += 1
            glBegin(GL_LINE_STRIP)
            for i in range(0,256,8):
                keyPair = self.servoAdjustment.getCurrKeyPair(value = i)
                if keyPair is None: continue
                A = self.servoAdjustment.animation[keyPair[0]]
                B = self.servoAdjustment.animation[keyPair[1]]
                intp = interp1d((keyPair[0], keyPair[1]), (A[j], B[j]))
                glVertex2d(i, intp(i))
            glEnd()

    def resizeGL(self, w, h):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        padd = 5
        glOrtho(-padd, 256 + padd, -padd, 256 + padd, -50.0, 50.0)
        glViewport(0, 0, w, h)

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

class ServoAdjustment(QMainWindow):
    def __init__(self):
        super(ServoAdjustment, self).__init__()
        self.ui = uic.loadUi("gluton.ui", self)
        self.ui.show()
        #self.ui.sliderWidget.setStyleSheet("background-image: url(logo.png);background-attachment: fixed")
            #setPixmap(QPixmap(os.getcwd() + "/logo.png"))
        self.ui.spinBoxServo.valueChanged.connect(self.servoChanged)
        self.sliders = []
        self.canvas = WfWidget(self)
        #self.canvas.setSizePolicy(QSizePolicy.Policy.
        self.ui.canvasLayout.addWidget(self.canvas)

        self.background_pixmap = QPixmap('logo.png')

        self.names = ['Left Ankle', 'Left Knee', 'Left Hip', 'Left Shoulder', 'Left Elbow', 'Left Wrist',
                      'Right Ankle', 'Right Knee', 'Right Hip', 'Right Shoulder', 'Right Elbow', 'Right Wrist', 'time']

        #self.names = ['Left Ankle', 'Left Knee', 'time']
        self.servoValueSliders = []
        self.servoValueLabels = []
        self.center()

        for i,index in zip(self.names, range(0, len(self.names))):
            exec('ServoAdjustment.f' + str(index) + ' = lambda self, value: self.servoSliderChanged(' + str(index) + ', value)')
            label = QLabel()
            label.setText(i + ':')
            label.setFixedWidth(100)
            label.setAlignment(Qt.AlignRight)
            class MySlider(QSlider):
                def __init__(self, direction, parent=None):
                    super(MySlider, self).__init__(direction, parent)
                    self.setMouseTracking(True)

                def enterEvent(self, event):
                    print("Enter")
                    #self.setStyleSheet("background-color:#45b545;")

                def leaveEvent(self, event):
                    self.setStyleSheet("background-color:yellow;")
                    #print("Leave")
            #slider = QSlider(Qt.Horizontal)
            slider = MySlider(Qt.Horizontal)
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
            """
            label.setContentsMargins(0, 0, 0, 0)
            slider.setContentsMargins(0, 0, 0, 0)
            valueLabel.setContentsMargins(0, 0, 0, 0)
            """
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
        self.animation = {0: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 18: [18, 38, 56, 0, 0, 0, 0, 0, 0, 0, 0, 0], 76: [80, 0, 30, 0, 0, 0, 0, 0, 0, 0, 0, 0]}

        self.mins = [150, 160, 170, 0, 0, 150, 150, 150, 150, 0, 645, 150, 150, 150, 150, 150]
        self.maxs = [560, 570, 580, 570, 367, 550, 550, 550, 550, 603, 179, 550, 550, 550, 550, 550]
        self.offsets = [0.0341796875, 0.0, -0.1591796875, 0.0009765625, -0.07666015625, -0.013671875, -0.115234375,
                        0.115234375, 0.0341796875, -0.0029296875, -0.03759765625, 0.0, 0, 0, 0, 0]
        self.animation = {0: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                          256: [256, 256, 256, 256, 256, 256, 256, 256, 256, 256, 256, 256],
                          18: [18, 38, 56, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                          165: [113, 101, 71, 126, 34, 126, 126, 126, 126, 126, 126, 126],
                          151: [153, 106, 124, 106, 0, 106, 106, 106, 106, 106, 106, 106],
                          177: [131, 121, 95, 143, 95, 113, 173, 95, 167, 60, 220, 89],
                          76: [80, 0, 30, 0, 0, 0, 0, 0, 0, 0, 0, 0]}

        self.ui.horizontalSliderMin.valueChanged.connect(self.minChanged)
        self.ui.horizontalSliderMax.valueChanged.connect(self.maxChanged)
        self.ui.horizontalSliderOffset.valueChanged.connect(self.offsetChanged)
        self.ui.horizontalSliderPos.valueChanged.connect(self.posChanged)
        self.ui.pushButtonDumpValues.clicked.connect(self.dumpValues)
        self.ui.pushButtonZeroPos.clicked.connect(lambda : self.ui.horizontalSliderPos.setValue(1024))
        #self.ui.spinBoxPose.valueChanged.connect(self.poseChanged)

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
        self.ui.pushButtonNextKey.clicked.connect(lambda : self.timeSlider.setValue(self.getCurrKeyPair('>')[1]))

        self.inTime = False

        for i in range(len(self.servoValueSliders)): self.servoSliderChanged(i, 0)

    def center(self):
        frameGm = self.frameGeometry()
        screen = QtGui.QApplication.desktop().screenNumber(QtGui.QApplication.desktop().cursor().pos())
        centerPoint = QtGui.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def ensureAnimation(self):
        pass

    def getCurrKeyPair(self, cmp = '>=', value=None):
        if value is None: value = self.timeSlider.value()
        keys = list(self.animation.keys())
        keys.sort()
        for i in range(len(keys)):
            if get_truth(keys[i], cmp, value): return (keys[i - 1], keys[i])

    def servoSliderChanged(self, index, value):
        t = self.timeSlider.value()

        if index == self.names.index('time'):
            self.timeLabel.setText(str(value))
            keyPair = self.getCurrKeyPair()
            if keyPair is None: return
            self.inTime = True
            A = self.animation[keyPair[0]]
            B = self.animation[keyPair[1]]
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



    def poseChanged(self, value):
        print('poseChanged', value)

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
