from PyQt4 import uic, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import QMainWindow
from PyQt4.QtOpenGL import *
from OpenGL.GL import *
from PyQt4.QtGui import *
from scipy.interpolate import interp1d
from scipy.interpolate import splrep
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
        glPointSize(5)
        glBegin(GL_POINTS)
        ani = self.servoAdjustment.animation

        for i,c in list(zip(ani, range(1, 1+len(ani)))):
            # Colors are wrong here
            glColor3f(self.colors[c][0], self.colors[c][1], self.colors[c][2])

            for t in ani[i]: glVertex2d(i,t)
        glEnd()

        for j in range(len(self.servoAdjustment.animation[0])):

            """Change line width depending on current joint being edited"""
            if j == self.servoAdjustment.currBeingEdited: glLineWidth(4)
            else:                                         glLineWidth(1)

            glColor3f(self.colors[j][0], self.colors[j][1], self.colors[j][2])
            glBegin(GL_LINE_STRIP)

            r = list(range(0,256,16)) + list(ani.keys())
            r.sort()
            keys = list(ani.keys())
            values = list(ani.values())
            #l = ([(x, y) for (x, y) in sorted(zip(keys, values))])
            for (x, y) in sorted(zip(keys, values)):
                print('x,y',x,y)

            #print('aaaa',l)
            #l = sorted(zip(keys, values))

            print('keys', keys)
            for i in r:
                keyPair = self.servoAdjustment.getCurrKeyPair(value=i)
                if keyPair is None: continue
                A = ani[keyPair[0]]
                B = ani[keyPair[1]]
                # print('keyPair[0]', keyPair[0], A[j])
                #print('int',(keyPair[0], keyPair[1]), (A[j], B[j]))
                intp = interp1d((keyPair[0], keyPair[1]), (A[j], B[j]))
                #intp = splrep()
                glVertex2d(i, intp(i))

            """
            r = list(ani.keys())
            r.sort()
            for i in r:
                keyPair = self.servoAdjustment.getCurrKeyPair(value=i)
                if keyPair is None: continue
                A = ani[keyPair[0]]
                B = ani[keyPair[1]]
                intp = interp1d((keyPair[0], keyPair[1]), (A[j], B[j]))
                glVertex2d(i, intp(i))
            """
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