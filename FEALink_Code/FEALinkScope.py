# FEALinkScope
# Ryan Arata
# updated May 2016
#
# This module implements the Scope class
# This class contains information on how large
# the FEALink model is.

import FEALinkNode
import numpy as np

class Scope(object):
	_buffer = 0.05 # constant buffer added to any scope to eliminate 0-scope problems
	_scale = 1.2 # scales up area to 1.2 times limits

	def updateScope(self,nodes): # can always be called, but slower than expandScope for additions
		self.xmin = None
		self.xmax = None
		self.ymin = None
		self.ymax = None
		self.xScope = None
		self.yScope = None
		self.modelSize = None
		if self.dimensions == 3:
			self.zmin = None
			self.zmax = None
			self.zScope = None

		if len(nodes) == 0:
			return

		for num,node in nodes.items():
			if self.xmin == None:
				self.xmin = node.x
				self.ymin = node.y
				if self.dimensions == 3:
					self.zmin = node.z

			self.xmin = min(self.xmin,node.x)
			self.ymin = min(self.ymin,node.y)
			self.xmax = max(self.xmax,node.x)
			self.ymax = max(self.ymax,node.y)
			if self.dimensions == 3:
				self.zmin = min(self.zmin,node.z)
				self.zmax = max(self.zmax,node.z)

		self.xScope = self.xmax-self.xmin+self._buffer
		self.yScope = self.ymax-self.ymin+self._buffer
		if self.dimensions == 2:
			self.modelSize = np.sqrt(self.xScope**2 + self.yScope**2)
		else:
			self.zScope = self.zmax-self.zmin+self._buffer
			self.modelSize = np.sqrt(self.xScope**2 + self.yScope**2 + self.zScope**2)

		self.setLimits()
		return

	def expandScope(self,node):
		if self.modelSize == None: # happens if the new node is the only node
			self.xmin = node.x
			self.ymin = node.y
			self.xmax = node.x
			self.ymax = node.y
			if self.dimensions == 3:
				self.zmin = node.z
				self.zmax = node.z

		else: # new node added
			self.xmin = min(self.xmin,node.x)
			self.ymin = min(self.ymin,node.y)
			self.xmax = max(self.xmax,node.x)
			self.ymax = max(self.ymax,node.y)
			if self.dimensions == 3:
				self.zmin = min(self.zmin,node.z)
				self.zmax = max(self.zmax,node.z)

		# update scope variables
		self.xScope = self.xmax-self.xmin+self._buffer
		self.yScope = self.ymax-self.ymin+self._buffer
		if self.dimensions == 2:
			self.modelSize = np.sqrt(self.xScope**2 + self.yScope**2)
		else:
			self.zScope = self.zmax-self.zmin+self._buffer
			self.modelSize = np.sqrt(self.xScope**2 + self.yScope**2 + self.zScope**2)

		self.setLimits()
		return

	def setLimits(self):
		xmid = (self.xmax+self.xmin)/2
		ymid = (self.ymax+self.ymin)/2
		if self.dimensions == 2:
			if self.xScope >= self.yScope:
				half = self.xScope/2*self._scale
			else:
				half = self.yScope/2*self._scale
		else:
			zmid = (self.zmax+self.zmin)/2
			if self.xScope >= self.yScope and self.xScope >= self.zScope:
				half = self.xScope/2*self._scale
			elif self.yScope >= self.xScope and self.yScope >= self.zScope:
				half = self.yScope/2*self._scale
			else:
				half = self.zScope/2*self._scale

		self.xlimits = [xmid-half,xmid+half]
		self.ylimits = [ymid-half,ymid+half]
		if self.dimensions == 3:
			self.zlimits = [zmid-half,zmid+half]

	def __init__(self,dimensions):
		self.dimensions = dimensions
		self.xmin = None
		self.xmax = None
		self.ymin = None
		self.ymax = None
		self.xScope = None
		self.yScope = None
		self.xlimits = [-.1,.1]
		self.ylimits = [-.1,.1]
		if self.dimensions == 3:
			self.zmin = None
			self.zmax = None
			self.zScope = None
			self.zlimits = [-.1,.1]
		self.modelSize = None
		return
