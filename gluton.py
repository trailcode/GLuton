import sys
import PyQt4
from PyQt4.QtGui import QMainWindow
from PyQt4.QtOpenGL import *
from OpenGL.GL import *
from PyQt4 import uic, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from scipy.interpolate import interp1d

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
    def __init__(self, parent = None):
        super(WfWidget, self).__init__(parent)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHeightForWidth(True)
        self.setSizePolicy(sizePolicy)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glColor3f(0.0, 0.0, 1.0)
        glRectf(-5, -5, 5, 5)
        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(20, 20, 0)
        glEnd()

    def resizeGL(self, w, h):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-50, 50, -50, 50, -50.0, 50.0)
        glViewport(0, 0, w, h)

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

class ServoAdjustment(QMainWindow):
    def __init__(self):
        super(ServoAdjustment, self).__init__()
        self.ui = uic.loadUi("gluton.ui", self)
        self.ui.show()
        self.ui.spinBoxServo.valueChanged.connect(self.servoChanged)

        self.canvas = WfWidget()
        #self.canvas.setSizePolicy(QSizePolicy.Policy.
        self.ui.canvasLayout.addWidget(self.canvas)

        """
        self.mins = [150,160,170,180,150,150,150,150,150,150,150,150,150,150,150,150]
        self.maxs = [560,570,580,550,550,550,550,550,550,550,550,550,550,550,550,550]
        self.offsets = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        """


        self.names = ['Left Ankle', 'Left Knee', 'Left Hip', 'Left Sholder', 'Left Elbo', 'Left Wrist',
                      'Right Ankle', 'Right Knee', 'Right Hip', 'Right Sholder', 'Right Elbo', 'Right Wrist', 'time']

        #self.names = ['Left Ankle', 'Left Knee', 'time']
        self.servoValueSliders = []
        self.servoValueLabels = []

        for i,index in zip(self.names, range(0, len(self.names))):
            exec('ServoAdjustment.f' + str(index) + ' = lambda self, value: self.servoSliderChanged(' + str(index) + ', value)')
            label = QLabel()
            label.setText(i + ':')
            label.setFixedWidth(100)
            label.setAlignment(Qt.AlignRight)
            slider = QSlider(Qt.Horizontal)
            slider.setMaximum(256)
            valueLabel = QLabel()
            valueLabel.setText(str(slider.value()))
            valueLabel.setFixedWidth(100)


            global _self
            _self = self
            exec('slider.valueChanged.connect(lambda x: _self.f' + str(index) + '(x))')

            box = QHBoxLayout()
            box.addWidget(label)
            box.addWidget(slider)
            box.addWidget(valueLabel)

            if i != 'time':
                self.servoValueSliders.append(slider)
                self.servoValueLabels.append(valueLabel)
                self.ui.verticalLayoutServoPositions.addLayout(box)

            else:
                self.timeSlider = slider
                self.timeLabel = valueLabel
                self.ui.horizontalLayoutTime.addLayout(box)



        print('self.timeSlider', self.timeSlider)

        #print(self.servoValueSliders)

        self.mins = [150, 160, 170, 0, 0, 150, 150, 150, 150, 0, 645, 150, 150, 150, 150, 150]
        self.maxs = [560, 570, 580, 570, 367, 550, 550, 550, 550, 603, 179, 550, 550, 550, 550, 550]
        self.offsets = [0.0341796875, 0.0, -0.1591796875, 0.0009765625, -0.07666015625, -0.013671875, -0.115234375,
                        0.115234375, 0.0341796875, -0.0029296875, -0.03759765625, 0.0, 0, 0, 0, 0]

        self.poses = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

        self.poses2 = [[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                       [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                       [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                       [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],]

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
            print('save')

        def reset():
            print('reset')

        self.ui.pushButtonSave.clicked.connect(save)
        self.ui.pushButtonReset.clicked.connect(reset)

        self.animation = {}

        self.ui.pushButtonPrevKey.clicked.connect(lambda : self.timeSlider.setValue(self.getCurrKeyPair()[0]))
        self.ui.pushButtonNextKey.clicked.connect(lambda : self.timeSlider.setValue(self.getCurrKeyPair('>')[1]))

        self.inTime = False

        for i in range(len(self.servoValueSliders)): self.servoSliderChanged(i, 0)

        print('Done')

    def ensureAnimation(self):
        pass

    def getCurrKeyPair(self, cmp = '>='):
        keys = list(self.animation.keys())
        keys.sort()
        print('keys', keys)
        for i in range(len(keys)):
            if get_truth(keys[i], cmp, self.timeSlider.value()): return (keys[i - 1], keys[i])

    def servoSliderChanged(self, index, value):
        print('servoSliderChanged', index, value, self.names[index])
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
            print('self.inTime', self.inTime)
            if self.inTime: return

            self.servoValueLabels[index].setText(str(value))
            self.animation[t] = []

            values = []

            for i in self.servoValueSliders: values += [i.value()]

            self.animation[t] = values

            print(values)

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
        print('Servo ', value)
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
        print(c)

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
