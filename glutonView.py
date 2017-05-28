from math import cos, sin
from OpenGL.raw.GLUT import glutSolidCube
from PyQt4.QtOpenGL import *
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt4.QtCore import QObject, Qt
from PyQt4.QtGui import *
from ArcBall import *
from SceneGraphNode import SceneGraphNode

PI2 = 2.0*3.1415926535			# 2 * PI (not squared!) 		// PI Squared

def Torus(MinorRadius, MajorRadius):
	# // Draw A Torus With Normals
	glBegin( GL_TRIANGLE_STRIP );									# // Start A Triangle Strip
	for i in range (20): 											# // Stacks
		for j in range (-1, 20): 										# // Slices
			# NOTE, python's definition of modulus for negative numbers returns
			# results different than C's
			#       (a / d)*d  +  a % d = a
			if (j < 0):
				wrapFrac = (-j%20)/20.0
				wrapFrac *= -1.0
			else:
				wrapFrac = (j%20)/20.0;
			phi = PI2*wrapFrac;
			sinphi = sin(phi);
			cosphi = cos(phi);

			r = MajorRadius + MinorRadius*cosphi;

			glNormal3f (sin(PI2*(i%20+wrapFrac)/20.0)*cosphi, sinphi, cos(PI2*(i%20+wrapFrac)/20.0)*cosphi);
			glVertex3f (sin(PI2*(i%20+wrapFrac)/20.0)*r, MinorRadius*sinphi, cos(PI2*(i%20+wrapFrac)/20.0)*r);

			glNormal3f (sin(PI2*(i+1%20+wrapFrac)/20.0)*cosphi, sinphi, cos(PI2*(i+1%20+wrapFrac)/20.0)*cosphi);
			glVertex3f (sin(PI2*(i+1%20+wrapFrac)/20.0)*r, MinorRadius*sinphi, cos(PI2*(i+1%20+wrapFrac)/20.0)*r);
	glEnd();														# // Done Torus


class GlutonView(QGLWidget):
    def __init__(self, servoAdjustment, parent = None):
        super(GlutonView, self).__init__(parent)
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

        self.servos = {}

        self.root = SceneGraphNode()
        self.servos['root'] = self.root

        def addServo(name, parent, servo):
            self.servos[name] = servo
            self.servos[parent].addChild(servo)

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


    def paintGL(self):
        self.makeCurrent()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        glLoadIdentity()
        glTranslatef(0, 0.0, self.distance)

        glPushMatrix()
        glMultMatrixf(self.transform)
        self.drawGroundGrid()
        glColor3f(1, 0.75, 0.75)
        self.root.updatePosition()
        self.root.render()
        glPopMatrix()

    def drawGroundGrid(self):
        glDisable(GL_LIGHTING)
        glColor3f(0,0.7,.3)
        glLineWidth(1)
        glBegin(GL_LINES)
        size = 10
        for i in range(-size, size + 1):
            glVertex3f(i, 0, size)
            glVertex3f(i, 0, -size)
            glVertex3f(size, 0, i)
            glVertex3f(-size, 0, i)
        glEnd()


    def resizeGL(self, width, height):
        if height == 0:  # Prevent A Divide By Zero If The Window Is Too Small
            height = 1

        glViewport(0, 0, width, height)  # Reset The Current Viewport And Perspective Transformation
        glMatrixMode(GL_PROJECTION)  # // Select The Projection Matrix
        glLoadIdentity()  # // Reset The Projection Matrix
        # // field of view, aspect ratio, near and far
        # This will squash and stretch our objects as the window is resized.
        # Note that the near clip plane is 1 (hither) and the far plane is 1000 (yon)
        gluPerspective(45.0, float(width) / float(height), 1, 100.0)

        glMatrixMode(GL_MODELVIEW);  # // Select The Modelview Matrix
        glLoadIdentity();  # // Reset The Modelview Matrix
        self.arcBall.setBounds(width, height)  # //*NEW* Update mouse bounds for arcball

    def initializeGL(self):

        glClearColor(0.0, 0.0, 0.0, 1.0)  # This Will Clear The Background Color To Black
        glClearDepth(1.0)  # Enables Clearing Of The Depth Buffer
        glDepthFunc(GL_LEQUAL)  # The Type Of Depth Test To Do
        glEnable(GL_DEPTH_TEST)  # Enables Depth Testing
        glShadeModel(GL_FLAT);  # Select Flat Shading (Nice Definition Of Objects)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)  # Really Nice Perspective Calculations

        self.quadratic = gluNewQuadric();
        gluQuadricNormals(self.quadratic, GLU_SMOOTH);
        gluQuadricDrawStyle(self.quadratic, GLU_FILL);
        # Why? this tutorial never maps any textures?! ?
        # gluQuadricTexture(self.quadratic, GL_TRUE);			# // Create Texture Coords

        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHTING)

        glEnable(GL_COLOR_MATERIAL)

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

    def doRotate(self, x, y):
        mouse_pt = Point2fT(x, y)
        ThisQuat = self.arcBall.drag(mouse_pt)  # // Update End Vector And Get Rotation As Quaternion
        self.thisRot = Matrix3fSetRotationFromQuat4f(ThisQuat)  # // Convert Quaternion Into Matrix3fT
        # Use correct Linear Algebra matrix multiplication C = A * B
        self.thisRot = Matrix3fMulMatrix3f(self.lastRot, self.thisRot)  # // Accumulate Last Rotation Into This One
        self.transform = Matrix4fSetRotationFromMatrix3f(self.transform,
                                                         self.thisRot)  # // Set Our Final Transform's Rotation From This One
        self.transform[3][3] = 1.0  # Prevent objects getting smaller and drifting apart over time

    def mouseMoveEvent(self, event):
        #print('mouseMoveEvent: x=%d, y=%d' % (event.x(), event.y()))

        if event.buttons() & Qt.LeftButton: self.doRotate(event.x(), event.y())

        self.paintGL()
        self.swapBuffers()
        self.repaint()

    def mousePressEvent(self, event):
        btns = event.buttons()
        x = event.x()
        y = event.y()
        if btns & Qt.LeftButton:
            self.lastRot = copy.copy(self.thisRot);  # // Set Last Static Rotation To Last Dynamic One
            mouse_pt = Point2fT(x, y)
            self.arcBall.click(mouse_pt);  # // Update Start Vector And Prepare For Dragging


    def wheelEvent(self, event : QWheelEvent):
        """
        Called by the Qt libraries whenever the window receives a mouse wheel change.

        This is used for zooming, or rather moving the camera ahead.
        """
        delta = event.delta()
        if delta == 0: return
        btns = event.buttons()
        moda = event.modifiers()
        x = event.x()
        y = event.y()
        self.lastRot = copy.copy(self.thisRot);  # // Set Last Static Rotation To Last Dynamic One
        mouse_pt = Point2fT(x, y)
        self.arcBall.click(mouse_pt);  # // Update Start Vector And Prepare For Dragging
        if moda & Qt.ShiftModifier : self.doRotate(x, y + delta)
        elif moda & Qt.AltModifier: self.doRotate(x + delta, y)
        else:
            self.distance += delta * 0.10
        #print('delta', delta, 'x', event.x(), 'y', event.y(), 'xx', event.globalX(), 'yy', event.globalY())

        self.paintGL()
        self.swapBuffers()
        self.repaint()