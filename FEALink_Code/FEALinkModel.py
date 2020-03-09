# FEALinkModel
# Ryan Arata
# updated May 2016
#
# This module implements the Model class, including the GUI interface

try:
    from Tkinter import *
except:
    from tkinter import *
import numpy as np
import matplotlib
try:
    import cPickle as pickle
except:
    import pickle
try:
    import FileDialog
    import tkFileDialog as tkfd
except:
    import tkinter.filedialog as tkfd
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import matplotlib.lines as mlines 
from mpl_toolkits.mplot3d import Axes3D
try:
    import ttk
except:
    import tkinter.ttk as ttk
import FEALinkMaterial
import FEALinkNode
import FEALinkLink
import FEALinkScope
import FEALinkSolution

class Model(object):
################## Interface Behavior Methods ##################
#---Keypress Handling---
    def on_key_event(self,event):
        print('you pressed %s' % event.key)
        key_press_handler(event, self.canvas, self.toolbar)
        return
        
#---Interface updates---
    def wipeErrorLabels(self):
        self.matErrorLabel.config(fg="red",text="")
        self.nodeErrorLabel.config(fg="red",text="")
        self.linkErrorLabel.config(fg="red",text="")
        self.conErrorLabel.config(fg="red",text="")
        self.forceErrorLabel.config(fg="red",text="")
        self.solErrorLabel.config(fg="red",text="")

    def updateNotes(self):
        self.units['mass'] = self.noteMassEntry.get()
        self.units['length'] = self.noteLengthEntry.get()
        self.units['time'] = self.noteTimeEntry.get()
        try:
            self.notes = self.noteText.get(0.0,END)
        except:
            self.notes = ""
        return


    def updatePlot(self):
        self.updateNotes()
        
        self.display.cla()
        if self.showModel.get():
            self.plotModel()
        if self.showExag.get():
            self.plotExaggeration()
        if self.showResult.get():
            self.plotResults()

        # show axes
        self.display.set_xlabel('x (' + self.units['length'] + ')')
        self.display.set_ylabel('y (' + self.units['length'] + ')')
        if self.dimensions == 3:
            self.display.set_zlabel('z (' + self.units['length'] + ')')

        # scale axes
        self.display.set_xlim(self._Scope.xlimits)
        self.display.set_ylim(self._Scope.ylimits)
        if self.dimensions == 3:
            self.display.set_zlim(self._Scope.zlimits)

        self.canvas.draw()
        return

    def plotModel(self):
        # Show empty plot if there are no nodes
        if len(self._Nodes) == 0:
            self.canvas.show()
            return

        # 2d plot
        if self.dimensions == 2:
            # plot nodes and get limits
            for num,node in self._Nodes.items():
                node.plotNode(self.display,self._Scope,showNumbers=self.nodeNumbers.get(),showConstraints=self.showConstraints.get(),
                                showForces=self.showForces.get(),maxForce=self.getMaxForce())

            # plot links
            for num,link in self._Links.items():
                link.plotLink(self.display,showNumbers=self.linkNumbers.get())

        # 3d plot
        else:
            # plot nodes and get limits
            for num,node in self._Nodes.items():
                node.plotNode(self.display,self._Scope,showNumbers=self.nodeNumbers.get(),showConstraints=self.showConstraints.get(),
                                showForces=self.showForces.get(),maxForce=self.getMaxForce())

            # plot links
            for num,link in self._Links.items():
                link.plotLink(self.display,self.linkNumbers.get())
        return

    def plotExaggeration(self):
        if self._Solution == None:
            self.solErrorLabel.config(text="Error: No solution to plot")
            self.solutionPage.after(2500,self.wipeErrorLabels)
            return

        # plot nodes
        for num,node in self._Solution._SolNodes.items():
            node.plotExaggerated(self.display,showNumbers = (self.nodeNumbers.get() and not self.showModel.get() and not self.showResult.get()))

        # get and show max stress if desired
        maxStress = None
        minStress = None
        if self.showStress.get(): 
            self.makeStressLegend()
            maxStress = self._Solution.maxStress
            minStress = self._Solution.minStress

        # plot links
        for num,link in self._Solution._SolLinks.items():
            link.plotExaggerated(self.display,maxStress = maxStress,minStress = minStress,showNumbers = 
                                    (self.linkNumbers.get() and not self.showModel.get() and not self.showResult.get()))

        self.canvas.draw()
        return

    def plotResults(self):
        if self._Solution == None:
            self.solErrorLabel.config(text="Error: No solution to plot")
            self.solutionPage.after(2500,self.wipeErrorLabels)
            return

        # plot nodes
        for num,node in self._Solution._SolNodes.items():
            node.plot(self.display,showNumbers = (self.nodeNumbers.get() and not self.showModel.get()))

        maxStress = None
        minStress = None
        if self.showStress.get(): 
            self.makeStressLegend()
            maxStress = self._Solution.maxStress
            minStress = self._Solution.minStress

        # plot links
        for num,link in self._Solution._SolLinks.items():
            link.plot(self.display,maxStress = maxStress,minStress = minStress,showNumbers = (self.linkNumbers.get() and not self.showModel.get()))

        return

    def makeStressLegend(self):
        maxStress = self._Solution.maxStress
        minStress = self._Solution.minStress
        tensionLine = mlines.Line2D([],[],color='red',label = ('%.4g' % maxStress))
        neutralLine = mlines.Line2D([],[],color='black',label = '0')
        compressionLine = mlines.Line2D([],[],color=(0,1,0), label = ('%.4g' % minStress))
        self.display.legend(bbox_to_anchor=(0., .94, 1., .06), loc=3,
            ncol=3, mode="expand", borderaxespad=0., prop={'size':10}, handles = [tensionLine,neutralLine,compressionLine])
        return

    def updateLists(self):
        self.updateMaterialList()
        self.updateNodeList()
        self.updateLinkList()
        self.updateConstraintList()
        self.updateForceList()
        if self._Solution != None:
            self.updateSolutionNotebook()
        return

