# FEALinkNode
# Ryan Arata
# updated May 2016
#
# This module implements the Node class

import matplotlib
from mpl_toolkits.mplot3d import Axes3D
import FEALinkScope
import numpy as np
import Arrow3D

class Node(object):
    def addConstraints(self,x=None,y=None,z=None):
        self.xconstrain = x
        self.yconstrain = y
        if self.dimensions == 3:
            self.zconstrain = z

    def addForce(self,x,y,z=0):
        self.xforce = float(x)
        self.yforce = float(y)
        if self.dimensions == 3:
            self.zforce = float(z)

    def deleteConstraints(self):
        self.xconstrain = None
        self.yconstrain = None
        if self.dimensions == 3:
            self.zconstrain = None

    def deleteForce(self):
        self.xforce = 0
        self.yforce = 0
        if self.dimensions == 3:
            self.zforce = 0

    def isConstrained(self): # returns true if there is any constraint placed on the node
        if self.dimensions == 2:
            if self.xconstrain != None or self.yconstrain != None:
                return True
        else:
            if self.xconstrain != None or self.yconstrain != None or self.zconstrain != None:
                return True
        return False

    def numConstraints(self):
        num = 0
        if self.xconstrain != None: num += 1
        if self.yconstrain != None: num += 1
        if self.dimensions == 3 and self.zconstrain != None: num += 1
        return num

    def hasForce(self):
        if self.xforce or self.yforce:
            return True
        if self.dimensions == 3 and self.zforce:
            return True
        return False

    def forceMagnitude(self):
        if self.dimensions == 2:
            magnitude = np.sqrt(self.xforce**2 + self.yforce**2)
        else:
            magnitude = np.sqrt(self.xforce**2 + self.yforce**2 + self.zforce**2)
        return magnitude

    def plotNode(self,display,scope,showNumbers=True,showConstraints=True,showForces=True,maxForce=0):
        if maxForce != 0:
            magnitude = self.forceMagnitude()
            relativeMagnitude = magnitude/maxForce
        else:
            relativeMagnitude = 1

        # 2D plot
        if self.dimensions == 2:
            # plot node points
            display.plot(self.x,self.y,'k.')

            # plot node numbers
            if showNumbers:
                display.text(self.x,self.y,'%s' % str(self.number),size=11)

            # plot constraints
            if showConstraints:
                if self.xconstrain != None:
                    headLength = .03*scope.modelSize
                    headWidth = .02*scope.modelSize
                    if self.xconstrain == 0:
                        display.arrow(self.x-headLength-1e-99,self.y,1e-99,0,
                                        ec='c',fc='w',head_width=headWidth,head_length=headLength)
                    elif abs(self.xconstrain) <= headLength:
                        display.arrow(self.x-np.sign(self.xconstrain)*headLength+self.xconstrain,self.y,
                                        1e-99*np.sign(self.xconstrain),0,
                                        ec='m',fc='w',head_width=headWidth,head_length=headLength)
                    else:
                        display.arrow(self.x,self.y,self.xconstrain-np.sign(self.xconstrain)*headLength,0,ec='m',fc='w',
                                        head_width=headWidth,head_length=headLength)

                if self.yconstrain != None:
                    headLength = .03*scope.modelSize
                    headWidth = .02*scope.modelSize
                    if self.yconstrain == 0:
                        display.arrow(self.x,self.y-headLength-1e-99,0,1e-99,
                                        ec='c',fc='w',head_width=headWidth,head_length=headLength)
                    elif abs(self.yconstrain) <= headLength:
                        display.arrow(self.x,self.y-np.sign(self.yconstrain)*headLength+self.yconstrain,
                                        0,1e-99*np.sign(self.yconstrain),
                                        ec='m',fc='w',head_width=headWidth,head_length=headLength)
                    else:
                        display.arrow(self.x,self.y,0,self.yconstrain-np.sign(self.yconstrain)*headLength,ec='m',fc='w',
                                        head_width=headWidth,head_length=headLength)

            # plot forces
            if showForces and self.hasForce():
                headLength = .02*scope.modelSize
                arrowLength = max(1.1*headLength,.15*relativeMagnitude*scope.modelSize)
                headWidth = .015*scope.modelSize
                lineWidth = .005*scope.modelSize
                magnitude = np.sqrt(self.xforce**2 + self.yforce**2)
                xdisp = self.xforce/magnitude*arrowLength
                xlen = self.xforce/magnitude*(arrowLength-headLength)
                ydisp = self.yforce/magnitude*arrowLength
                ylen = self.yforce/magnitude*(arrowLength-headLength)
                display.arrow(self.x-xdisp,self.y-ydisp,xlen,ylen,ec='r',fc='r',head_width=headWidth,head_length=headLength,width=lineWidth)


        # 3D plot
        else:
            display.plot([self.x],[self.y],[self.z],'k.')
            if showNumbers:
                display.text(self.x,self.y,self.z,'%s' % str(self.number),size=11,zorder=1)


            if showConstraints:
                if self.xconstrain != None:
                    headLength = .04*scope.modelSize
                    if self.xconstrain == 0:
                        arrow = Arrow3D.Arrow3D([self.x-headLength-1e-99,self.x+self.xconstrain],[self.y,self.y],[self.z,self.z],
                                                color = 'c',arrowstyle = '->',mutation_scale=20)
                        display.add_artist(arrow)
                    elif abs(self.xconstrain) <= headLength:
                        arrow = Arrow3D.Arrow3D([self.x-np.sign(self.xconstrain)*headLength+self.xconstrain,self.x+self.xconstrain],
                                                [self.y,self.y],[self.z,self.z],color = 'm',arrowstyle = '->',mutation_scale=20)
                        display.add_artist(arrow)
                    else:
                        arrow = Arrow3D.Arrow3D([self.x,self.x+self.xconstrain],[self.y,self.y],[self.z,self.z],
                                                color = 'm',arrowstyle = '->',mutation_scale = 20)
                        display.add_artist(arrow)

                if self.yconstrain != None:
                    headLength = .04*scope.modelSize
                    if self.yconstrain == 0:
                        arrow = Arrow3D.Arrow3D([self.x,self.x],[self.y-headLength,self.y],[self.z,self.z],
                                                color = 'c',arrowstyle = '->',mutation_scale=20)
                        display.add_artist(arrow)
                    elif abs(self.yconstrain) <= headLength:
                        arrow = Arrow3D.Arrow3D([self.x,self.x],
                                                [self.y-np.sign(self.yconstrain)*headLength+self.yconstrain,self.y+self.yconstrain],
                                                [self.z,self.z],color = 'm',arrowstyle = '->',mutation_scale=20)
                        display.add_artist(arrow)
                    else:
                        arrow = Arrow3D.Arrow3D([self.x,self.x],[self.y,self.y+self.yconstrain],[self.z,self.z],
                                                color = 'm',arrowstyle = '->',mutation_scale = 20)
                        display.add_artist(arrow)

                if self.zconstrain != None:
                    headLength = .04*scope.modelSize
                    if self.zconstrain == 0:
                        arrow = Arrow3D.Arrow3D([self.x,self.x],[self.y,self.y],[self.z-headLength,self.z],
                                                color = 'c',arrowstyle = '->',mutation_scale=20)
                        display.add_artist(arrow)
                    elif abs(self.zconstrain) <= headLength:
                        arrow = Arrow3D.Arrow3D([self.x,self.x],[self.y,self.y],
                                                [self.z-np.sign(self.zconstrain)*headLength+self.zconstrain,self.z+self.zconstrain],
                                                color = 'm',arrowstyle = '->',mutation_scale=20)
                        display.add_artist(arrow)
                    else:
                        arrow = Arrow3D.Arrow3D([self.x,self.x],[self.y,self.y],[self.z,self.z+self.zconstrain],
                                                color = 'm',arrowstyle = '->',mutation_scale = 20)
                        display.add_artist(arrow)

            if showForces and self.hasForce():
                arrowLength = .3*relativeMagnitude*scope.modelSize
                magnitude = np.sqrt(self.xforce**2 + self.yforce**2 + self.zforce**2)
                xdisp = self.xforce/magnitude*arrowLength
                ydisp = self.yforce/magnitude*arrowLength
                zdisp = self.zforce/magnitude*arrowLength
                arrow = Arrow3D.Arrow3D([self.x-xdisp,self.x],[self.y-ydisp,self.y],[self.z-zdisp,self.z],
                                                color='r',arrowstyle='-|>',mutation_scale=20)
                display.add_artist(arrow)
        return

    def linkToNode(self,num): # returns false if already linked to that node 
        if num in self.linkedNodes:
            return False
        else:
            self.linkedNodes.append(num)
        return True

    def disconnectFromNode(self,num):
        self.linkedNodes.remove(num)
        return

    def isLinked(self):
        if len(self.linkedNodes) != 0:
            return True
        return False

    def addSolution(self,displacement,reaction): # nodes with solutions will only exist in the list as part of the Solution class
        self.xdisp = displacement[0]
        self.xsol = self.x + self.xdisp
        if self.xconstrain != None:
            self.xreact = reaction[0]
        else:
            self.xreact = 0

        self.ydisp = displacement[1]
        self.ysol = self.y + self.ydisp
        self.yreact = reaction[1] - self.yforce
        if self.yconstrain != None:
            self.yreact = reaction[1]
        else:
            self.yreact = 0

        if self.dimensions == 3:
            self.zdisp = displacement[2]
            self.zsol = self.z + self.zdisp
            if self.zconstrain != None:
                self.zreact = reaction[2]
            else:
                self.zreact = 0

        return

    def __str__(self):
        output = "Node __str__ function not yet implemented"
        return output

    def __init__(self,num,x,y,z=None):
        self.number = num
        self.x = x
        self.y = y
        self.xconstrain = None
        self.yconstrain = None
        self.xforce = 0
        self.yforce = 0

        if z is None:
            self.dimensions = 2
        else: # only define z-direction if z given (indicating 3d model)
            self.dimensions = 3
            self.z = z
            self.zconstrain = None
            self.zforce = 0

        self.linkedNodes = list() # list of nodes this node is linked to
