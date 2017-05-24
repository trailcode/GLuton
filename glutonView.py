import math
from math import cos, sin
from PyQt4.QtOpenGL import *
from OpenGL.GL import *
from OpenGL.GLU import *
import OpenGL.GLUT
from PyQt4.QtGui import QColor, QMatrix4x4, QVector2D, QVector3D, QVector4D, QQuaternion
from PyQt4.QtCore import QObject, Qt
from PyQt4.QtGui import *
from ArcBall import *

PI2 = 2.0*3.1415926535			# 2 * PI (not squared!) 		// PI Squared

# *********************** Globals ***********************
# Python 2.2 defines these directly

g_Transform = Matrix4fT ()
g_LastRot = Matrix3fT ()
g_ThisRot = Matrix3fT ()

g_ArcBall = ArcBallT (640, 480)
g_isDragging = False
g_quadratic = None

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

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);  # // Clear Screen And Depth Buffer
        glLoadIdentity();  # // Reset The Current Modelview Matrix
        glTranslatef(-1.5, 0.0, -6.0);  # // Move Left 1.5 Units And Into The Screen 6.0

        glPushMatrix();  # // NEW: Prepare Dynamic Transform
        glMultMatrixf(g_Transform);  # // NEW: Apply Dynamic Transform
        glColor3f(0.75, 0.75, 1.0);
        Torus(0.30, 1.00);
        glPopMatrix();  # // NEW: Unapply Dynamic Transform

        glLoadIdentity();  # // Reset The Current Modelview Matrix
        glTranslatef(1.5, 0.0, -6.0);  # // Move Right 1.5 Units And Into The Screen 7.0

        glPushMatrix();  # // NEW: Prepare Dynamic Transform
        glMultMatrixf(g_Transform);  # // NEW: Apply Dynamic Transform
        glColor3f(1.0, 0.75, 0.75);
        gluSphere(g_quadratic, 1.3, 20, 20);
        glPopMatrix();  # // NEW: Unapply Dynamic Transform

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
        g_ArcBall.setBounds(width, height)  # //*NEW* Update mouse bounds for arcball

    def initializeGL(self):
        global g_quadratic

        glClearColor(0.0, 0.0, 0.0, 1.0)  # This Will Clear The Background Color To Black
        glClearDepth(1.0)  # Enables Clearing Of The Depth Buffer
        glDepthFunc(GL_LEQUAL)  # The Type Of Depth Test To Do
        glEnable(GL_DEPTH_TEST)  # Enables Depth Testing
        glShadeModel(GL_FLAT);  # Select Flat Shading (Nice Definition Of Objects)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)  # Really Nice Perspective Calculations

        g_quadratic = gluNewQuadric();
        gluQuadricNormals(g_quadratic, GLU_SMOOTH);
        gluQuadricDrawStyle(g_quadratic, GLU_FILL);
        # Why? this tutorial never maps any textures?! ?
        # gluQuadricTexture(g_quadratic, GL_TRUE);			# // Create Texture Coords

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

    def mouseMoveEvent(self, event):
        #print('mouseMoveEvent: x=%d, y=%d' % (event.x(), event.y()))
        btns = event.buttons()
        x = event.x()
        y = event.y()

        global g_LastRot, g_Transform, g_ThisRot

        if btns & Qt.LeftButton:
            mouse_pt = Point2fT(x, y)
            ThisQuat = g_ArcBall.drag(mouse_pt)  # // Update End Vector And Get Rotation As Quaternion
            g_ThisRot = Matrix3fSetRotationFromQuat4f(ThisQuat)  # // Convert Quaternion Into Matrix3fT
            # Use correct Linear Algebra matrix multiplication C = A * B
            g_ThisRot = Matrix3fMulMatrix3f(g_LastRot, g_ThisRot)  # // Accumulate Last Rotation Into This One
            g_Transform = Matrix4fSetRotationFromMatrix3f(g_Transform,
                                                          g_ThisRot)  # // Set Our Final Transform's Rotation From This One

        self.paintGL()
        self.swapBuffers()
        self.repaint()

    def mousePressEvent(self, event):
        btns = event.buttons()
        x = event.x()
        y = event.y()
        global g_isDragging, g_LastRot, g_Transform, g_ThisRot
        if btns & Qt.LeftButton:
            g_LastRot = copy.copy(g_ThisRot);  # // Set Last Static Rotation To Last Dynamic One
            g_isDragging = True  # // Prepare For Dragging
            mouse_pt = Point2fT(x, y)
            g_ArcBall.click(mouse_pt);  # // Update Start Vector And Prepare For Dragging


    def wheelEvent(self, event):
        """
        Called by the Qt libraries whenever the window receives a mouse wheel change.

        This is used for zooming, or rather moving the camera ahead.
        """
        delta = event.delta()

        atype = type(event);
        ll = dir(event)
        for i in ll: print(i)
        #fsdfds

        self.paintGL()
        self.swapBuffers()
        self.repaint()