#---Command Line---
    def upCommand(self,event=None):
        if len(self._CommandList) == 0:
            return "break"
        elif self.commandIndex == -1:
            return "break"
        elif self.commandIndex == 0:
            self.commandLine.delete(0,END)
            self.commandIndex = -1
            return "break"
        self.commandIndex -= 1
        self.commandLine.delete(0,END)
        self.commandLine.insert(0,str(self._CommandList[self.commandIndex]))
        return "break"

    def downCommand(self,event=None):
        if self.commandIndex >= len(self._CommandList)-1:
            self.commandLine.delete(0,END)
            self.commandIndex = len(self._CommandList)
            return "break"
        self.commandIndex += 1
        self.commandLine.delete(0,END)
        self.commandLine.insert(0,str(self._CommandList[self.commandIndex]))
        return "break"

    def executeCommand(self,event=None):
        text = self.commandLine.get()
        self._CommandList.append(text)
        self.commandLine.delete(0,END)
        self.commandIndex = len(self._CommandList)

        command = [x.strip() for x in text.split(',')]
        commandType = command[0].lower()
        del command[0]

        if commandType in ['m','material']:
            self.commandNewMaterial(command)
        elif commandType in ['dm','deletematerial']:
            self.commandDeleteMaterial(command)
        elif commandType in ['n','node','createnode','newnode']:
            self.commandNewNode(command)
        elif commandType in ['dn','deletenode']:
            self.commandDeleteNode(command)
        elif commandType in ['l','link','createlink','newlink']:
            self.commandNewLink(command)
        elif commandType in ['dl','deletelink']:
            self.commandDeleteLink(command)
        elif commandType in ['c','d','constrain','constraint','displacement']:
            self.commandAddConstraint(command)
        elif commandType in ['dc','dd','deleteconstraint','deleteconstrain','deletedisplacement']:
            self.commandDeleteConstraint(command)
        elif commandType in ['f','force','addforce']:
            self.commandAddForce(command)
        elif commandType in ['df','deleteforce']:
            self.commandDeleteForce(command)
        elif commandType in ['mn','multinode','linnode','linearnode']:
            self.commandLinNode(command)
        elif commandType in ['ml','multilink']:
            self.commandMultiLink(command)
        elif commandType in ['s','solve']:
            self.commandSolve()
        elif commandType in ['nn','nodenumbers']:
            self.nodeNumCheck.toggle()
            self.updatePlot()
        elif commandType in ['ln','linknumbers']:
            self.linkNumCheck.toggle()
            self.updatePlot()
        elif commandType in ['sf','showforce','showforces']:
            self.forceCheck.toggle()
            self.updatePlot()
        elif commandType in ['sc','showconstrain','showconstraint','showconstraints']:
            self.constraintCheck.toggle()
            self.updatePlot()
        elif commandType in ['save']:
            self.save()
        elif commandType in ['saveas']:
            self.saveAs()
        elif commandType in ['update','plot','up', 'updateplot','replot','rp']:
            self.updatePlot()
        elif commandType in ['pe','ex','plotexaggerated','ed','exaggerateddeformation','ped','exag']:
            self.plotExagCheck.toggle()
            self.updatePlot()
        elif commandType in ['p','pm','plotmodel','show','showmodel','sm','plotpreloadedmodel','ppm','pplm']:
            if self.showResult.get() or self.showExag.get():
                self.plotModelCheck.toggle()
            self.updatePlot()
        elif commandType in ['pr','plotresult','plotresults','sr','showresult','showresults','per','plotexact','plotexactresults']:
            self.plotResultCheck.toggle()
            self.updatePlot()
        elif commandType in ['ss','showstress','ps','plotstress']:
            self.showStressCheck.toggle()
            self.updatePlot()
        elif commandType in ['q','quit']:
            self.root.destroy()
        else:
            self.commandLine.insert(0,"invalid commmand")
            self.commandLine.select_range(0,END)
        return

    def commandNewMaterial(self,command):
        self.notebook.select(self.materialPage)
        if len(command) > 3:
            self.matErrorLabel.config(text="Error: Command sequence too long")
            self.materialPage.after(2500,self.wipeErrorLabels)
            return
        while len(command) < 3:
            command.append("")
        if command[0] == "":
            if not self._Materials:
                command[0] = 0
            else:
                command[0] = str(max(self._Materials)+1) # autoNumber if no number given
        self.matNumEntry.delete(0,END); self.matNumEntry.insert(0,command[0])
        self.matAreaEntry.delete(0,END); self.matAreaEntry.insert(0,command[1])
        self.matModEntry.delete(0,END); self.matModEntry.insert(0,command[2])

        self.newMaterial()
        return

    def commandDeleteMaterial(self,command):
        self.notebook.select(self.materialPage)

        # parse a:b or a:step:b to list
        if len(command) == 1 and ":" in command[0]:
            command = [x.strip() for x in command[0].split(':')]
            try:
                if len(command) == 3:
                    a = int(command[0]); b = int(command[2]); step = int(command[1]);
                else:
                    a = int(command[0]); b = int(command[1]); step = 1
                command = list(np.arange(a,b,step))
                command.append(b)
            except:
                self.matErrorLabel.config(fg='red',text = "Error: Invalid syntax for deletematerial")
                self.matPage.after(2500,self.wipeErrorLabels)
                return

        errorList = list()
        for num in command:
            self.matDelEntry.delete(0,END); self.matDelEntry.insert(0,num)
            self.deleteMaterial()
            if self.matErrorLabel.cget("text") != "":
                self.matErrorLabel.config(text = "")
                errorList.append(num)
        if len(errorList) > 0:
            self.matErrorLabel.config(fg="red",text = "Errors deleting materials: " + str(errorList))
            self.materialPage.after(2500,self.wipeErrorLabels)
        return

    def commandNewNode(self,command):
        self.notebook.select(self.nodePage)
        if len(command) > 1+self.dimensions:
            self.nodeErrorLabel.config(text="Error: Command sequence too long")
            self.nodePage.after(2500,self.wipeErrorLabels)
            return
        while len(command) < 1+self.dimensions:
            command.append("")
        if command[0] == "":
            if not self._Nodes:
                command[0] = 0
            else:
                command[0] = str(max(self._Nodes)+1) # autoNumber if no number given

        self.nodeNumEntry.delete(0,END); self.nodeNumEntry.insert(0,command[0])
        self.nodeXEntry.delete(0,END); self.nodeXEntry.insert(0,command[1])
        self.nodeYEntry.delete(0,END); self.nodeYEntry.insert(0,command[2])
        if self.dimensions == 3:
            self.nodeZEntry.delete(0,END); self.nodeZEntry.insert(0,command[3])
        self.newNode()
        return

    def commandDeleteNode(self,command):
        self.notebook.select(self.nodePage)

        # parse a:b or a:step:b to list
        if len(command) == 1 and ":" in command[0]:
            command = [x.strip() for x in command[0].split(':')]
            try:
                if len(command) == 3:
                    a = int(command[0]); b = int(command[2]); step = int(command[1]);
                else:
                    a = int(command[0]); b = int(command[1]); step = 1
                command = list(np.arange(a,b,step))
                command.append(b)
            except:
                self.nodeErrorLabel.config(fg='red',text = "Error: Invalid syntax for deletenode")
                self.nodePage.after(2500,self.wipeErrorLabels)
                return

        errorList = list()
        for num in command:
            self.nodeDelEntry.delete(0,END); self.nodeDelEntry.insert(0,num)
            self.deleteNode()
            if self.nodeErrorLabel.cget("text") != "":
                self.nodeErrorLabel.config(text = "")
                errorList.append(num)
        if len(errorList) > 0:
            self.nodeErrorLabel.config(fg="red",text = "Errors deleting nodes: " + str(errorList))
        return

    def commandNewLink(self,command):
        self.notebook.select(self.linkPage)
        if len(command) > 4:
            self.linkErrorLabel.config(text="Error: Command sequence too long")
            self.linkPage.after(2500,self.wipeErrorLabels)
            return
        while len(command) < 4:
            command.append("")
        if command[0] == "":
            if self._Links:
                command[0] = str(max(self._Links)+1)
            else:
                command[0] = 0
        if command[3] == "":
            command[3] = 0 # set the material as 0 by default

        self.linkNumEntry.delete(0,END); self.linkNumEntry.insert(0,command[0])
        self.linkNode1Entry.delete(0,END); self.linkNode1Entry.insert(0,command[1])
        self.linkNode2Entry.delete(0,END); self.linkNode2Entry.insert(0,command[2])
        self.linkMatEntry.delete(0,END); self.linkMatEntry.insert(0,command[3])
        self.newLink()
        return

    def commandDeleteLink(self,command):
        self.notebook.select(self.linkPage)

        # parse a:b or a:step:b to list
        if len(command) == 1 and ":" in command[0]:
            command = [x.strip() for x in command[0].split(':')]
            try:
                if len(command) == 3:
                    a = int(command[0]); b = int(command[2]); step = int(command[1]);
                else:
                    a = int(command[0]); b = int(command[1]); step = 1
                command = list(np.arange(a,b,step))
                command.append(b)
            except:
                self.linkErrorLabel.config(fg='red',text = "Error: Invalid syntax for deletelink")
                self.linkPage.after(2500,self.wipeErrorLabels)
                return

        errorList = list()
        for num in command:
            self.linkDelEntry.delete(0,END); self.linkDelEntry.insert(0,num)
            self.deleteLink()
            if self.linkErrorLabel.cget("text") != "":
                self.linkErrorLabel.config(text = "")
                errorList.append(num)
        if len(errorList) > 0:
            self.linkErrorLabel.config(fg="red",text = "Errors deleting links: " + str(errorList))
        return

    def commandAddConstraint(self,command):
        self.notebook.select(self.constrainPage)
        if len(command) > 1+self.dimensions:
            self.conErrorLabel.config(text="Error: Command sequence too long")
            self.constrainPage.after(2500,self.wipeErrorLabels)
        while len(command) < 1+self.dimensions:
            command.append("")
        self.conNumEntry.delete(0,END); self.conNumEntry.insert(0,command[0])
        self.conXEntry.delete(0,END); self.conXEntry.insert(0,command[1])
        self.conYEntry.delete(0,END); self.conYEntry.insert(0,command[2])
        if self.dimensions == 3:
            self.conZEntry.delete(0,END); self.conZEntry.insert(0,command[3])
        self.addConstraint()
        return

    def commandDeleteConstraint(self,command):
        self.notebook.select(self.constrainPage)

        # parse a:b or a:step:b to list
        if len(command) == 1 and ":" in command[0]:
            command = [x.strip() for x in command[0].split(':')]
            try:
                if len(command) == 3:
                    a = int(command[0]); b = int(command[2]); step = int(command[1]);
                else:
                    a = int(command[0]); b = int(command[1]); step = 1
                command = list(np.arange(a,b,step))
                command.append(b)
            except:
                self.conErrorLabel.config(fg='red',text = "Error: Invalid syntax for deleteconstraint")
                self.constrainPage.after(2500,self.wipeErrorLabels)
                return

        errorList = list()
        for num in command:
            self.conDelEntry.delete(0,END); self.conDelEntry.insert(0,num)
            self.deleteConstraint()
            if self.conErrorLabel.cget("text") != "":
                self.conErrorLabel.config(text = "")
                errorList.append(num)
        if len(errorList) > 0:
            self.conErrorLabel.config(fg="red",text = "Errors deleting constraints on nodes: " + str(errorList))
        return

    def commandAddForce(self,command):
        self.notebook.select(self.forcePage)
        if len(command) > 1+self.dimensions:
            self.forceErrorLabel.config(text="Error: Command sequence too long")
            self.forcePage.after(2500,self.wipeErrorLabels)
        while len(command) < 1+self.dimensions:
            command.append("")
        self.forceNumEntry.delete(0,END); self.forceNumEntry.insert(0,command[0])
        self.forceXEntry.delete(0,END); self.forceXEntry.insert(0,command[1])
        self.forceYEntry.delete(0,END); self.forceYEntry.insert(0,command[2])
        if self.dimensions == 3:
            self.forceZEntry.delete(0,END); self.forceZEntry.insert(0,command[3])
        self.addForce()
        return

    def commandDeleteForce(self,command):
        self.notebook.select(self.forcePage)

        # parse a:b or a:step:b to list
        if len(command) == 1 and ":" in command[0]:
            command = [x.strip() for x in command[0].split(':')]
            try:
                if len(command) == 3:
                    a = int(command[0]); b = int(command[2]); step = int(command[1]);
                else:
                    a = int(command[0]); b = int(command[1]); step = 1
                command = list(np.arange(a,b,step))
                command.append(b)
            except:
                self.forceErrorLabel.config(fg='red',text = "Error: Invalid syntax for deleteforce")
                self.forcePage.after(2500,self.wipeErrorLabels)
                return

        errorList = list()
        for num in command:
            self.forceDelEntry.delete(0,END); self.forceDelEntry.insert(0,num)
            self.deleteForce()
            if self.forceErrorLabel.cget("text") != "":
                self.forceErrorLabel.config(text = "")
                errorList.append(num)
        if len(errorList) > 0:
            self.forceErrorLabel.config(fg="red",text = "Errors deleting forces on nodes: " + str(errorList))
        return

    def commandLinNode(self,command):
        self.notebook.select(self.nodePage)
        if len(command) > 3+2*self.dimensions:
            self.nodeErrorLabel.config(text="Error: Command sequence too long")
            self.nodePage.after(2500,self.wipeErrorLabels)
            return
        while len(command) < 3+2*self.dimensions:
            command.append("")
        if command[2] == "":
            command[2] = "1"

        self.linNodeStartNumEntry.delete(0,END); self.linNodeStartNumEntry.insert(0,command[0])
        self.linNodeNumNodesEntry.delete(0,END); self.linNodeNumNodesEntry.insert(0,command[1])
        self.linNodeSpaceEntry.delete(0,END); self.linNodeSpaceEntry.insert(0,command[2])
        self.linNodeStartXEntry.delete(0,END); self.linNodeStartXEntry.insert(0,command[3])
        self.linNodeEndXEntry.delete(0,END); self.linNodeEndXEntry.insert(0,command[4])
        self.linNodeStartYEntry.delete(0,END); self.linNodeStartYEntry.insert(0,command[5])
        self.linNodeEndYEntry.delete(0,END); self.linNodeEndYEntry.insert(0,command[6])
        if self.dimensions == 3:
            self.linNodeStartZEntry.delete(0,END); self.linNodeStartZEntry.insert(0,command[7])
            self.linNodeEndZEntry.delete(0,END); self.linNodeEndZEntry.insert(0,command[8])

        self.linNode()
        return

    def commandMultiLink(self,command):
        self.notebook.select(self.linkPage)
        if len(command) > 6:
            self.linkErrorLabel.config(text="Error: Command sequence too long")
            self.linkPage.after(2500,self.wipeErrorLabels)
            return
        while len(command) < 6:
            command.append("")

        # set defaulst for spacings and material
        if command[3] == "":
            command[3] = 0
        if command[4] == "":
            command[4] = 1
        if command[5] == "":
            command[5] = 1

        self.multiLinkStartLinkEntry.delete(0,END); self.multiLinkStartLinkEntry.insert(0,command[0])
        self.multiLinkStartNodeEntry.delete(0,END); self.multiLinkStartNodeEntry.insert(0,command[1])
        self.multiLinkEndNodeEntry.delete(0,END); self.multiLinkEndNodeEntry.insert(0,command[2])
        self.multiLinkMatEntry.delete(0,END); self.multiLinkMatEntry.insert(0,command[3])
        self.multiLinkNodeSpaceEntry.delete(0,END); self.multiLinkNodeSpaceEntry.insert(0,command[4])
        self.multiLinkSpaceEntry.delete(0,END); self.multiLinkSpaceEntry.insert(0,command[5])

        self.multiLink()
        return

    def commandSolve(self):
        self.notebook.select(self.solutionPage)
        self.solve()

