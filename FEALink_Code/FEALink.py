# FEALink
# created by Ryan Arata
# last updated May 2016
#
# This module implements the FEALink start center

import sys
try:
    from Tkinter import * # python 2.7
except:
    from tkinter import * # python 3

try:
    import tkFileDialog as tkfd # python 2.7
except:
    import tkinter.filedialog as tkfd # python 3
import FEALinkModel

class FEALinkStartCenter(Frame):
    def bringToFront(self): 
        self.root.lift()
        self.root.attributes('-topmost',1)
        self.root.after_idle(self.root.attributes,'-topmost',0)

    def addButtons(self):
        self.new2d_button = Button(self,text="New 2d Model",command=self.new2dModel)
        self.new2d_button.config(width=20)
        self.new2d_button.pack(fill=X,expand=1)

        self.new3d_button = Button(self,text="New 3d Model",command=self.new3dModel)
        self.new3d_button.config(width=20)
        self.new3d_button.pack(fill=X)

        self.load_button = Button(self,text="Load Model",command=self.loadModel)
        self.load_button.config(width=20)
        self.load_button.pack(fill=X)

        self.quit_button = Button(self,text="Quit",command=self.quit)
        self.quit_button.config(width=20)
        self.quit_button.pack(fill=X)

    def makeMenu(self):
        self.menu = Menu(self.root)
        self.fileMenu = Menu(self.menu,tearoff=0)
        self.fileMenu.add_command(label="New 2D Model",command = self.new2dModel)
        self.fileMenu.add_command(label="New 3D Model",command = self.new3dModel)
        self.fileMenu.add_command(label="Load Model",command = self.loadModel)
        self.fileMenu.add_command(label="Quit",command = self.quit)
        self.menu.add_cascade(label="File",menu = self.fileMenu)
        self.root.config(menu=self.menu)
        return

    def quit(self):
        for model in self.Models:
            model.root.destroy()
            del model
            self.numModels -= 1
        self.root.destroy()
        sys.exit()

    def new2dModel(self):
        self.Models[self.numModels] = FEALinkModel.Model(dimensions=2)
        self.numModels += 1

    def new3dModel(self):
        self.Models[self.numModels] = FEALinkModel.Model(dimensions=3)
        self.numModels += 1

    def loadModel(self):
        filename = tkfd.askopenfilename()
        self.Models[self.numModels] = FEALinkModel.Model(load=True,filename=filename)
        self.numModels += 1

    def __init__(self,master=None):
        Frame.__init__(self,master)
        self.root = master
        self.pack()
        self.addButtons()
        self.makeMenu()
        self.Models = list()
        self.numModels = 0

root = Tk()
root.title("FEALink Start Center")
root.geometry("200x120")
startCenter = FEALinkStartCenter(master = root)
startCenter.bringToFront()
root.mainloop()
