from OpenGL.GL import *
from OpenGL.raw.GLUT import *
from PyQt4.QtGui import *

class SceneGraphNode:
    def __init__(self, positionOffset = QVector3D(0.0, 0.0, 0.0), rotationAxis = QVector3D(0,0,0)):
        self.positionOffset = positionOffset
        self.children = []
        self.rotationAxis = rotationAxis
        self.parent = None
        self.angle = 0
        self.distanceFromParent = 1
        self.position = QVector3D(0.0, 0.0, 0.0)

    def getPosition(self):
        return self.position

    def addChild(self, child):
        self.children += [child]
        child.parent = self

    def render(self):

        if self.parent is None:
            parentPos = QVector3D(0.0, 0.0, 0.0)
            parentM = QMatrix4x4()
            parentAngle = 0
            rotationAxis = QVector3D(0,0,0)
        else:
            parentPos = self.parent.getPosition()
            parentM = self.parent.m
            parentAngle = self.parent.angle
            rotationAxis = self.parent.rotationAxis

        self.m = QMatrix4x4()

        p = self.positionOffset

        self.m.rotate(parentAngle, rotationAxis.x(), rotationAxis.y(), rotationAxis.z())
        self.m = self.m * parentM
        p *= self.m
        p += parentPos
        glColor4f(0,1,0.75,1)
        glLineWidth(3)
        glBegin(GL_LINES)
        glVertex3f(parentPos.x(), parentPos.y(), parentPos.z())
        glVertex3f(p.x(), p.y(), p.z())
        glEnd()
        glPushMatrix()
        glTranslatef(p.x(), p.y(), p.z())
        glColor4f(1,0.75,0,1)
        glutSolidSphere(0.2, 10,10)
        glPopMatrix()
        self.position = p

        for child in self.children: child.render()

