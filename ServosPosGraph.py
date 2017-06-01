import sys
from enum import IntEnum
from PyQt4.QtOpenGL import *
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt4.QtCore import QObject, Qt
from PyQt4.QtGui import *
from scipy.interpolate import interp1d
from scipy.interpolate import splrep, splev, UnivariateSpline, InterpolatedUnivariateSpline
import numpy as np

def myGlVertex2f(self): glVertex2f(self.x(), self.y())

QVector2D.glVertexf = myGlVertex2f

class Mode(IntEnum):
    NORMAL  = 0
    DELETE  = 1
    MOVE    = 2
    ADD     = 3

class ServosPosGraph(QGLWidget):
    def __init__(self, gluton, parent = None):
        fmt = QGLFormat()
        fmt.setSampleBuffers(True)  # antialiasing
        super(ServosPosGraph, self).__init__(fmt, parent)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHeightForWidth(True)
        self.setSizePolicy(sizePolicy)
        self.sliders = gluton.sliders
        self.gluton = gluton
        self.colors = [(70,128,50),(255,255,255),(255,0,0),(0,255,0),(0,0,255),(255,255,0),(0,255,255),(255,0,255),
                       (192,192,192),(128,128,128),(128,0,0),(128,128,0),(0,128,0),(128,0,128),(0,128,128),(0,0,128)] # Move to Gluton.py
        self.setMouseTracking(True)
        self.closestKey = 0
        self.cursor = (0,0)
        self.closestKeyValuePos = None # type: QVector2D
        self.mode = Mode.NORMAL

        def setMode(mode): self.mode = mode

        self.gluton.ui.delButton.clicked.connect(lambda: setMode(Mode.DELETE))

    def paintGL(self):
        self.makeCurrent()

        # Need to do this each time for some reason. My guess is because the other canvas changes the projection
        # matrix each frame when in orthographic mode.
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        padd = 5
        glOrtho(-padd, 256 + padd, -padd, 256 + padd, -50.0, 50.0)

        t = self.gluton.timeSlider.value()
        glClear(GL_COLOR_BUFFER_BIT)
        glColor3f(0.0, 0.0, 1.0)
        glRectf(-5, -5, 5, 5)
        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_LINES)
        glVertex3f(t, 0, 0)
        glVertex3f(t, 256, 0)
        glEnd()

        ani = self.gluton.animation

        self.closestKey = self.gluton.getClosestKey()

        keys, values = self.gluton.getOrderedKeysValues()

        curves = self.gluton.curves

        def setColorAndLineWidth(index):
            """Change line width depending on current joint being edited"""
            if self.closestKeyValuePos is not None:
                if self.closestKeyValuePos[0] == index:         glLineWidth(4)
                else:                                           glLineWidth(1)
            elif index == self.gluton.currBeingEdited: glLineWidth(4)
            else:                                               glLineWidth(1)

            glColor3f(self.colors[index][0], self.colors[index][1], self.colors[index][2])

        for i in range(len(curves)):
            if not self.gluton.servoPosGraphShowServo[i]: continue
            setColorAndLineWidth(i)
            glBegin(GL_LINE_STRIP)
            curve = curves[i]
            xValues = curve[0]
            yValues = curve[1]

            try:
                s = splrep(np.ndarray(shape=(len(xValues),), buffer=np.array(xValues), dtype=int),
                           np.ndarray(shape=(len(xValues),), buffer=np.array(yValues), dtype=int))
                x = np.linspace(0, 256, 256)
                y = splev(x, s)

                for i in range(len(y)): glVertex2f(x[i], y[i])


            except:
                for i in range(len(xValues)):
                    glVertex2d(xValues[i], yValues[i])
            glEnd()

            glColor3f(1,1,1)
            for i in range(len(xValues)):
                if xValues[i] == self.closestKey:
                    glPointSize(10)
                    glBegin(GL_POINTS)
                    glVertex2f(xValues[i], yValues[i])
                    glEnd()
                else:
                    glPointSize(5)
                    glBegin(GL_POINTS)
                    glVertex2f(xValues[i], yValues[i])
                    glEnd()

        glLineWidth(1)

        if self.closestKeyValuePos is not None:
            glColor3f(1,1,0)
            glPointSize(10)
            glBegin(GL_POINTS)
            self.closestKeyValuePos[2].glVertexf()
            glEnd()

        return

        def do1D_Interpolation(index):
            setColorAndLineWidth(index)

            glBegin(GL_LINE_STRIP)

            r = list(range(0, 256, 16)) + list(ani.keys())
            r.sort()
            for i in r:
                keyPair = self.gluton.getCurrKeyPair(value=i)
                if keyPair is None: continue
                A = ani[keyPair[0]]
                B = ani[keyPair[1]]
                intp = interp1d((keyPair[0], keyPair[1]), (A[index], B[index]))
                glVertex2d(i, intp(i))

            glEnd()

        if self.servoAdjustment.interpolationMode == 0:
            index = 0
            for i in values:
                if self.servoAdjustment.servoPosGraphShowServo[index]:
                    setColorAndLineWidth(index)

                    try:
                        s = splrep( np.ndarray(shape=(len(keys),), buffer=np.array(keys), dtype=int),
                                    np.ndarray(shape=(len(keys),), buffer=np.array(i),    dtype=int))
                        x = np.linspace(0, 256, 256)
                        y = splev(x, s)
                        glBegin(GL_LINE_STRIP)
                        for i in range(len(y)): glVertex2f(x[i], y[i])
                        glEnd()

                    except: do1D_Interpolation(index)
                index += 1

        elif self.servoAdjustment.interpolationMode == 1:
            index = 0
            for i in values:
                if self.servoAdjustment.servoPosGraphShowServo[index]:
                    setColorAndLineWidth(index)

                    try:
                        s = UnivariateSpline(np.ndarray(shape=(len(keys),), buffer=np.array(keys), dtype=int),
                                             np.ndarray(shape=(len(keys),), buffer=np.array(i), dtype=int), s=100)

                        x = np.linspace(0, 256, 256)
                        y = s(x)
                        glBegin(GL_LINE_STRIP)
                        for i in range(len(y)): glVertex2f(x[i], y[i])
                        glEnd()

                    except:
                        do1D_Interpolation(index)
                index += 1
            """
            elif self.servoAdjustment.interpolationMode == 2:
            index = 0
            for i in values:
                setColorAndLineWidth(index)

                try:
                    s = InterpolatedUnivariateSpline(   np.ndarray(shape=(len(keys),), buffer=np.array(keys), dtype=int),
                                                        np.ndarray(shape=(len(keys),), buffer=np.array(i), dtype=int))

                    x = np.linspace(0, 256, 256)
                    y = s(x)
                    glBegin(GL_LINE_STRIP)
                    for i in range(len(y)): glVertex2f(x[i], y[i])
                    glEnd()

                except:
                    do1D_Interpolation(index)
                index += 1
            """
        else:
        #if True:
            for j in range(len(self.servoAdjustment.animation[0])): do1D_Interpolation(j)

        glLineWidth(1)


    def resizeGL(self, w: int, h: int):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        padd = 5
        glOrtho(-padd, 256 + padd, -padd, 256 + padd, -50.0, 50.0)

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

    def setMouseTracking(self, flag: bool):
        def recursive_set(parent):
            for child in parent.findChildren(QObject):
                try:
                    child.setMouseTracking(flag)
                except:
                    pass
                recursive_set(child)

        QWidget.setMouseTracking(self, flag)
        recursive_set(self)

    def mousePressEvent(self, event):
        if self.closestKeyValuePos is None: return
        if not event.buttons() & Qt.LeftButton: return

        if self.mode == Mode.DELETE:
            (i, j, k) = self.closestKeyValuePos
            del self.gluton.curves[i][0][j]
            del self.gluton.curves[i][1][j]
            self.mouseMoveEvent(event)
            self.glDraw()


    def mouseMoveEvent(self, event: QMouseEvent):

        model = glGetDoublev(GL_MODELVIEW_MATRIX)
        proj = glGetDoublev(GL_PROJECTION_MATRIX)
        view = glGetIntegerv(GL_VIEWPORT)
        objx, objy, objz = gluUnProject(event.x(), self.height() - event.y(), 0, model, proj, view)

        mousePos = QVector2D(objx, objy)

        self.cursor = (objx, objy)

        minDist = sys.float_info.max

        self.closestKeyValuePos = None

        for i in range(len(self.gluton.curves)):
            curve = self.gluton.curves[i]
            for j in range(len(curve[0])):
                p = QVector2D(curve[0][j], curve[1][j])
                dist = (mousePos - p).length()
                if dist > 20 or dist > minDist: continue
                self.closestKeyValuePos = (i, j, p)
                minDist = dist

        self.glDraw()

    def leaveEvent(self, event):
        self.closestKeyValuePos = None
        return super(ServosPosGraph, self).enterEvent(event)