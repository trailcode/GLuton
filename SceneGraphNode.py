from OpenGL.GL import *
from OpenGL.raw.GLUT import *
from PyQt4.QtGui import QVector3D, QMatrix4x4
import util

class SceneGraphNode:
    """Class representing a scene graph node representing a servo. The servo can rotation around a defined axis"""
    def __init__(self,
                 positionOffset = QVector3D(0.0, 0.0, 0.0),
                 rotationAxis = QVector3D(0,0,0),
                 #angleOffset = 0
                 color = [1,0.75,0,1]
                 ):
        self.positionOffset = positionOffset
        self.children = []
        self.rotationAxis = rotationAxis
        self.parent = None # type: SceneGraphNode
        self.rotationMatrix = None # type: QMatrix4x4
        self.angle = 0
        self.angleOffset = 0
        self.color = color
        self.position = QVector3D(0.0, 0.0, 0.0)
        self.highlighted = False

    def setAngle(self, angle: float):
        self.angle = angle + self.angleOffset

    def getPosition(self):
        return self.position

    def addChild(self, child):
        self.children += [child]
        child.parent = self

    def updatePosition(self):

        if self.parent is None:
            self.parentPos = QVector3D(0.0, 0.0, 0.0)
            parentM = QMatrix4x4()
            parentAngle = 0
            rotationAxis = QVector3D(0,0,0)
        else:
            self.parentPos = self.parent.getPosition()
            parentM = self.parent.rotationMatrix
            parentAngle = self.parent.angle
            rotationAxis = self.parent.rotationAxis

        self.rotationMatrix = QMatrix4x4()

        # Need to make a copy of the position offset because it is going to be changed.
        p = self.positionOffset

        self.rotationMatrix.rotate(parentAngle, rotationAxis)
        self.rotationMatrix = self.rotationMatrix * parentM
        p *= self.rotationMatrix
        p += self.parentPos
        self.mm = QMatrix4x4(self.rotationMatrix)
        axis = self.rotationAxis
        axis *= self.rotationMatrix
        self.mm.rotate(self.angle, axis.x(), axis.y(), axis.z())
        self.mm = self.mm.transposed()
        self.position = p

        for child in self.children: child.updatePosition()

    def render(self):
        glDisable(GL_LIGHTING)
        glColor4f(0, 1, 0.75, 1)
        glLineWidth(3)
        glBegin(GL_LINES)
        self.parentPos.glVertexf()
        self.position.glVertexf()
        glEnd()
        glEnable(GL_LIGHTING)
        glPushMatrix()
        self.position.glTranslatef()
        if self.highlighted:    glColor4f(1, 1, 0.3, 1)
        else:                   glColor4f(self.color[0], self.color[1], self.color[2], 0.6)
        glMultMatrixf(self.mm.data())
        glutSolidCube(0.2)
        glPopMatrix()

        for child in self.children: child.render()


