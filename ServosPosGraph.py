
from PyQt4.QtOpenGL import *
from OpenGL.GL import *
from PyQt4.QtCore import QObject
from PyQt4.QtGui import *
from scipy.interpolate import interp1d
from scipy.interpolate import splrep, splev
import numpy as np

class ServosPosGraph(QGLWidget):
    def __init__(self, servoAdjustment, parent = None):
        super(ServosPosGraph, self).__init__(parent)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHeightForWidth(True)
        self.setSizePolicy(sizePolicy)
        self.sliders = servoAdjustment.sliders
        self.servoAdjustment = servoAdjustment
        self.colors = [(70,128,50),(255,255,255),(255,0,0),(0,255,0),(0,0,255),(255,255,0),(0,255,255),(255,0,255),
                       (192,192,192),(128,128,128),(128,0,0),(128,128,0),(0,128,0),(128,0,128),(0,128,128),(0,0,128)]
        self.setMouseTracking(True)

    def paintGL(self):
        print('paint')
        self.makeCurrent()
        t = self.servoAdjustment.timeSlider.value()
        glClear(GL_COLOR_BUFFER_BIT)
        glColor3f(0.0, 0.0, 1.0)
        glRectf(-5, -5, 5, 5)
        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_LINES)
        glVertex3f(t, 0, 0)
        glVertex3f(t, 256, 0)
        glEnd()

        ani = self.servoAdjustment.animation

        closest = self.servoAdjustment.getClosestKey()

        glColor3f(1, 1, 1)

        for i,c in list(zip(ani, range(1, 1+len(ani)))):
            #@TODO Colors are wrong here
            # if i == closest: glPointSize(10)
            # else: glPointSize(4)

            #if i != closestPair[0] and i != closestPair[1]: glColor3f(self.colors[c][0]/10, self.colors[c][1]/10, self.colors[c][2]/10)
            """
            if i != closest:
                glColor3f(self.colors[c][0] / 10, self.colors[c][1] / 10, self.colors[c][2] / 10)
            else: glColor3f(1,1,1)
            """

            if i != closest:    glPointSize(3)
            else:               glPointSize(6)

            glBegin(GL_POINTS)
            for t in ani[i]: glVertex2d(i,t)
            glEnd()

        keys, values = self.servoAdjustment.getOrderedKeysValues()

        def setColorAndLineWidth(index):
            """Change line width depending on current joint being edited"""
            if index == self.servoAdjustment.currBeingEdited:   glLineWidth(4)
            else:                                               glLineWidth(1)

            glColor3f(self.colors[index][0], self.colors[index][1], self.colors[index][2])

        def do1D_Interpolation(index):
            setColorAndLineWidth(index)

            glBegin(GL_LINE_STRIP)

            r = list(range(0, 256, 16)) + list(ani.keys())
            r.sort()
            for i in r:
                keyPair = self.servoAdjustment.getCurrKeyPair(value=i)
                if keyPair is None: continue
                A = ani[keyPair[0]]
                B = ani[keyPair[1]]
                intp = interp1d((keyPair[0], keyPair[1]), (A[index], B[index]))
                glVertex2d(i, intp(i))

            glEnd()

        if self.servoAdjustment.interpolationMode == 0:
            index = 0
            for i in values:
                setColorAndLineWidth(index)

                try:
                    s = splrep( np.ndarray(shape=(len(keys),), buffer=np.array(keys), dtype=int),
                                np.ndarray(shape=(len(keys),), buffer=np.array(i),    dtype=int))
                    x2 = np.linspace(0, 256, 256)
                    y2 = splev(x2, s)
                    glBegin(GL_LINE_STRIP)
                    for i in range(len(y2)): glVertex2f(x2[i], y2[i])
                    glEnd()

                except: do1D_Interpolation(index)
                index += 1
        else:
        #if True:
            for j in range(len(self.servoAdjustment.animation[0])): do1D_Interpolation(j)

        glLineWidth(1)


    def resizeGL(self, w, h):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        padd = 5
        glOrtho(-padd, 256 + padd, -padd, 256 + padd, -50.0, 50.0)
        glViewport(0, 0, w, h)

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

    def setMouseTracking(self, flag):
        def recursive_set(parent):
            for child in parent.findChildren(QObject):
                try:
                    child.setMouseTracking(flag)
                except:
                    pass
                recursive_set(child)

        QWidget.setMouseTracking(self, flag)
        recursive_set(self)

    def mouseMoveEvent(self, event):
        #print('mouseMoveEvent: x=%d, y=%d' % (event.x(), event.y()))
        pass