# FEALinkLink
# Ryan Arata
# updated May 2016
#
# This module implements the Link class

import matplotlib
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import FEALinkNode
import FEALinkMaterial

class Link(object):
    def plotLink(self,display,showNumbers=True):
        if self.dimensions == 2:
            display.plot(self.x,self.y,'b')
            if showNumbers == True:
                display.text(self.xmid,self.ymid,'%s' % str(self.number),size=11,color='b')
        else:
            display.plot(self.x,self.y,self.z,'b')
            if showNumbers == True:
                display.text(self.xmid,self.ymid,self.zmid,'%s' % str(self.number),size=11,zorder=1,color='b')
        return

    def getAngles(self):
        if self.dimensions == 2:
            self.cos = (self.x[1]-self.x[0])/self.length
            self.sin = (self.y[1]-self.y[0])/self.length
        else:
            self.cosx = (self.x[1]-self.x[0])/self.length
            self.cosy = (self.y[1]-self.y[0])/self.length
            self.cosz = (self.z[1]-self.z[0])/self.length
        return

    def __str__(self):
        output = "Link __str__ function not yet implemented"
        return output

    def __init__(self,num,node1,node2,material):
        self.number = num
        self.node1 = node1 # FEALinkNode.Node object
        self.node2 = node2
        self.material = material # FEALinkMaterial.Material object
        self.dimensions = node1.dimensions
        self.x = [node1.x,node2.x]
        self.y = [node1.y,node2.y]
        self.xmid = (.55*node1.x+.45*node2.x)
        self.ymid = (.55*node1.y+.45*node2.y)
        if self.dimensions == 2:
            self.length = np.sqrt((self.x[0]-self.x[1])**2 + (self.y[0]-self.y[1])**2)
        else:
            self.z = [node1.z,node2.z]
            self.zmid = (.55*node1.z+.45*node2.z)
            self.length = np.sqrt((self.x[0]-self.x[1])**2 + (self.y[0]-self.y[1])**2 + (self.z[0]-self.z[1])**2)
        self.getAngles()
