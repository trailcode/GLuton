import sys
from enum import IntEnum
from PyQt4.QtOpenGL import *
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt4.QtCore import QObject, Qt
from PyQt4.QtGui import *
from shapely.geometry import LineString, Point
from scipy.interpolate import interp1d
from scipy.interpolate import splrep, splev, UnivariateSpline, InterpolatedUnivariateSpline
import numpy as np
import util

class Mode(IntEnum):
    NORMAL      = 0
    DELETE      = 1
    MOVE        = 2
    ADD         = 3
    TRANSLATE   = 4
    SELECT      = 5
    COPY        = 6
    PASTE       = 7

class ServosPosGraph(QGLWidget):
    def __init__(self, gluton, parent = None):
        fmt = QGLFormat()
        fmt.setSampleBuffers(True)  # antialiasing
        super(ServosPosGraph, self).__init__(fmt, parent)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHeightForWidth(True)
        self.setSizePolicy(sizePolicy)
        self.setMouseTracking(True)

        self.closestKey         = 0
        self.closestKeyValuePos = None
        self.closestCurveIndex  = None
        self.mode               = Mode.NORMAL
        self.copyBuffer         = None
        self.lastClickPos       = None # type: QVector2D
        self.interpolatedCurves = []
        self.gluton             = gluton  # type: GLuton
        self.glutonView         = self.gluton.glutonCanvas  # type: GlutonView
        self.sliders            = gluton.sliders
        self.colors             = [  # Move to Gluton.py
                                    (87, 87, 87),  # Dk. Gray
                                    (173, 35, 35),  # Red
                                    (42, 75, 215),  # Blue
                                    (29, 105, 20),  # Green
                                    (129, 74, 25),  # Brown
                                    (129, 38, 192),  # Purple
                                    (160, 160, 160),  # Lt. Gray
                                    (129, 197, 122),  # Lt. Green
                                    (157, 175, 255),  # Lt. Blue
                                    (41, 208, 208),  # Cyan
                                    (255, 146, 51),  # Orange
                                    (255, 238, 51),  # Yellow
                                    (233, 222, 187),  # Tan
                                    (255, 205, 243),  # Pink
                                    (255, 255, 255),  # White
                                ]

        #....................................................................................
        # Connect the mode buttons at the top of the panel so when they are pressed the
        # current mode is changed.
        def setMode(mode):
            self.mode = mode
            self.glDraw()

        self.gluton.ui.delButton            .clicked.connect(lambda: setMode(Mode.DELETE))
        self.gluton.ui.addButton            .clicked.connect(lambda: setMode(Mode.ADD))
        self.gluton.ui.moveButton           .clicked.connect(lambda: setMode(Mode.MOVE))
        self.gluton.ui.transButton          .clicked.connect(lambda: setMode(Mode.TRANSLATE))
        self.gluton.ui.selectButton         .clicked.connect(lambda: setMode(Mode.SELECT))
        self.gluton.ui.copyKeyValuesButton  .clicked.connect(lambda: setMode(Mode.COPY))
        self.gluton.ui.pasteKeyValuesButton .clicked.connect(lambda: setMode(Mode.PASTE))
        # ....................................................................................

    def paintGL(self):
        self.makeCurrent()

        # Need to do this each time for some reason. My guess is because the other canvas changes the projection
        # matrix each frame when in orthographic mode.
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        padd = 5
        glOrtho(-padd, 256 + padd, -padd, 256 + padd, -50.0, 50.0)

        t = self.gluton.timeSlider.value()
        glClearColor(0.1,0.1,0.1,1)
        glClear(GL_COLOR_BUFFER_BIT)
        glColor3f(0.0, 0.0, 1.0)
        glRectf(-5, -5, 5, 5)
        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_LINES)
        glVertex3f(t, 0, 0)
        glVertex3f(t, 256, 0)
        glEnd()

        curves = self.gluton.curves

        def setColorAndLineWidth(index):

            smallWidth = 2
            fatWidth = 5

            if self.closestCurveIndex is not None:
                if self.closestCurveIndex == index:         glLineWidth(fatWidth)
                else:                                       glLineWidth(smallWidth)
            elif self.closestKeyValuePos is not None:
                if self.closestKeyValuePos[0] == index:     glLineWidth(fatWidth)
                else:                                       glLineWidth(smallWidth)
            elif index == self.gluton.currBeingEdited:      glLineWidth(fatWidth)
            else:                                           glLineWidth(smallWidth)

            glColor3f(self.colors[index][0] / 255.0, self.colors[index][1] / 255.0, self.colors[index][2] / 255.0)

            if self.gluton.servoPosGraphShowServo[index]:
                glDisable(GL_LINE_STIPPLE)

            else:
                glLineStipple(3, 0xAAAA)
                glEnable(GL_LINE_STIPPLE)

        self.interpolatedCurves = []

        closestKey = self.gluton.getClosestKey()

        for curveIndex in range(len(curves)):
            points = []

            setColorAndLineWidth(curveIndex)
            glBegin(GL_LINE_STRIP)
            curve = curves[curveIndex]
            xValues = curve[0]
            yValues = curve[1]

            try:
                #dasdd
                s = splrep(np.ndarray(shape=(len(xValues),), buffer=np.array(xValues), dtype=int),
                           np.ndarray(shape=(len(xValues),), buffer=np.array(yValues), dtype=int))
                x = np.linspace(0, 256, 256)
                y = splev(x, s)

                for i in range(len(y)):
                    glVertex2f(x[i], y[i])
                    points += [(x[i], y[i])]

            except:
                for i in range(len(xValues)):
                    glVertex2d(xValues[i], yValues[i])
                    points += [(xValues[i], yValues[i])]
            glEnd()

            if self.gluton.servoPosGraphShowServo[curveIndex]:  self.interpolatedCurves += [LineString(points)]
            else:                                               self.interpolatedCurves += [None]

            glColor3f(1,1,1)
            for i in range(len(xValues)):
                if xValues[i] == closestKey and self.mode != Mode.DELETE and self.mode != Mode.MOVE:
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
                try:    child.setMouseTracking(flag)
                except: pass
                recursive_set(child)

        QWidget.setMouseTracking(self, flag)
        recursive_set(self)

    def getWC_Pos(self, x, y):
        model = glGetDoublev(GL_MODELVIEW_MATRIX)
        proj = glGetDoublev(GL_PROJECTION_MATRIX)
        view = glGetIntegerv(GL_VIEWPORT)
        objX, objY, objZ = gluUnProject(x, self.height() - y, 0, model, proj, view)
        return QVector2D(objX, objY)

    def mousePressEvent(self, event):
        if not event.buttons() & Qt.LeftButton: return

        self.lastClickPos = self.getWC_Pos(event.x(), event.y())

        if self.mode == Mode.COPY:
            if self.closestCurveIndex is None: return
            self.copyBuffer = self.gluton.curves[self.closestCurveIndex].copy()

        if self.mode == Mode.PASTE:
            if self.closestCurveIndex is None or self.copyBuffer is None: return
            self.gluton.curves[self.closestCurveIndex] = self.copyBuffer.copy()
            self.gluton.updateServoSliders()
            self.glDraw()

        if self.closestKeyValuePos is None: return

        if self.mode == Mode.DELETE:
            (i, j, k) = self.closestKeyValuePos
            del self.gluton.curves[i][0][j]
            del self.gluton.curves[i][1][j]
            self.closestKeyValuePos = None
            self.glDraw()

    def mouseMoveEvent(self, event: QMouseEvent):

        if self.mode == Mode.NORMAL: return

        mousePos = self.getWC_Pos(event.x(), event.y())

        if event.buttons() & Qt.LeftButton:
            if self.lastClickPos is None:
                self.lastClickPos = mousePos
                return

            diff = mousePos - self.lastClickPos

            for i in range(len(self.gluton.curves)):
                if not self.gluton.servoPosGraphShowServo[i]: continue


            self.lastClickPos = mousePos

            return

        minDist = sys.float_info.max

        self.closestKeyValuePos = None
        self.closestCurveIndex = None

        if self.mode == Mode.DELETE or self.mode == Mode.MOVE:
            for i in range(len(self.gluton.curves)):
                if not self.gluton.servoPosGraphShowServo[i]: continue
                curve = self.gluton.curves[i]
                for j in range(len(curve[0])):
                    p = QVector2D(curve[0][j], curve[1][j])
                    dist = (mousePos - p).length()
                    if dist > 20 or dist > minDist: continue
                    self.closestKeyValuePos = (i, j, p)
                    minDist = dist

        elif (  self.mode == Mode.TRANSLATE or
                self.mode == Mode.SELECT or
                self.mode == Mode.COPY or
                self.mode == Mode.PASTE):

            mousePos = Point(mousePos.x(), mousePos.y())

            for i in range(len(self.interpolatedCurves)):
                if self.interpolatedCurves[i] is None: continue
                dist = mousePos.distance(self.interpolatedCurves[i])
                if dist > minDist: continue
                minDist = dist
                self.closestCurveIndex = i

            self.glutonView.highlightServo(self.gluton.servoNames[self.closestCurveIndex])
            self.glutonView.glDraw()

        self.glDraw()

    def wheelEvent(self, event: QWheelEvent):
        delta = event.delta() / 2
        if delta == 0: return
        t = self.gluton.timeSlider.value()
        maxDelta = 3
        t += min(maxDelta, max(-maxDelta, delta))
        if t > self.gluton.timeSlider.maximum(): t = 0
        elif t < 0: t = self.gluton.timeSlider.maximum()
        self.gluton.timeSlider.setValue(t)

    def leaveEvent(self, event):
        self.closestKeyValuePos = None
        self.closestCurveIndex = None
        self.glutonView.unhighlightLastServo()
        self.glDraw()
        return super(ServosPosGraph, self).enterEvent(event)