#---Material---
    def newMaterial(self,event=None):
        # Check that number is an integer
        try:
            num = int(self.matNumEntry.get())
        except:
            self.matErrorLabel.config(text="Error: Material number must be an integer")
            self.materialPage.after(2500,self.wipeErrorLabels)
            return

        # check that other entries
        try:
            E = float(self.matModEntry.get())
            A = float(self.matAreaEntry.get())
            D = self.matDensityEntry.get()
            if D == "":
                D = 0
            else:
                D = float(D)
        except:
            self.matErrorLabel.config(text="Error: Invalid entry or entries")
            self.materialPage.after(2500,self.wipeErrorLabels)
            return

        # check input physical validity
        if E <= 0:
            self.matErrorLabel.config(text="Error: Young's Modulus must be positive")
            self.materialPage.after(2500,self.wipeErrorLabels)
            return
        if A <= 0:
            self.matErrorLabel.config(text="Error: Area must be positive")
            self.materialPage.after(2500,self.wipeErrorLabels)
            return

       # check if material number already exists
        if num in self._Materials:
            self.matErrorLabel.config(fg = "orange",text="Warning: Replacing existing material")
            self.materialPage.after(2500,self.wipeErrorLabels)
            self._Materials[num] = FEALinkMaterial.Material(num,E,A,D)
            for linkNum,link in self._Links.items():
                if link.material.number == num:
                    self._Links[linkNum] = FEALinkLink.Link(linkNum,link.node1,link.node2,self._Materials[num])
        else:
            self._Materials[num] = FEALinkMaterial.Material(num,E,A,D)
        self.updateMaterialList()
        # increment material number entry box for convenience
        self.matNumEntry.delete(0,END)
        self.matNumEntry.insert(0,str(num+1))
        return

    def deleteMaterial(self,event=None):
        try:
            num = int(self.matDelEntry.get())
        except:
            self.matErrorLabel.config(text="Error: Material number must be an integer")
            self.materialPage.after(2500,self.wipeErrorLabels)
            return

        if num in self._Materials:
            # check if material is associated to any links
            for linkNum,link in self._Links.items():
                if link.material == self._Materials[num]:
                    self.matErrorLabel.config(text="Error: Material is used in link - cannot delete")
                    self.materialPage.after(2500,self.wipeErrorLabels)
                    return
            del self._Materials[num]
            self.updateMaterialList()
        else:
            self.matErrorLabel.config(fg="blue",text="Note: Material number does not exist to delete")
            self.materialPage.after(2500,self.wipeErrorLabels)
        return

    def updateMaterialList(self):
        self.matListTree.delete(*self.matListTree.get_children())
        for num,m in self._Materials.items():
            if m.density == 0:
                self.matListTree.insert("",'end',text=str(num),values=(m.area,m.modulus,""))
            else:
                self.matListTree.insert("",'end',text=str(num),values=(m.area,m.modulus,m.density))
        return

#---Node---
    def newNode(self,event=None):
        # get number of new node
        try:
            num = int(self.nodeNumEntry.get())
        except:
            self.nodeErrorLabel.config(text="Error: Node number must be an integer")
            self.nodePage.after(2500,self.wipeErrorLabels)
            return
        # get x,y,z coordinates
        try:
            X = float(self.nodeXEntry.get())
            Y = float(self.nodeYEntry.get())
            if self.dimensions == 3:
                Z = float(self.nodeZEntry.get())
            else:
                Z = None
        except:
            self.nodeErrorLabel.config(text="Error: Invalid entry or entries")
            self.nodePage.after(2500,self.wipeErrorLabels)
            return
        
        # check if there is already a node in that location
        if self.dimensions == 2:
            for n,node in self._Nodes.items():
                if node.x == X and node.y == Y:
                    self.nodeErrorLabel.config(text="Error: Node exists in that location")
                    self.nodePage.after(2500,self.wipeErrorLabels)
                    return
        else:
            for n,node in self._Nodes.items():
                if node.z == Z and node.y == Y and node.x == X:
                    self.nodeErrorLabel.config(text="Error: Node exists in that location")
                    self.nodePage.after(2500,self.wipeErrorLabels)
                    return

        # check if node exists and replace
        if num in self._Nodes:
            self.nodeErrorLabel.config(text="Warning: Replacing existing node",fg="orange")
            self.nodePage.after(2500,self.wipeErrorLabels)
            self._Nodes[num].x = X
            self._Nodes[num].y = Y
            if self.dimensions == 3:
                self._Nodes[num].z = Z
            thisNode = self._Nodes[num]
            for linkNum,link in self._Links.items():
                if link.node1.number == num:
                    otherNode = link.node2
                    self._Links[linkNum] = FEALinkLink.Link(linkNum,thisNode,otherNode,link.material)
                elif link.node2.number == num:
                    otherNode = link.node1
                    self._Links[linkNum] = FEALinkLink.Link(linkNum,otherNode,thisNode,link.material)
        else:
            self._Nodes[num] = FEALinkNode.Node(num,X,Y,Z)
        self.updateNodeList()

        # update scope to include the new node
        self._Scope.expandScope(self._Nodes[num])

        # update plot
        self.updatePlot()
        # increment node number entry box for convenience
        self.nodeNumEntry.delete(0,END)
        self.nodeNumEntry.insert(0,str(num+1))
        return

    def deleteNode(self,event=None):
        try:
            num = int(self.nodeDelEntry.get())
        except:
            self.nodeErrorLabel.config(text="Error: Node number must be an integer")
            self.nodePage.after(2500,self.wipeErrorLabels)
            return

        if num in self._Nodes:
            if self._Nodes[num].isLinked():
                self.nodeErrorLabel.config(text="Error: Cannot delete linked node")
                self.nodePage.after(2500,self.wipeErrorLabels)
                return
            else:
                del self._Nodes[num]
                self.updateNodeList()
        else:
            self.nodeErrorLabel.config(fg="blue",text="Note: Node number does not exist to delete")
            self.nodePage.after(2500,self.wipeErrorLabels)
            return

        # update problem scope
        self._Scope.updateScope(self._Nodes)

        # update constraint tree
        self.updateConstraintList()

        # update plot
        self.updatePlot()
        return

    def linNode(self,event=None):
        # get node number data
        try:
            startNum = self.linNodeStartNumEntry.get()
            if startNum == "":
                if len(self._Nodes) == 0:
                    startNum = 0
                else:
                    startNum = max(self._Nodes) + 1
            else:
                startNum = int(startNum)
            numNodes = int(self.linNodeNumNodesEntry.get())
            spacing = int(self.linNodeSpaceEntry.get())
        except:
            self.nodeErrorLabel.config(text="MultiNode Error: Node numbers must be integers",fg="red")
            self.nodePage.after(2500,self.wipeErrorLabels)
            return

        nodeNums = [(startNum+i*spacing) for i in range(0,numNodes)]

        # check if any of the node numbers exist
        if any(num in nodeNums for num in self._Nodes):
            self.nodeErrorLabel.config(text="MultiNode Error: One or more nodes already exist",fg="red")
            self.nodePage.after(2500,self.wipeErrorLabels)
            return

        # get node position data
        xEnd = self.linNodeEndXEntry.get()
        yEnd = self.linNodeEndYEntry.get()
        if self.dimensions == 3:
            zEnd = self.linNodeEndZEntry.get()

        try:
            xStart = float(self.linNodeStartXEntry.get())
            if xEnd == "": 
                xEnd = xStart
            else:
                xEnd = float(xEnd)
            yStart = float(self.linNodeStartYEntry.get())
            if yEnd == "": 
                yEnd = yStart
            else:
                yEnd = float(yEnd)
            if self.dimensions == 3:
                zStart = float(self.linNodeStartZEntry.get())
                if zEnd == "":
                    zEnd = zStart
                else:
                    zEnd = float(zEnd)
        except:
            self.nodeErrorLabel.config(text="MultiNode Error: Node positions are not valid numbers")
            self.nodePage.after(2500,wipeErrorLabels)
            return

        x = np.linspace(xStart,xEnd,numNodes)
        y = np.linspace(yStart,yEnd,numNodes)
        if self.dimensions == 3:
            z = np.linspace(zStart,zEnd,numNodes)

        # check for nodes in positions
        if self.dimensions == 2:
            for i in range(0,numNodes):
                for n,node in self._Nodes.items():
                    if node.x == x[i] and node.y == y[i]:
                        self.nodeErrorLabel.config(text="MultiNode Error: Node overlaps existing node location")
                        self.nodePage.after(2500,self.wipeErrorLabels)
                        return
        else:
            for i in range(0,numNodes):
                for n,node in self._Nodes.items():
                    if node.z == z[i] and node.y == y[i] and node.x == x[i]:
                        self.nodeErrorLabel.config(text="MultiNode Error: Node overlaps existing node location")
                        self.nodePage.after(2500,self.wipeErrorLabels)
                        return

        # create the nodes
        if self.dimensions == 2:
            for i in range(0,numNodes):
                num = nodeNums[i]
                self._Nodes[num] = (FEALinkNode.Node(num,x[i],y[i]))
                self._Scope.expandScope(self._Nodes[num])
        else:
            for i in range(0,numNodes):
                num = nodeNums[i]
                self._Nodes[num] = (FEALinkNode.Node(num,x[i],y[i],z[i]))
                self._Scope.expandScope(self._Nodes[num])

        self.updateNodeList()
        self.updatePlot()

        return

    def updateNodeList(self):
        self.nodeListTree.delete(*self.nodeListTree.get_children())
        if self.dimensions == 3:
            for num,n in self._Nodes.items():
                self.nodeListTree.insert("",'end',text=str(num),values=(n.x,n.y,n.z))
        else:
            for num,n in self._Nodes.items():
                self.nodeListTree.insert("",'end',text=str(num),values=(n.x,n.y,0))
        return

