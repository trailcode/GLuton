from OpenGL.GL import *
from OpenGL.raw.GLUT import *
from PyQt4.QtGui import *

class SceneGraphNode:
    def __init__(self,
                 positionOffset = QVector3D(0.0, 0.0, 0.0),
                 rotationAxis = QVector3D(0,0,0),
                 #angleOffset = 0
                 color = [1,0.75,0,1]
                 ):
        self.positionOffset = positionOffset
        self.children = []
        self.rotationAxis = rotationAxis
        self.parent = None
        self.angle = 0
        #self.angleOffset = angleOffset
        self.angleOffset = 0
        self.color = color
        self.position = QVector3D(0.0, 0.0, 0.0)

    def setAngle(self, angle):
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
            parentM = self.parent.m
            parentAngle = self.parent.angle
            rotationAxis = self.parent.rotationAxis

        self.m = QMatrix4x4()

        p = self.positionOffset

        self.m.rotate(parentAngle, rotationAxis.x(), rotationAxis.y(), rotationAxis.z())
        self.m = self.m * parentM
        p *= self.m
        p += self.parentPos
        self.mm = QMatrix4x4(self.m)
        axis = self.rotationAxis
        axis *= self.m
        self.mm.rotate(self.angle, axis.x(), axis.y(), axis.z())
        self.mm = self.mm.transposed()
        self.position = p

        for child in self.children: child.updatePosition()

    def render(self):
        glDisable(GL_LIGHTING)
        glColor4f(0, 1, 0.75, 1)
        glLineWidth(3)
        glBegin(GL_LINES)
        glVertex3f(self.parentPos.x(), self.parentPos.y(), self.parentPos.z())
        glVertex3f(self.position.x(), self.position.y(), self.position.z())
        glEnd()
        glEnable(GL_LIGHTING)
        glPushMatrix()
        glTranslatef(self.position.x(), self.position.y(), self.position.z())
        glColor4f(self.color[0], self.color[1], self.color[2], 1)
        glMultMatrixf(self.mm.data())
        glutSolidCube(0.2)
        # glutSolidSphere(0.2, 10, 10)
        glPopMatrix()

        for child in self.children: child.render()


