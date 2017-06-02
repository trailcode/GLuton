from OpenGL.GL import *
from PyQt4.QtGui import QVector2D, QVector3D

def myGlVertex2f(self): glVertex2f(self.x(), self.y())

QVector2D.glVertexf = myGlVertex2f

def myGLVertex3f(self): glVertex3f(self.x(), self.y(), self.z())

def myGLTranslate3f(self): glTranslatef(self.x(), self.y(), self.z())

QVector3D.glVertexf = myGLVertex3f
QVector3D.glTranslatef = myGLTranslate3f