#---Link---
    def newLink(self,event=None):
        # get number of new link
        try:
            num = int(self.linkNumEntry.get())
        except:
            self.linkErrorLabel.config(text="Error: Link number must be an integer")
            self.linkPage.after(2500,self.wipeErrorLabels)
            return
        # get nodes and material
        try:
            node1 = self._Nodes[int(self.linkNode1Entry.get())]
            node2 = self._Nodes[int(self.linkNode2Entry.get())]
        except:
            self.linkErrorLabel.config(text="Error: Invalid node number")
            self.linkPage.after(2500,self.wipeErrorLabels)
            return

        # check if connecting a node to itself
        if node1 == node2:
            self.linkErrorLabel.config(text="Error: Cannot link node to itself")
            self.linkPage.after(2500,self.wipeErrorLabels)
            return

        try:
            matNum = self.linkMatEntry.get()
            if matNum == "":
                matNum = 0
            else:
                matNum = int(matNum)
            material = self._Materials[int(matNum)]
        except:
            self.linkErrorLabel.config(text="Error: Invalid material")
            self.linkPage.after(2500,self.wipeErrorLabels)
            return

        # check if link exists and add it if it does not
        if num in self._Links:
            self.linkErrorLabel.config(text="Error: Link number already exists")
            self.linkPage.after(2500,self.wipeErrorLabels)
            return
        else:
            if node1.linkToNode(node2.number): # returns false if nodes already linked
                node2.linkToNode(node1.number)
                self._Links[num] = FEALinkLink.Link(num,node1,node2,material)
                self.updateLinkList()
            else:
                self.linkErrorLabel.config(text="Error: Nodes already linked")
                self.linkPage.after(2500,self.wipeErrorLabels)
                return

        # update plot
        self.updatePlot()
        # increment link number entry box for convenience
        self.linkNumEntry.delete(0,END)
        self.linkNumEntry.insert(0,str(num+1))
        return

    def deleteLink(self,event=None):
        # get number of link to delete
        try:
            num = int(self.linkDelEntry.get())
        except:
            self.linkErrorLabel.config(text="Error: Link number must be an integer")
            self.linkPage.after(2500,self.wipeErrorLabels)
            return

        # delete link
        if num in self._Links:
            link = self._Links[num]
            link.node1.disconnectFromNode(link.node2.number)
            link.node2.disconnectFromNode(link.node1.number)
            del self._Links[num]
            self.updateLinkList()
        else:
            self.linkErrorLabel.config(fg="blue",text="Note: Link number does not exist to delete")
            self.linkPage.after(2500,self.wipeErrorLabels)

        # update plot
        self.updatePlot()
        return

    def multiLink(self,event=None):
        if len(self._Nodes) == 0:
            self.linkErrorLabel.config(text="MultiLink Error: No nodes exist")
            self.linkPage.after(2500,self.wipeErrorLabels)
            return

        # get nodal boundaries
        try:
            lower = self.multiLinkStartNodeEntry.get()
            if lower == "":
                lower = 0
            else:
                lower = int(lower)

            upper = self.multiLinkEndNodeEntry.get()
            if upper == "":
                upper = max(self._Nodes)
            else:
                upper = int(upper)

            nodeSpacing = self.multiLinkNodeSpaceEntry.get()
            if nodeSpacing == "":
                nodeSpacing = 1
            elif nodeSpacing == "0":
                self.linkErrorLabel.config(text="MultiLink Error: Node Spacing must be non-zero")
                self.linkPage.after(2500,self.wipeErrorLabels)
                return
            else:
                nodeSpacing = int(nodeSpacing)
        except:
            self.linkErrorLabel.config(text="MultiLink Error: Node boundaries and spacing must be integers or blank")
            self.linkPage.after(2500,self.wipeErrorLabels)
            return

        # get link number specifications
        try:
            mat = self.multiLinkMatEntry.get()
            if mat == "":
                mat = 0
            else:
                mat = int(mat)

            linkStartNum = self.multiLinkStartLinkEntry.get()
            if linkStartNum == "":
                if len(self._Links) == 0:
                    linkStartNum = 0
                else:
                    linkStartNum = max(self._Links)+1
            else:
                linkStartNum = int(linkStartNum)
            linkSpacing = int(self.multiLinkSpaceEntry.get())
        except:
            self.linkErrorLabel.config(text="MultiLinkError: Link and Material numbers must be integers")
            self.linkPage.after(2500,self.wipeErrorLabels)
            return

        # check material
        try:
            mat = self._Materials[mat]
        except:
            self.linkErrorLabel.config(text="MultiLink Error: Invalid material number")
            self.linkPage.after(2500,wipeErrorLabels)
            return

        # make links (but don't include them in list of links yet, in case we run into an error)
        linkNum = linkStartNum
        newLinks = dict()
        for nodeNum in range(lower,(upper+1)-nodeSpacing):
            if nodeNum in self._Nodes and nodeNum+nodeSpacing in self._Nodes:
                node1 = self._Nodes[nodeNum]
                node2 = self._Nodes[nodeNum+nodeSpacing]
                if node2.number not in node1.linkedNodes:
                    if linkNum in self._Links:
                        self.linkErrorLabel.config(text="MultiLink Error: Link number to be created already exists")
                        self.linkPage.after(2500,self.wipeErrorLabels)
                        return
                    newLinks[linkNum] = FEALinkLink.Link(linkNum,node1,node2,mat)
                    linkNum = linkNum + linkSpacing

        # link nodes
        for num,link in newLinks.items():
            self._Links[num] = link
            link.node1.linkToNode(link.node2.number)
            link.node2.linkToNode(link.node1.number)
        
        self.updatePlot()
        self.updateLinkList()
        return

    def updateLinkList(self):
        self.linkListTree.delete(*self.linkListTree.get_children())
        for num,l in self._Links.items():
            self.linkListTree.insert("",'end',text=num,values=(l.node1.number,l.node2.number,l.material.number,l.length))
        return

#---Constraint---
    def addConstraint(self,event=None):
        # get node number
        try:
            num = int(self.conNumEntry.get())
        except:
            self.conErrorLabel.config(text="Error: Node number must be an integer")
            self.constrainPage.after(2500,self.wipeErrorLabels)
            return

        # get constraints
        xcon = self.conXEntry.get()
        if xcon == "":
            xcon = None
        else:
            try:
                xcon = float(xcon)
            except:
                self.conErrorLabel.config(text="Error: Invalid x constraint")
                self.constrainPage.after(2500,self.wipeErrorLabels)

        ycon = self.conYEntry.get()
        if ycon == "":
            ycon = None
        else:
            try:
                ycon = float(ycon)
            except:
                self.conErrorLabel.config(text="Error: Invalid y constraint")
                self.constrainPage.after(2500,self.wipeErrorLabels)

        if self.dimensions == 3:
            zcon = self.conZEntry.get()
            if zcon == "":
                zcon = None
            else:
                try:
                    zcon = float(zcon)
                except:
                    self.conErrorLabel.config(text="Error: Invalid z constraint")
                    self.constrainPage.after(2500,self.wipeErrorLabels)

        # add the constraints to the relevant node
        if num in self._Nodes:
            # check existing constraints
            if self._Nodes[num].isConstrained():
                self.conErrorLabel.config(fg="orange",text="Warning: Replacing existing constraint(s)")
                self.constrainPage.after(2500,self.wipeErrorLabels)

            # add constraints to node
            if self.dimensions == 2:
                self._Nodes[num].addConstraints(xcon,ycon)
            else:
                self._Nodes[num].addConstraints(xcon,ycon,zcon)
        else:
            self.conErrorLabel.config(text="Error: Node number not defined")
            self.constrainPage.after(2500,self.wipeErrorLabels)
            return

        # Update constraint treeview
        self.updateConstraintList()

        # Update plot
        self.updatePlot()
        return

    def deleteConstraint(self,event=None):
        # get node number
        try:
            num = int(self.conDelEntry.get())
        except:
            self.conErrorLabel.config(text="Error: Node number must be an integer")
            self.constrainPage.after(2500,self.wipeErrorLabels)
            return

        # Delete constraints at node
        if num in self._Nodes:
            if self._Nodes[num].isConstrained():
                self._Nodes[num].deleteConstraints()
            else:
                self.conErrorLabel.config(fg="blue",text="Note: No constraints at node to delete")
                self.constrainPage.after(2500,self.wipeErrorLabels)
                return
        else:
            self.conErrorLabel.config(text="Error: Node number not defined")
            self.constrainPage.after(2500,self.wipeErrorLabels)
            return

        # Update constraint treeview
        self.updateConstraintList()

        # Update Plot
        self.updatePlot()
        return

    def updateConstraintList(self):
        self.conListTree.delete(*self.conListTree.get_children())
        if self.dimensions == 2:
            for num,n in self._Nodes.items():
                if n.isConstrained():
                    self.conListTree.insert("",'end',text=num,values=(n.xconstrain,n.yconstrain,None))
        else:
            for num,n in self._Nodes.items():
                if n.isConstrained():
                    self.conListTree.insert("",'end',text=num,values=(n.xconstrain,n.yconstrain,n.zconstrain))
        return

