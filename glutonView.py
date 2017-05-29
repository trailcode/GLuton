import copy
from PyQt4.QtOpenGL import QGLWidget, QGLFormat
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt4.QtCore import QObject, Qt, QEvent
from PyQt4.QtGui import QSizePolicy, QVector3D, QWheelEvent, QWidget
from ArcBall import Matrix4fT, Matrix3fT, ArcBallT, Point2fT, Matrix3fSetRotationFromQuat4f, Matrix3fMulMatrix3f, Matrix4fSetRotationFromMatrix3f
from SceneGraphNode import SceneGraphNode
import numpy as np

class GlutonView(QGLWidget):

    def __init__(self, gluton, parent = None):
        fmt = QGLFormat()
        fmt.setSampleBuffers(True)  # antialiasing

        super(GlutonView, self).__init__(fmt, parent)

        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHeightForWidth(True)
        self.setSizePolicy(sizePolicy)
        self.setMouseTracking(True)
        self.distance = -16.0
        self.transform = Matrix4fT()
        self.lastRot = Matrix3fT()
        self.thisRot = Matrix3fT()

        self.arcBall = ArcBallT(640, 480)
        self.quadratic = None

        self.gridTranslation = [0,0]

        self.servos = {}

        self.root = SceneGraphNode()
        self.servos['root'] = self.root

        self.lastRightFootPos = 0
        self.lastLeftFootPos = 0

        self.renderWithPerspective = True
        self.moveGrid = True

        def addServo(servoName, parentServo, servo):
            self.servos[servoName] = servo
            self.servos[parentServo].addChild(servo)

        addServo('Right Hip',       'root',             SceneGraphNode(QVector3D(1,0,0),      QVector3D(1,0,0),   [1,0.45,0,1]))
        addServo('Left Hip',        'root',             SceneGraphNode(QVector3D(-1, 0, 0),   QVector3D(1, 0, 0), [0,0.45,1]))
        addServo('Right Knee',      'Right Hip',        SceneGraphNode(QVector3D(0,-1,0),     QVector3D(1, 0, 0), [1,0.45,0,1]))
        addServo('Left Knee',       'Left Hip',         SceneGraphNode(QVector3D(0, -1, 0),   QVector3D(1, 0, 0), [0,0.45,1]))
        addServo('Right Ankle',     'Right Knee',       SceneGraphNode(QVector3D(0, -1, 0),   QVector3D(0, 0, 1), [1,0.45,0,1]))
        addServo('Left Ankle',      'Left Knee',        SceneGraphNode(QVector3D(0, -1, 0),   QVector3D(0, 0, 1), [0,0.45,1]))
        addServo('chest',           'root',             SceneGraphNode(QVector3D(0,2,0)))
        addServo('Right Shoulder',  'chest',            SceneGraphNode(QVector3D(1.3, 0, 0),  QVector3D(1, 0, 0)))
        addServo('Left Shoulder',   'chest',            SceneGraphNode(QVector3D(-1.3, 0, 0), QVector3D(1, 0, 0)))
        addServo('Right Elbow',     'Right Shoulder',   SceneGraphNode(QVector3D(0, -0.7, 0), QVector3D(1, 0, 0)))
        addServo('Left Elbow',      'Left Shoulder',    SceneGraphNode(QVector3D(0, -0.7, 0), QVector3D(1, 0, 0)))
        addServo('Right Wrist',     'Right Elbow',      SceneGraphNode(QVector3D(0, -0.7, 0), QVector3D(1, 0, 0)))
        addServo('Left Wrist',      'Left Elbow',       SceneGraphNode(QVector3D(0, -0.7, 0), QVector3D(1, 0, 0)))
        addServo('Right Hand',      'Right Wrist',      SceneGraphNode(QVector3D(0, -0.2, 0), QVector3D(1, 0, 0)))
        addServo('Left Hand',       'Left Wrist',       SceneGraphNode(QVector3D(0, -0.2, 0), QVector3D(1, 0, 0)))
        addServo('Head',            'chest',            SceneGraphNode(QVector3D(0, 0.8, 0),  QVector3D(1, 0, 0)))
        addServo('Right Foot',      'Right Ankle',      SceneGraphNode(QVector3D(0.3, 0, 0),  QVector3D(1, 0, 0), [1,0.45,0,1]))
        addServo('Left Foot',       'Left Ankle',       SceneGraphNode(QVector3D(-0.3, 0, 0), QVector3D(1, 0, 0), [0,0.45,1]))

        self.rightFootPoints = []
        self.leftFootPoints = []

    def paintGL(self):
        self.makeCurrent()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if not self.renderWithPerspective:
            glMatrixMode(GL_PROJECTION)  # // Select The Projection Matrix
            glLoadIdentity()  # // Reset The Projection Matrix
            glOrtho(self.distance, -self.distance, self.distance, -self.distance, -100.0, 100.0)

        glMatrixMode(GL_MODELVIEW)  # // Select The Modelview Matrix
        glLoadIdentity()  # // Reset The Modelview Matrix

        glEnable(GL_BLEND)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

        glLoadIdentity()
        if self.renderWithPerspective: glTranslatef(0, 0.0, self.distance)

        glPushMatrix()
        glMultMatrixf(self.transform)
        self.root.updatePosition()
        A = self.servos['Right Ankle'].position
        B = self.servos['Left Ankle'].position

        glPushMatrix()
        if A.y() > B.y():
            heightDiff = -B.y() + 0.1
            diff = A.y() - B.y()
            self.servos['Right Foot'].color = [1, 0.45, 0]
            self.servos['Left Foot'].color = [1, 1, 1]
            self.servos['Right Ankle'].color = [1, 0.45, 0]
            self.servos['Left Ankle'].color = [1, 1, 1]

            delta = B.z() - self.lastLeftFootPos

            self.lastLeftFootPos = B.z()

        else:
            heightDiff = -A.y() + 0.1
            diff = B.y() - A.y()
            self.servos['Right Foot'].color = [1, 1, 1]
            self.servos['Left Foot'].color = [0, 0.45, 1]
            self.servos['Right Ankle'].color = [1, 1, 1]
            self.servos['Left Ankle'].color = [0, 0.45, 1]

            delta = A.z() - self.lastRightFootPos

            self.lastRightFootPos = A.z()

        glTranslatef(0, heightDiff, 0)

        self.root.render()

        glPopMatrix()

        if not self.moveGrid:
            self.gridTranslation[1] += delta
            self.rightFootPoints += [(A.x(), A.y() + heightDiff, A.z())]
            self.leftFootPoints += [(B.x(), B.y() + heightDiff, B.z())]
        else:
            if delta < 0: self.gridTranslation[1] += delta
            glTranslatef(self.gridTranslation[0], 0, self.gridTranslation[1])
            self.rightFootPoints += [(A.x(), A.y() + heightDiff, A.z() - self.gridTranslation[1])]
            self.leftFootPoints += [(B.x(), B.y() + heightDiff, B.z() - self.gridTranslation[1])]


        if delta > 0:
            #self.rightFootPoints = []
            #self.leftFootPoints = []
            pass


        self.drawGroundGrid()

        glColor3f(1, 0, 0)
        glBegin(GL_LINE_STRIP)
        for p in self.rightFootPoints: glVertex3f(p[0], p[1], p[2])
        glEnd()

        glColor3f(0, 1, 1)
        glBegin(GL_LINE_STRIP)
        for p in self.leftFootPoints: glVertex3f(p[0], p[1], p[2])
        glEnd()

        glPopMatrix()

        if diff < 0.001:    glColor3f(1,0,0)
        else:               glColor3f(1,1,0)

        self.renderText(10,
                        self.height() - 15,
                        "{0:.4f}".format(diff) +
                        " pos: " + "{0:.4f}".format(self.gridTranslation[1]) +
                        " delta: " + "{0:.4f}".format(delta),
                        self.font())

    def drawGroundGrid(self):
        glDisable(GL_LIGHTING)
        glColor3f(0,0.7,.3)
        glLineWidth(1)
        glBegin(GL_LINES)
        size = 100
        for i in range(-size, size + 1):
            glVertex3f(i, 0, size)
            glVertex3f(i, 0, -size)
            glVertex3f(size, 0, i)
            glVertex3f(-size, 0, i)
        glEnd()


    def resizeGL(self, width: int, height: int):
        # Prevent A Divide By Zero If The Window Is Too Small
        if height == 0: height = 1

        glViewport(0, 0, width, height)  # Reset The Current Viewport And Perspective Transformation
        glMatrixMode(GL_PROJECTION)  # // Select The Projection Matrix
        glLoadIdentity()  # // Reset The Projection Matrix

        if not self.renderWithPerspective: glOrtho(self.distance, -self.distance, self.distance, -self.distance, -100.0, 100.0)
        else:
            # // field of view, aspect ratio, near and far
            # This will squash and stretch our objects as the window is resized.
            # Note that the near clip plane is 1 (hither) and the far plane is 1000 (yon)
            gluPerspective(45.0, float(width) / float(height), 1, 100.0)

        glMatrixMode(GL_MODELVIEW)  # // Select The Modelview Matrix
        glLoadIdentity()  # // Reset The Modelview Matrix
        self.arcBall.setBounds(width, height)  # //*NEW* Update mouse bounds for arcball

    def initializeGL(self):

        glClearColor(0.0, 0.0, 0.0, 1.0)  # This Will Clear The Background Color To Black
        glClearDepth(1.0)  # Enables Clearing Of The Depth Buffer
        glDepthFunc(GL_LEQUAL)  # The Type Of Depth Test To Do
        glEnable(GL_DEPTH_TEST)  # Enables Depth Testing
        glShadeModel(GL_FLAT)  # Select Flat Shading (Nice Definition Of Objects)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)  # Really Nice Perspective Calculations

        self.quadratic = gluNewQuadric()
        gluQuadricNormals(self.quadratic, GLU_SMOOTH)
        gluQuadricDrawStyle(self.quadratic, GLU_FILL)

        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHTING)

        glEnable(GL_COLOR_MATERIAL)

    def setMouseTracking(self, flag: bool):
        def recursive_set(parent):
            for child in parent.findChildren(QObject):
                child.setMouseTracking(flag)
                recursive_set(child)

        QWidget.setMouseTracking(self, flag)
        recursive_set(self)

    def doRotate(self, x: int, y: int):
        mouse_pt = Point2fT(x, y)
        ThisQuat = self.arcBall.drag(mouse_pt)  # // Update End Vector And Get Rotation As Quaternion
        self.thisRot = Matrix3fSetRotationFromQuat4f(ThisQuat)  # // Convert Quaternion Into Matrix3fT
        # Use correct Linear Algebra matrix multiplication C = A * B
        self.thisRot = Matrix3fMulMatrix3f(self.lastRot, self.thisRot)  # // Accumulate Last Rotation Into This One

        self.transform = Matrix4fSetRotationFromMatrix3f(self.transform,
                                                         self.thisRot)  # // Set Our Final Transform's Rotation From This One
        self.transform[3][3] = 1.0  # Prevent objects getting smaller and drifting apart over time

    def mouseMoveEvent(self, event: QWheelEvent):

        if event.buttons() & Qt.LeftButton: self.doRotate(event.x(), event.y())

        self.paintGL()
        self.swapBuffers()
        self.repaint()

    def mousePressEvent(self, event: QWheelEvent):
        btns = event.buttons()
        x = event.x()
        y = event.y()
        if btns & Qt.LeftButton:
            self.lastRot = copy.copy(self.thisRot)  # // Set Last Static Rotation To Last Dynamic One
            mouse_pt = Point2fT(x, y)
            self.arcBall.click(mouse_pt)  # // Update Start Vector And Prepare For Dragging


    def wheelEvent(self, event : QWheelEvent):
        """
        Called by the Qt libraries whenever the window receives a mouse wheel change.

        This is used for zooming, or rather moving the camera ahead.
        """
        delta = event.delta()
        if delta == 0: return
        moda = event.modifiers()
        x = event.x()
        y = event.y()
        self.lastRot = copy.copy(self.thisRot)  # // Set Last Static Rotation To Last Dynamic One
        mouse_pt = Point2fT(x, y)
        self.arcBall.click(mouse_pt)  # // Update Start Vector And Prepare For Dragging
        if moda & Qt.ShiftModifier : self.doRotate(x, y + delta)
        elif moda & Qt.AltModifier: self.doRotate(x + delta, y)
        else:
            self.distance += delta * 0.05
            if self.distance > -2: self.distance = -2

        self.glDraw()

    def setRotation(self, rotation):

        self.thisRot = np.array(rotation, dtype=np.float32)

        # Set Our Final Transform's Rotation From This One
        self.transform = Matrix4fSetRotationFromMatrix3f(self.transform,
                                                         self.thisRot)
        self.glDraw()

    def setSide(self):

        self.setRotation([  [0, 0, 1],
                            [0, 1, 0],
                            [1, 0, 0]])



    def setFront(self):

        self.setRotation([ [-1, 0, 0],
                           [0, 1, 0],
                           [0, 0, -1]])

    def setTop(self):

        self.setRotation([ [1, 0, 0],
                           [0, 0, 1],
                           [0, -1, 0]])

    def setAngled(self):

        self.setRotation([ [0.5, 0.5, -0.75],
                           [0, 0.75, 0.5],
                           [0.75, -0.5, 0.5]])

    def setRenderPerspective(self, state):

        self.renderWithPerspective = state != 0

        if self.renderWithPerspective:
            glMatrixMode(GL_PROJECTION)  # // Select The Projection Matrix
            glLoadIdentity()  # // Reset The Projection Matrix
            #field of view, aspect ratio, near and far
            # This will squash and stretch our objects as the window is resized.
            # Note that the near clip plane is 1 (hither) and the far plane is 1000 (yon)
            gluPerspective(45.0, float(self.width()) / float(self.height()), 1, 100.0)

        self.glDraw()

    def setMoveGrid(self, state):

        self.rightFootPoints = []
        self.leftFootPoints = []

        self.moveGrid = state != 0
        self.glDraw()