#---Force---
    def addForce(self,event=None):
        # get node number
        try:
            num = int(self.forceNumEntry.get())
        except:
            self.forceErrorLabel.config(text="Error: Node number must be an integer")
            self.forcePage.after(2500,self.wipeErrorLabels)
            return

        # get force values
        x = self.forceXEntry.get()
        if x == "":
            x = 0
        else:
            try:
                x = float(x)
            except:
                self.forceErrorLabel.config(text="Error: Invalid x force")
                self.forcePage.after(2500,self.wipeErrorLabels)

        y = self.forceYEntry.get()
        if y == "":
            y = 0
        else:
            try:
                y = float(y)
            except:
                self.forceErrorLabel.config(text="Error: Invalid y force")
                self.forcePage.after(2500,self.wipeErrorLabels)

        if self.dimensions == 3:
            z = self.forceZEntry.get()
            if z == "":
                z = 0
            else:
                try:
                    z = float(z)
                except:
                    self.forceErrorLabel.config(text="Error: Invalid z force")
                    self.forcePage.after(2500,self.wipeErrorLabels)

        # add the forces to the relevant node
        if num in self._Nodes:
            # check existing forces
            if self._Nodes[num].hasForce():
                self.forceErrorLabel.config(fg="orange",text="Warning: Replacing existing force(s)")
                self.forcePage.after(2500,self.wipeErrorLabels)

            # add forces to node
            if self.dimensions == 2:
                self._Nodes[num].addForce(x,y)
            else:
                self._Nodes[num].addForce(x,y,z)
        else:
            self.forceErrorLabel.config(text="Error: Node number not defined")
            self.forcePage.after(2500,self.wipeErrorLabels)
            return

        # Update force treeview
        self.updateForceList()

        # Update plot
        self.updatePlot()
        return

    def deleteForce(self,event=None):
        # get node number
        try:
            num = int(self.forceDelEntry.get())
        except:
            self.forceErrorLabel.config(text="Error: Node number must be an integer")
            self.forcePage.after(2500,self.wipeErrorLabels)
            return

        if num in self._Nodes:
            if self._Nodes[num].hasForce():
                self._Nodes[num].deleteForce()
            else:
                self.forceErrorLabel.config(fg="blue",text="Note: No forces at node to delete")
                self.forcePage.after(2500,self.wipeErrorLabels)
                return
        else:
            self.forceErrorLabel.config(text="Error: Node number not defined")
            self.forcePage.after(2500,self.wipeErrorLabels)
            return

        # Update force treeview
        self.updateForceList()

        # Update plot
        self.updatePlot()
        return

    def updateForceList(self):
        self.forceListTree.delete(*self.forceListTree.get_children())
        if self.dimensions == 2:
            for num,n in self._Nodes.items():
                if n.hasForce():
                    self.forceListTree.insert("",'end',text=num,values=(n.xforce,n.yforce,None))
        else:
            for num,n in self._Nodes.items():
                if n.hasForce():
                    self.forceListTree.insert("",'end',text=num,values=(n.xforce,n.yforce,n.zforce))
        return

    def getMaxForce(self):
        maxForce=0;
        for num,node in self._Nodes.items():
            maxForce = max(maxForce,node.forceMagnitude())
        return maxForce

#---Solution---
    def solve(self,event=None):
        self._Solution = None

        self.solErrorLabel.config(text="Solving...",fg="green")
        self._Solution = FEALinkSolution.Solution(self)
        try:
            message = self._Solution.solve()
            if message == "Success":
                self.solErrorLabel.config(text="Solution Completed",fg="green")
                self.solutionPage.after(2500,self.wipeErrorLabels)
                self.updateSolutionNotebook()
                self.plotExagCheck.config(state=NORMAL)
                self.plotResultCheck.config(state=NORMAL)
                self.showStressCheck.config(state=NORMAL)
            else:
                self._Solution = None
                self.solErrorLabel.config(text=message,fg="red")
                self.solErrorLabel.after(2500,self.wipeErrorLabels)
                self.wipeSolutionNotebook()
        except:
            self._Solution = None
            self.solErrorLabel.config(text="Solve Failed",fg="red")
            self.solutionPage.after(2500,self.wipeErrorLabels)
            self.wipeSolutionNotebook()
        return

    def updateSolutionNotebook(self):
        self.nodalListTree.delete(*self.nodalListTree.get_children())
        self.reactListTree.delete(*self.reactListTree.get_children())
        if self.dimensions == 2:
            for num,n in self._Solution._SolNodes.items():
                self.nodalListTree.insert("",'end',text=num,values=('%.9g' % n.displacement[0],'%.9g' % n.displacement[1]))
                self.reactListTree.insert("",'end',text=num,values=('%.9g' % n.reaction[0],'%.9g' % n.reaction[1]))
        else:
            for num,n in self._Solution._SolNodes.items():
                self.nodalListTree.insert("",'end',text=num,values=('%.8g' % n.displacement[0],'%.8g' % n.displacement[1],'%.8g' % n.displacement[2]))
                self.reactListTree.insert("",'end',text=num,values=('%.8g' % n.reaction[0],'%.8g' % n.reaction[1],'%.8g' % n.reaction[2]))

        self.ssListTree.delete(*self.ssListTree.get_children())
        for num,link in self._Solution._SolLinks.items():
            self.ssListTree.insert("",'end',text=num,values=('%.8g' % link.tension,'%.8g' % link.stress,'%.8g' %link.strain))

        self.massListTree.delete(*self.massListTree.get_children())
        if self._Solution.totalMass == 0:
            self.massListTree.insert("",'end',text="Total",values=('%.8g' % self._Solution.totalLength, ""))
        else:
            self.massListTree.insert("",'end',text="Total",values=('%.8g' % self._Solution.totalLength, '%.8g' % self._Solution.totalMass))
        for num,materialMass in self._Solution._Mass.items():
            if materialMass == 0:
                self.massListTree.insert("",'end',text=num,values=('%.8g' % self._Solution._Length[num],""))
            else:
                self.massListTree.insert("",'end',text=num,values=('%.8g' % self._Solution._Length[num],'%.8g' % self._Solution._Mass[num]))
        return

    def wipeSolutionNotebook(self):
        self.nodalListTree.delete(*self.nodalListTree.get_children())
        self.reactListTree.delete(*self.reactListTree.get_children())
        self.ssListTree.delete(*self.ssListTree.get_children())
        self.massListTree.delete(*self.massListTree.get_children())
        return


##################  GUI Creation Methods ##################
#---Root Level---
    def bringToFront(self):
        self.root.lift()
        self.root.attributes('-topmost',1)
        self.root.after_idle(self.root.attributes,'-topmost',0)
        return

    def makePlot(self):
        self.fig = Figure(figsize=(3,3),dpi=100)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.show()
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self.root)
        self.toolbar.update() 

        self.canvas.get_tk_widget().pack(side=RIGHT,expand=1,fill=BOTH)  
        self.canvas._tkcanvas.pack(side=BOTTOM)

        #self.canvas.mpl_connect('key_press_event', self.on_key_event)

        if self.dimensions == 2:
            self.display = self.fig.add_subplot(111)
            self.display.plot([],[])
            self.display.set_xlabel('x')
            self.display.set_ylabel('y')
        else:
            self.display = self.fig.add_subplot(111,projection='3d')
            self.display.plot([],[],[])
            self.display.set_xlabel('x')
            self.display.set_ylabel('y')
            self.display.set_zlabel('z')

        self.updatePlot()
        return

    def makeInterface(self):
        # make menu bar
        self.menu = Menu(self.root)
        self.fileMenu = Menu(self.menu,tearoff = 0)
        self.fileMenu.add_command(label="Load Model",command=self.load)
        self.fileMenu.add_command(label="Save Model",command=self.save)
        self.fileMenu.add_command(label="SaveAs",command=self.saveAs)
        self.menu.add_cascade(label="File", menu=self.fileMenu)
        self.root.config(menu=self.menu)

        # make command frame
        self.commandFrame = Frame(self.root)
        self.commandFrame.pack(side=TOP,fill=X)
        self.commandFrame.bind('<Return>',self.executeCommand)

        # saving
        self.saveBtn = Button(self.commandFrame,text="Save Model",command = self.save)
        self.saveBtn.pack(side=RIGHT)

        # make check boxes for displaying numbers
        self.nodeNumbers = BooleanVar()
        self.linkNumbers = BooleanVar()
        self.showConstraints = BooleanVar()
        self.showForces = BooleanVar()
        self.nodeNumCheck = Checkbutton(self.commandFrame,text="Node Numbers",variable=self.nodeNumbers,command=self.updatePlot)
        self.nodeNumCheck.select()
        self.nodeNumCheck.pack(side=RIGHT)
        self.linkNumCheck = Checkbutton(self.commandFrame,text="Link Numbers",variable=self.linkNumbers,command=self.updatePlot)
        self.linkNumCheck.select()
        self.linkNumCheck.pack(side=RIGHT)
        self.constraintCheck = Checkbutton(self.commandFrame,text="Show Constraints",variable=self.showConstraints,command=self.updatePlot)
        self.constraintCheck.select()
        self.constraintCheck.pack(side=RIGHT)
        self.forceCheck = Checkbutton(self.commandFrame,text="Show Forces",variable=self.showForces,command=self.updatePlot)
        self.forceCheck.select()
        self.forceCheck.pack(side=RIGHT)

        # make command line
        self.commandBtn = Button(self.commandFrame,text="Execute Command",command=self.executeCommand)
        self.commandBtn.pack(side=RIGHT)
        self.commandLine = Entry(self.commandFrame)
        self.commandLine.pack(side=LEFT,fill=X,expand=1)
        self.commandLine.bind('<Return>',self.executeCommand)
        self.commandLine.bind('<Up>',self.upCommand)
        self.commandLine.bind('<Down>',self.downCommand)

        # make Notebook widget
        self.notebook = ttk.Notebook(self.root,name="actions",width=500,height=500)
        self.notebook.pack(side=LEFT)

        # Notes
        self.notePage = Frame(self.notebook,name="notes")
        self.makeNotePage()
        self.notebook.add(self.notePage,text="Notes")

        # Materials
        self.materialPage = Frame(self.notebook,name="materials")
        self.makeMaterialPage()
        self.notebook.add(self.materialPage,text="Material")

        # Nodes
        self.nodePage = Frame(self.notebook,name="node")
        self.makeNodePage()
        self.notebook.add(self.nodePage,text="Node")

        # Links
        self.linkPage = Frame(self.notebook,name="link")
        self.makeLinkPage()
        self.notebook.add(self.linkPage,text="Link")

        # Constraints
        self.constrainPage = Frame(self.notebook,name="constraints")
        self.makeConstrainPage()
        self.notebook.add(self.constrainPage,text="Constrain")

        # Forces
        self.forcePage = Frame(self.notebook,name="forces")
        self.makeForcePage()
        self.notebook.add(self.forcePage,text="Force")

        # Solve and Results
        self.solutionPage = Frame(self.notebook,name="solution")
        self.makeSolutionPage()
        self.notebook.add(self.solutionPage,text="Solution")
        return

#---Notebook Pages---
    def makeMaterialPage(self):
        # make material creation buttons, labels, and entry boxes
        self.matMakeBtn = Button(self.materialPage,text="Make/Replace Material")
        self.matMakeBtn.grid(row=1,column=1)
        self.matNumLabel = Label(self.materialPage,text="Material #")
        self.matNumLabel.grid(row=2,column=0)
        self.matNumEntry = Entry(self.materialPage)
        self.matNumEntry.grid(row=2,column=1)
        self.matAreaLabel = Label(self.materialPage,text="Area")
        self.matAreaLabel.grid(row=3,column=0)
        self.matAreaEntry = Entry(self.materialPage)
        self.matAreaEntry.grid(row=3,column=1)        
        self.matModLabel = Label(self.materialPage,text="Young's Modulus")
        self.matModLabel.grid(row=4,column=0)
        self.matModEntry = Entry(self.materialPage)
        self.matModEntry.grid(row=4,column=1)
        self.matDensityLabel = Label(self.materialPage,text="Density (optional)")
        self.matDensityLabel.grid(row=5,column=0)
        self.matDensityEntry = Entry(self.materialPage)
        self.matDensityEntry.grid(row=5,column=1)

        self.matNumEntry.bind('<Return>',self.newMaterial)
        self.matAreaEntry.bind('<Return>',self.newMaterial)
        self.matModEntry.bind('<Return>',self.newMaterial)
        self.matDensityEntry.bind('<Return>',self.newMaterial)

        # make material deletion button and entry box
        self.matDelBtn = Button(self.materialPage,text="Delete Material")
        self.matDelBtn.grid(row=1,column=3)
        self.matDelEntry = Entry(self.materialPage)
        self.matDelEntry.grid(row=2,column=3)

        self.matDelEntry.bind('<Return>',self.deleteMaterial)

        # set default entries
        self.matNumEntry.insert(0,'0')

        # set button commands
        self.matMakeBtn.config(command=self.newMaterial)
        self.matDelBtn.config(command=self.deleteMaterial)

        # make error display label
        self.matErrorLabel = Label(self.materialPage,text="",fg="red")
        self.matErrorLabel.grid(row=6,column=0,columnspan=4)

        # make treeview to display materials list
        self.matListTree = ttk.Treeview(self.materialPage,columns=("A","E","D"))
        self.matListTree.grid(row=7,column=0,columnspan=4)
        self.matListTree.column("#0",width=75)
        self.matListTree.heading("#0",text="Material #")
        self.matListTree.column("A",width=135)
        self.matListTree.heading("A",text="Area")
        self.matListTree.column("E",width=135)
        self.matListTree.heading("E",text="Young's Modulus")
        self.matListTree.column("D",width=135)
        self.matListTree.heading("D",text="Density")

        return

    def makeNodePage(self):
        # Make labels for node number, x, y
        self.nodeNumLabel = Label(self.nodePage,text="Node #")
        self.nodeNumLabel.grid(row=1,column=0)
        self.nodeXLabel = Label(self.nodePage,text="x",justify=RIGHT)
        self.nodeXLabel.grid(row=2,column=0)
        self.nodeYLabel = Label(self.nodePage,text="y",justify=RIGHT)
        self.nodeYLabel.grid(row=3,column=0)

        # Make entry boxes for number, x, y
        self.nodeNumEntry = Entry(self.nodePage)
        self.nodeNumEntry.grid(row=1,column=1)
        self.nodeXEntry = Entry(self.nodePage)
        self.nodeXEntry.grid(row=2,column=1)
        self.nodeYEntry = Entry(self.nodePage)
        self.nodeYEntry.grid(row=3,column=1)

        self.nodeNumEntry.bind('<Return>',self.newNode)
        self.nodeXEntry.bind('<Return>',self.newNode)
        self.nodeYEntry.bind('<Return>',self.newNode)

        # Make label and entry box for z if 3D
        if self.dimensions == 3:
            self.nodeZLabel = Label(self.nodePage,text="z",justify=RIGHT)
            self.nodeZLabel.grid(row=4,column=0)
            self.nodeZEntry = Entry(self.nodePage)
            self.nodeZEntry.grid(row=4,column=1)
            self.nodeZEntry.bind('<Return>',self.newNode)

        # Deletion node number Entry box
        self.nodeDelEntry = Entry(self.nodePage)
        self.nodeDelEntry.grid(row=1,column=2)
        self.nodeDelEntry.bind('<Return>',self.deleteNode)

        # set default entries
        self.nodeNumEntry.insert(0,'0')
        self.nodeXEntry.insert(0,'0')
        self.nodeYEntry.insert(0,'0')
        if self.dimensions == 3:
            self.nodeZEntry.insert(0,'0')

        # Create and Delete buttons
        self.nodeMakeBtn = Button(self.nodePage,text="New/Move Node")
        self.nodeMakeBtn.config(command=self.newNode)
        self.nodeMakeBtn.grid(row=0,column=1)
        self.nodeDelBtn = Button(self.nodePage,text="Delete Node")
        self.nodeDelBtn.config(command=self.deleteNode)
        self.nodeDelBtn.grid(row=0,column=2)

        # create error label
        self.nodeErrorLabel = Label(self.nodePage,text="",fg="red")
        self.nodeErrorLabel.grid(row=5,column=0,columnspan=4)

        # Create node list
        if self.dimensions == 2:
            self.nodeListTree = ttk.Treeview(self.nodePage,columns=("X","Y"))
        else:
            self.nodeListTree = ttk.Treeview(self.nodePage,columns=("X","Y","Z"))
        self.nodeListTree.grid(row=6,column=0,columnspan=4)
        self.nodeListTree.column("#0",width=120)
        self.nodeListTree.heading("#0",text="Node #")
        self.nodeListTree.column("X",width=120)
        self.nodeListTree.heading("X",text="X")
        self.nodeListTree.column("Y",width=120)
        self.nodeListTree.heading("Y",text="Y")
        if self.dimensions == 3:
            self.nodeListTree.column("Z",width=120)
            self.nodeListTree.heading("Z",text="Z")

        # Make LinNode area
        self.linNodeFrame = Frame(self.nodePage,relief = SUNKEN,borderwidth=1)
        self.linNodeFrame.grid(row=7,column=0,columnspan=4,sticky=W+E+N+S)

        self.linNodeLabel = Label(self.linNodeFrame,text="MultiNode Tool",fg="blue",justify=LEFT)
        self.linNodeLabel.grid(row=0,column=0)

        self.linNodeBtn = Button(self.linNodeFrame,text="Make Nodes",command = self.linNode)
        self.linNodeBtn.grid(row=0,column=3,columnspan=2)

        self.linNodeStartNumLabel = Label(self.linNodeFrame,text="First Node #",justify=RIGHT)
        self.linNodeNumNodesLabel = Label(self.linNodeFrame,text="# of Nodes",justify=RIGHT)
        self.linNodeSpaceLabel = Label(self.linNodeFrame,text="Node # Spacing",justify=RIGHT)
        self.linNodeStartNumEntry = Entry(self.linNodeFrame,width=4)
        self.linNodeNumNodesEntry = Entry(self.linNodeFrame,width=4)
        self.linNodeSpaceEntry = Entry(self.linNodeFrame,width=4)
        self.linNodeStartNumLabel.grid(row=2,column=0)
        self.linNodeNumNodesLabel.grid(row=3,column=0)
        self.linNodeSpaceLabel.grid(row=4,column=0)
        self.linNodeStartNumEntry.grid(row=2,column=1)
        self.linNodeNumNodesEntry.grid(row=3,column=1)
        self.linNodeSpaceEntry.grid(row=4,column=1)
        self.linNodeSpaceEntry.insert(0,'1')


        self.linNodeStartXLabel = Label(self.linNodeFrame,text="Start X",justify=RIGHT)
        self.linNodeEndXLabel = Label(self.linNodeFrame,text="End X",justify=RIGHT)
        self.linNodeStartXEntry = Entry(self.linNodeFrame,width=4)
        self.linNodeEndXEntry = Entry(self.linNodeFrame,width=4)
        self.linNodeStartXLabel.grid(row=2,column=2)
        self.linNodeStartXEntry.grid(row=2,column=3)
        self.linNodeEndXLabel.grid(row=3,column=2)
        self.linNodeEndXEntry.grid(row=3,column=3)

        self.linNodeStartYLabel = Label(self.linNodeFrame,text="Start Y",justify=RIGHT)
        self.linNodeEndYLabel = Label(self.linNodeFrame,text="End Y",justify=RIGHT)
        self.linNodeStartYEntry = Entry(self.linNodeFrame,width=4)
        self.linNodeEndYEntry = Entry(self.linNodeFrame,width=4)
        self.linNodeStartYLabel.grid(row=2,column=4)
        self.linNodeStartYEntry.grid(row=2,column=5)
        self.linNodeEndYLabel.grid(row=3,column=4)
        self.linNodeEndYEntry.grid(row=3,column=5)

        if self.dimensions == 3:
            self.linNodeStartZLabel = Label(self.linNodeFrame,text="Start Z",justify=RIGHT)
            self.linNodeEndZLabel = Label(self.linNodeFrame,text="End Z",justify=RIGHT)
            self.linNodeStartZEntry = Entry(self.linNodeFrame,width=4)
            self.linNodeEndZEntry = Entry(self.linNodeFrame,width=4)
            self.linNodeStartZLabel.grid(row=2,column=6)
            self.linNodeStartZEntry.grid(row=2,column=7)
            self.linNodeEndZLabel.grid(row=3,column=6)
            self.linNodeEndZEntry.grid(row=3,column=7)
            self.linNodeStartZEntry.bind('<Return>',self.linNode)
            self.linNodeEndZEntry.bind('<Return>',self.linNode)

        # bind return key to entry boxes
        self.linNodeStartNumEntry.bind('<Return>',self.linNode)
        self.linNodeStartXEntry.bind('<Return>',self.linNode)
        self.linNodeEndXEntry.bind('<Return>',self.linNode)
        self.linNodeStartYEntry.bind('<Return>',self.linNode)
        self.linNodeEndYEntry.bind('<Return>',self.linNode)
        self.linNodeSpaceEntry.bind('<Return>',self.linNode)
        self.linNodeNumNodesEntry.bind('<Return>',self.linNode)
        return

    def makeLinkPage(self):

        self.linkNumLabel = Label(self.linkPage,text="Link #")
        self.linkNumLabel.grid(row=1,column=0)
        self.linkNode1Label = Label(self.linkPage,text="Node 1")
        self.linkNode1Label.grid(row=2,column=0)
        self.linkNode2Label = Label(self.linkPage,text="Node 2")
        self.linkNode2Label.grid(row=3,column=0)
        self.linkMatLabel = Label(self.linkPage,text="Material #")
        self.linkMatLabel.grid(row=4,column=0)

        self.linkNumEntry = Entry(self.linkPage)
        self.linkNumEntry.grid(row=1,column=1)
        self.linkNode1Entry = Entry(self.linkPage)
        self.linkNode1Entry.grid(row=2,column=1)
        self.linkNode2Entry = Entry(self.linkPage)
        self.linkNode2Entry.grid(row=3,column=1)
        self.linkMatEntry = Entry(self.linkPage)
        self.linkMatEntry.grid(row=4,column=1)

        self.linkNumEntry.bind('<Return>',self.newLink)
        self.linkNode1Entry.bind('<Return>',self.newLink)
        self.linkNode2Entry.bind('<Return>',self.newLink)
        self.linkMatEntry.bind('<Return>',self.newLink)

        self.linkDelEntry = Entry(self.linkPage)
        self.linkDelEntry.grid(row=1,column=2)
        self.linkDelEntry.bind('<Return>',self.deleteLink)

        # set default entries
        self.linkNumEntry.insert(0,'0')
        self.linkNode1Entry.insert(0,'0')
        self.linkNode2Entry.insert(0,'0')
        self.linkMatEntry.insert(0,'0')

        # make buttons
        self.linkMakeBtn = Button(self.linkPage,text="New Link",command=self.newLink)
        self.linkMakeBtn.grid(row=0,column=1)
        self.linkDelBtn = Button(self.linkPage,text="Delete Link",command=self.deleteLink)
        self.linkDelBtn.grid(row=0,column=2)

        # make error label
        self.linkErrorLabel = Label(self.linkPage,text="",fg="red")
        self.linkErrorLabel.grid(row=5,column=0,columnspan=4)

        # make list treeview
        self.linkListTree = ttk.Treeview(self.linkPage,columns=("Node1","Node2","Material","Length"))
        self.linkListTree.grid(row=7,column=0,columnspan=4)
        self.linkListTree.column("#0",width=80)
        self.linkListTree.heading("#0",text="Link #")
        self.linkListTree.column("Node1",width=100)
        self.linkListTree.heading("Node1",text="Node 1")
        self.linkListTree.column("Node2",width=100)
        self.linkListTree.heading("Node2",text="Node 2")
        self.linkListTree.column("Material",width=100)
        self.linkListTree.heading("Material",text="Material")
        self.linkListTree.column("Length",width=100)
        self.linkListTree.heading("Length",text="Length")

        # multi-link tool
        self.multiLinkFrame = Frame(self.linkPage,relief = SUNKEN,borderwidth=1)
        self.multiLinkFrame.grid(row=8,column=0,columnspan=4,sticky=W+E+N+S)

        self.multiLinkLabel = Label(self.multiLinkFrame,text="MultiLink Tool",fg="blue",justify=LEFT)
        self.multiLinkLabel.grid(row=0,column=0)

        self.multiLinkBtn = Button(self.multiLinkFrame,text="Make Links",command = self.multiLink)
        self.multiLinkBtn.grid(row=0,column=2)

        self.multiLinkStartLinkLabel = Label(self.multiLinkFrame,text="First Link #",justify=RIGHT)
        self.multiLinkStartLinkEntry = Entry(self.multiLinkFrame,width=10)

        self.multiLinkStartNodeLabel = Label(self.multiLinkFrame,text="Node # Lower Bound",justify=RIGHT)
        self.multiLinkStartNodeEntry = Entry(self.multiLinkFrame,width=10)

        self.multiLinkEndNodeLabel = Label(self.multiLinkFrame,text="Node # Upper Bound",justify=RIGHT)
        self.multiLinkEndNodeEntry = Entry(self.multiLinkFrame,width=10)

        self.multiLinkMatLabel = Label(self.multiLinkFrame,text="Material #",justify=RIGHT)
        self.multiLinkMatEntry = Entry(self.multiLinkFrame,width=10)

        self.multiLinkNodeSpaceLabel = Label(self.multiLinkFrame,text="Node # Spacing to Link",justify=RIGHT)
        self.multiLinkNodeSpaceEntry = Entry(self.multiLinkFrame,width=10)
        self.multiLinkNodeSpaceEntry.insert(0,'1')

        self.multiLinkSpaceLabel = Label(self.multiLinkFrame,text="Link # Spacing",justify=RIGHT)
        self.multiLinkSpaceEntry = Entry(self.multiLinkFrame,width=10)

        self.multiLinkStartLinkLabel.grid(row=1,column=0)
        self.multiLinkStartLinkEntry.grid(row=1,column=1)
        self.multiLinkStartNodeLabel.grid(row=2,column=0)
        self.multiLinkStartNodeEntry.grid(row=2,column=1)
        self.multiLinkEndNodeLabel.grid(row=3,column=0)
        self.multiLinkEndNodeEntry.grid(row=3,column=1)
        self.multiLinkMatLabel.grid(row=1,column=2)
        self.multiLinkMatEntry.grid(row=1,column=3)
        self.multiLinkNodeSpaceLabel.grid(row=2,column=2)
        self.multiLinkNodeSpaceEntry.grid(row=2,column=3)
        self.multiLinkSpaceLabel.grid(row=3,column=2)
        self.multiLinkSpaceEntry.grid(row=3,column=3)

        self.multiLinkSpaceEntry.insert(0,'1')
        self.multiLinkMatEntry.insert(0,'0')

        self.multiLinkStartLinkEntry.bind('<Return>',self.multiLink)
        self.multiLinkStartNodeEntry.bind('<Return>',self.multiLink)
        self.multiLinkEndNodeEntry.bind('<Return>',self.multiLink)
        self.multiLinkNodeSpaceEntry.bind('<Return>',self.multiLink)
        self.multiLinkSpaceEntry.bind('<Return>',self.multiLink)
        self.multiLinkMatEntry.bind('<Return>',self.multiLink)
        return

    def makeConstrainPage(self):
        # make labels and entry boxes
        self.conNumLabel = Label(self.constrainPage,text="Node #")
        self.conNumLabel.grid(row=1,column=0)
        self.conXLabel = Label(self.constrainPage,text="X displacement")
        self.conXLabel.grid(row=2,column=0)
        self.conYLabel = Label(self.constrainPage,text="Y displacement")
        self.conYLabel.grid(row=3,column=0)

        self.conNumEntry = Entry(self.constrainPage)
        self.conNumEntry.grid(row=1,column=1)
        self.conXEntry = Entry(self.constrainPage)
        self.conXEntry.grid(row=2,column=1)
        self.conYEntry = Entry(self.constrainPage)
        self.conYEntry.grid(row=3,column=1)

        self.conNumEntry.insert(0,'0')
        self.conXEntry.insert(0,'0')
        self.conYEntry.insert(0,'0')

        self.conNumEntry.bind('<Return>',self.addConstraint)
        self.conXEntry.bind('<Return>',self.addConstraint)
        self.conYEntry.bind('<Return>',self.addConstraint)

        if self.dimensions == 3:
            self.conZLabel = Label(self.constrainPage,text="Z displacement")
            self.conZLabel.grid(row=4,column=0)
            self.conZEntry = Entry(self.constrainPage)
            self.conZEntry.grid(row=4,column=1)
            self.conZEntry.insert(0,'0')
            self.conZEntry.bind('<Return>',self.addConstraint)

        self.conDelEntry = Entry(self.constrainPage)
        self.conDelEntry.grid(row=1,column=2)
        self.conDelEntry.bind('<Return>',self.deleteConstraint)

        # make buttons
        self.conMakeBtn = Button(self.constrainPage,text="Add/Edit Constraint",
                                    command=self.addConstraint)
        self.conMakeBtn.grid(row=0,column=1)
        self.conDelBtn = Button(self.constrainPage,text="Delete Constraint",
                                    command=self.deleteConstraint)
        self.conDelBtn.grid(row=0,column=2)

        # make info label
        Label(self.constrainPage,text="Info: Leave entry blank for no constraint").grid(row=5,column=0,columnspan=3)

        # make error label
        self.conErrorLabel = Label(self.constrainPage,text="",fg="red")
        self.conErrorLabel.grid(row=6,column=0,columnspan=4)

        # make treeview
        if self.dimensions == 2:
            self.conListTree = ttk.Treeview(self.constrainPage,columns=("X","Y"))
        else:
            self.conListTree = ttk.Treeview(self.constrainPage,columns=("X","Y","Z"))
        self.conListTree.grid(row=7,column=0,columnspan=4)
        self.conListTree.column("#0",width=120)
        self.conListTree.heading("#0",text="Node #")
        self.conListTree.column("X",width=120)
        self.conListTree.heading("X",text="X")
        self.conListTree.column("Y",width=120)
        self.conListTree.heading("Y",text="Y")
        if self.dimensions == 3:
            self.conListTree.column("Z",width=120)
            self.conListTree.heading("Z",text="Z")

    def makeForcePage(self):
        # make labels and entry boxes
        self.forceNumLabel = Label(self.forcePage,text="Node #")
        self.forceNumLabel.grid(row=1,column=0)
        self.forceNumEntry = Entry(self.forcePage)
        self.forceNumEntry.grid(row=1,column=1)
        self.forceXLabel = Label(self.forcePage,text="X Force")
        self.forceXLabel.grid(row=2,column=0)
        self.forceXEntry = Entry(self.forcePage)
        self.forceXEntry.grid(row=2,column=1)
        self.forceYLabel = Label(self.forcePage,text="Y Force")
        self.forceYLabel.grid(row=3,column=0)
        self.forceYEntry = Entry(self.forcePage)
        self.forceYEntry.grid(row=3,column=1)

        self.forceNumEntry.bind('<Return>',self.addForce)
        self.forceXEntry.bind('<Return>',self.addForce)
        self.forceYEntry.bind('<Return>',self.addForce)

        if self.dimensions == 3:
            self.forceZLabel = Label(self.forcePage,text="Z Force")
            self.forceZLabel.grid(row=4,column=0)
            self.forceZEntry = Entry(self.forcePage)
            self.forceZEntry.grid(row=4,column=1)
            self.forceZEntry.bind('<Return>',self.addForce)

        self.forceDelEntry = Entry(self.forcePage)
        self.forceDelEntry.grid(row=1,column=2)
        self.forceDelEntry.bind('<Return>',self.deleteForce)

        # make info label
        Label(self.forcePage,text="Info: Leave entry blank for no force").grid(row=5,column=0,columnspan=3)

        # make buttons
        self.forceMakeBtn = Button(self.forcePage,text="Add/Edit Force",command=self.addForce)
        self.forceMakeBtn.grid(row=0,column=1)
        self.forceDelBtn = Button(self.forcePage,text="Delete Force",command=self.deleteForce)
        self.forceDelBtn.grid(row=0,column=2)

        # make error label
        self.forceErrorLabel = Label(self.forcePage,text="",fg="red")
        self.forceErrorLabel.grid(row=6,column=0,columnspan=4)

        # make treeview
        if self.dimensions == 2:
            self.forceListTree = ttk.Treeview(self.forcePage,columns=("X","Y"))
        else:
            self.forceListTree = ttk.Treeview(self.forcePage,columns=("X","Y","Z"))
        self.forceListTree.column("#0",width=120)
        self.forceListTree.heading("#0",text="Node #")
        self.forceListTree.column("X",width=120)
        self.forceListTree.heading("X",text="X")
        self.forceListTree.column("Y",width=120)
        self.forceListTree.heading("Y",text="Y")
        if self.dimensions == 3:
            self.forceListTree.column("Z",width=120)
            self.forceListTree.heading("Z",text="Z")
        self.forceListTree.grid(row=7,column=0,columnspan=4)

    def makeSolutionPage(self):
        # make solve button
        self.solveBtn = Button(self.solutionPage,text="Solve",command=self.solve)
        self.solveBtn.grid(row=0,column=0)

        # make plotting buttons
        self.showModel = BooleanVar()
        self.plotModelCheck = Checkbutton(self.solutionPage,text="Plot Pre-loaded Model",justify=LEFT,command = self.updatePlot,variable = self.showModel)
        self.plotModelCheck.grid(row=1,column=0)
        self.plotModelCheck.select()

        self.showExag = BooleanVar()
        self.plotExagCheck = Checkbutton(self.solutionPage,text="Exaggerated Deformation",justify=LEFT,command = self.updatePlot,variable = self.showExag)
        self.plotExagCheck.grid(row=2,column=0)

        self.showResult = BooleanVar()
        self.plotResultCheck = Checkbutton(self.solutionPage,text = "Plot Exact Results",justify=LEFT,command = self.updatePlot,variable = self.showResult)
        self.plotResultCheck.grid(row=3,column=0)

        self.showStress = BooleanVar()
        self.showStressCheck = Checkbutton(self.solutionPage,text="Show Stress",justify=LEFT,variable = self.showStress,command = self.updatePlot)
        self.showStressCheck.grid(row=4,column=0)

        if self._Solution is None:
            self.plotExagCheck.config(state = DISABLED)
            self.plotResultCheck.config(state = DISABLED)
            self.showStressCheck.config(state = DISABLED)

        # make error label
        self.solErrorLabel = Label(self.solutionPage,text="",fg="red")
        self.solErrorLabel.grid(row=5,column=0,columnspan=4)

        # make solution display notebook
        self.solutionNotebook = ttk.Notebook(self.solutionPage,name="results",width=450,height=300)
        self.solutionNotebook.grid(row=6,column=0,columnspan=4)

        self.nodalSolution = Frame(self.solutionNotebook,name="nodal")
        self.makeNodalPage()
        self.solutionNotebook.add(self.nodalSolution,text="Nodal")

        self.reactSolution = Frame(self.solutionNotebook,name="reaction")
        self.makeReactPage()
        self.solutionNotebook.add(self.reactSolution,text="Reaction")

        self.ssSolution = Frame(self.solutionNotebook,name="stress/strain")
        self.makeStressStrainPage()
        self.solutionNotebook.add(self.ssSolution,text="Link Loading")

        self.massSolution = Frame(self.solutionNotebook,name="length/mass")
        self.makeMassPage()
        self.solutionNotebook.add(self.massSolution,text = "Length/Mass")

    def makeNotePage(self):
        self.noteUnitLabel = Label(self.notePage,text = "Model Units")
        self.noteMassLabel = Label(self.notePage,text="Mass",justify=RIGHT)
        self.noteLengthLabel = Label(self.notePage,text="Length",justify=RIGHT)
        self.noteTimeLabel = Label(self.notePage,text="Time",justify=RIGHT)

        self.noteMassEntry = Entry(self.notePage)
        self.noteLengthEntry = Entry(self.notePage)
        self.noteTimeEntry = Entry(self.notePage)

        self.noteUnitLabel.grid(row=0,column=0,columnspan = 2)
        self.noteMassLabel.grid(row=1,column=0)
        self.noteLengthLabel.grid(row=2,column=0)
        self.noteTimeLabel.grid(row=3,column=0)

        self.noteMassEntry.grid(row=1,column=1)
        self.noteLengthEntry.grid(row=2,column=1)
        self.noteTimeEntry.grid(row=3,column=1)

        self.noteLabel = Label(self.notePage,text="Model Notes")
        self.noteText = Text(self.notePage,borderwidth=3,relief=SUNKEN,width=67,height=23)

        self.noteLabel.grid(row=4,column=0,columnspan=2)
        self.noteText.grid(row=5,column=0,columnspan=2,rowspan=15)

        self.noteMassEntry.insert(0,self.units['mass'])
        self.noteLengthEntry.insert(0,self.units['length'])
        self.noteTimeEntry.insert(0,self.units['time'])
        try:
            self.noteText.insert(END,self.notes)
        except:
            self.notes = ""
        return

#---Solution Notebook Pages---
    def makeNodalPage(self):
        if self.dimensions == 2:
            self.nodalListTree = ttk.Treeview(self.nodalSolution,columns=("X","Y"))
            colWidth = 140
        else:
            self.nodalListTree = ttk.Treeview(self.nodalSolution,columns=("X","Y","Z"))
            colWidth = 120
        self.nodalListTree.column("#0",width=60)
        self.nodalListTree.heading("#0",text="Node #")
        self.nodalListTree.column("X",width=colWidth)
        self.nodalListTree.heading("X",text="X")
        self.nodalListTree.column("Y",width=colWidth)
        self.nodalListTree.heading("Y",text="Y")
        if self.dimensions == 3:
            self.nodalListTree.column("Z",width=colWidth)
            self.nodalListTree.heading("Z",text="Z")
        self.nodalListTree.pack(fill=BOTH)

    def makeReactPage(self):
        if self.dimensions == 2:
            self.reactListTree = ttk.Treeview(self.reactSolution,columns=("X","Y"))
            colWidth = 140
        else:
            self.reactListTree = ttk.Treeview(self.reactSolution,columns=("X","Y","Z"))
            colWidth = 120
        self.reactListTree.column("#0",width=60)
        self.reactListTree.heading("#0",text="Node #")
        self.reactListTree.column("X",width=colWidth)
        self.reactListTree.heading("X",text="X")
        self.reactListTree.column("Y",width=colWidth)
        self.reactListTree.heading("Y",text="Y")
        if self.dimensions == 3:
            self.reactListTree.column("Z",width=colWidth)
            self.reactListTree.heading("Z",text="Z")
        self.reactListTree.pack(fill=BOTH)

    def makeStressStrainPage(self):
        self.ssListTree = ttk.Treeview(self.ssSolution,columns=("Tension","Stress","Strain"))
        self.ssListTree.column("#0",width=60)
        self.ssListTree.heading("#0",text="Link #")
        self.ssListTree.column("Tension",width = 120)
        self.ssListTree.heading("Tension",text="Tension")
        self.ssListTree.column("Stress",width=120)
        self.ssListTree.heading("Stress",text="Stress")
        self.ssListTree.column("Strain",width=120)
        self.ssListTree.heading("Strain",text="Strain")
        self.ssListTree.pack(fill=BOTH)

    def makeMassPage(self):
        self.massListTree = ttk.Treeview(self.massSolution,columns = ("Length","Mass"))
        self.massListTree.column("#0",width=100)
        self.massListTree.heading("#0",text="Material #")
        self.massListTree.column("Length",width=140)
        self.massListTree.heading("Length",text="Length")
        self.massListTree.column("Mass",width=140)
        self.massListTree.heading("Mass",text="Mass")
        self.massListTree.pack(fill=BOTH)

################## Object Initialization ##################
    def save(self,event=None):
        if self.name == "untitled":
            self.saveAs()
            return
        else:
            self.commandLine.insert(0,"saved as " + str(self.name))
            self.commandLine.focus()
            self.commandLine.select_range(0,END)
        
        self.updateNotes()

        file = open(str(self.name),'wb')
        modelInfo = [self.name,self.dimensions,self._Materials,self._Nodes,self._Links,self._Scope,self._Solution,self.units,self.notes]
        pickle.dump(modelInfo,file,protocol=pickle.HIGHEST_PROTOCOL)
        file.close()
        return

    def saveAs(self):
        self.updateNotes()

        self.name = str(tkfd.asksaveasfilename())
        self.commandLine.insert(0,"saved as " + str(self.name))
        self.commandLine.focus()
        self.commandLine.select_range(0,END)
        self.root.title(self.name)
        file = open(str(self.name),'wb')
        modelInfo = [self.name,self.dimensions,self._Materials,self._Nodes,self._Links,self._Scope,self._Solution,self.units,self.notes]
        pickle.dump(modelInfo,file,protocol=pickle.HIGHEST_PROTOCOL)
        file.close()
        return

    def load(self,filename):
        file = open(str(filename),'rb')
        modelInfo = pickle.load(file)
        file.close()

        self.name = filename
        self.dimensions = modelInfo[1]
        self._Materials = modelInfo[2]
        self._Nodes = modelInfo[3]
        self._Links = modelInfo[4]
        self._Scope = modelInfo[5]
        self._Solution = modelInfo[6]

        # backwards-compatability exceptions for older models
        try:
            self.units = modelInfo[7]
            self.notes = modelInfo[8]
        except:
            print('failure loading units or notes info')
            self.units = {'mass':'kg','length':'m','time':'s'}
            self.notes = ""
        for num, mat in self._Materials.items():
            if not hasattr(mat,'density'): 
                mat.density = 0
        if self._Solution is not None and not hasattr(self._Solution,'totalMass'):
            self._Solution.totalMass = 0
            self._Solution.totalLength = 0
            self._Solution._Length = dict()
            self._Solution._Mass = dict()

        return

    def __init__(self,dimensions=None,load=False,filename=None):
        if load:
            self.load(filename)
        else:
            self.name = "untitled"
            self.dimensions = dimensions

            self._Materials = dict() # materials dictionary: number->FEALinkMaterial.Material
            self._Nodes = dict() # nodes dictionary: number->FEALinkNode.Node
            self._Links = dict() # links dictionary: number->FEALinkLink.Link
            self._Scope = FEALinkScope.Scope(self.dimensions) # will be defined as FEALinkScope.Scope object in __init__
            self._Solution = None
            self.units = {'mass':'kg','length':'m','time':'s'}
            self.notes = ""

        self._CommandList = list()
        self.commandIndex = -1

        self.root = Toplevel()
        if self.dimensions == 2:
            self.root.title(self.name)
        else:
            self.root.title(self.name)

        self.root.geometry("1200x600+200+200")
        self.root.bind('<Command-s>',self.save)
        self.root.bind('<Control-s>',self.save)
        self.makeInterface()
        self.makePlot()
        self.updateLists()
        self.bringToFront()
        self.root.mainloop()
        return
