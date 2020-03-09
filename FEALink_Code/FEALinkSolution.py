# FEALinkNode
# Ryan Arata
# updated May 2016
#
# This module implements the Solution class

import FEALinkModel
import FEALinkNode
import FEALinkLink
import numpy as np

class Solution(object):

	def isConstrained(self):
		# check for forces and constraints in x-direction
		hasXForce = False
		isXConstrained = False
		for num,node in self._Nodes.items():
			if node.xforce != 0:
				hasXForce = True
			if node.xconstrain != None:
				isXConstrained = True
		if hasXForce and not isXConstrained: return False

		# check y-direction
		hasYForce = False
		isYConstrained = False
		for num,node in self._Nodes.items():
			if node.yforce != 0:
				hasYForce = True
			if node.yconstrain != None:
				isYConstrained = True
		if hasYForce and not isYConstrained: return False

		# check z-direction if 3D
		if self.dimensions == 3:
			hasZForce = False
			for num,node in self._Nodes.items():
				if node.zforce != 0:
					hasZForce = True
				if node.zconstrain != None:
					isZConstrained = True
			if hasZForce and not isZConstrained: return False

		return True

	def isStable(self):
		c = 0 # number of constraints
		for num,node in self._Nodes.items():
			c += node.numConstraints()

		n = len(self._Nodes) # number of nodes
		l = len(self._Links) # number of links

		if c+l >= self.dimensions*n: return True
		else: return False

	def getStiffnessMatrix(self):
		# set up m x m matrix
		K = np.zeros([self.size,self.size])

		# fill K matrix
		d = self.dimensions
		if d == 2: # 2D stiffness matrix
			for num,link in self._Links.items():
				i = link.node1.number
				j = link.node2.number
				stiffness = link.material.area * link.material.modulus / link.length # AE/L
				blockii = stiffness * np.array([[link.cos**2       , link.cos*link.sin],
												[link.cos*link.sin , link.sin**2      ]])
				blockij = -blockii
				blockji = -blockii
				blockjj = blockii

				K[ d*i : d*(i+1) , d*i : d*(i+1)] += blockii
				K[ d*i : d*(i+1) , d*j : d*(j+1)] += blockij
				K[ d*j : d*(j+1) , d*i : d*(i+1)] += blockji
				K[ d*j : d*(j+1) , d*j : d*(j+1)] += blockjj
		else: # 3D stiffness matrix
			for num,link in self._Links.items():
				i = link.node1.number
				j = link.node2.number
				stiffness = link.material.area * link.material.modulus / link.length # AE/L
				blockii = stiffness * np.array([[link.cosx**2        , link.cosx*link.cosy , link.cosx*link.cosz],
												[link.cosx*link.cosy , link.cosy**2        , link.cosy*link.cosz],
												[link.cosx*link.cosz , link.cosy*link.cosz , link.cosz**2       ]])
				blockij = -blockii
				blockji = -blockii
				blockjj = blockii

				K[ d*i : d*(i+1) , d*i : d*(i+1)] += blockii
				K[ d*i : d*(i+1) , d*j : d*(j+1)] += blockij
				K[ d*j : d*(j+1) , d*i : d*(i+1)] += blockji
				K[ d*j : d*(j+1) , d*j : d*(j+1)] += blockjj

		return K

	def getForceVector(self):
		# Go through each node and fill the force vector
		F = np.zeros([self.size,1])

		d = self.dimensions
		if d == 2:
			for num,node in self._Nodes.items():
				F[d*num] = node.xforce
				F[d*num+1] = node.yforce
		else:
			for num,node in self._Nodes.items():
				F[d*num] = node.xforce
				F[d*num+1] = node.yforce
				F[d*num+2] = node.zforce

		return F

	def getDisplacement(self): # Uses the penalty method to get displacements
		c = self.penaltyMultiplier; # penalty multiplier
		d = self.dimensions

		# set up penalty matrices
		Fp = np.zeros_like(self.F)
		Kp = np.zeros_like(self.K)

		# get penalty matrices
		if d == 2:
			for num,node in self._Nodes.items():
				if node.xconstrain != None: 
					rowMax = max(abs(self.K[d*num,:]))
					Fp[d*num] = c*node.xconstrain*rowMax
					Kp[d*num,d*num] = c*rowMax

				if node.yconstrain != None: 
					rowMax = max(abs(self.K[d*num+1,:]))
					Fp[d*num+1] = c*node.yconstrain*rowMax
					Kp[d*num+1,d*num+1] = c*rowMax

		else:
			for num,node in self._Nodes.items():
				if node.xconstrain != None: 
					rowMax = max(abs(self.K[d*num,:]))
					Fp[d*num] = c*node.xconstrain*rowMax
					Kp[d*num,d*num] = c*rowMax

				if node.yconstrain != None: 
					rowMax = max(abs(self.K[d*num+1,:]))
					Fp[d*num+1] = c*node.yconstrain*rowMax
					Kp[d*num+1,d*num+1] = c*rowMax

				if node.zconstrain != None: 
					rowMax = max(abs(self.K[d*num+2,:]))
					Kp[d*num+2,d*num+2] = c*rowMax
					Fp[d*num+2] = c*node.zconstrain*rowMax

		self.Fp = Fp
		self.Kp = Kp
		# Solve for U (Kp*U = Fp)
		Fp = Fp + self.F
		Kp = Kp + self.K

		# fill in diagonals in rows that have no term - these displacements will be 0
		for i in range(0,self.size):
			if np.count_nonzero(Kp[i,:]) == 0:
				Kp[i,i] = 42 # the answer to the ultimate question of life, the universe, and everything (arbitrary #)

		U = np.linalg.solve(Kp,Fp)
		return U

	def getReactions(self):
		R = np.dot(self.K,self.U)
		return R

	def compileSolution(self):
		d = self.dimensions
		maxDisplacement = self.getMaxDisplacement()
		# make solution nodes
		for num,node in self._Nodes.items():
			displacement = np.transpose(self.U[num*d:(num+1)*d])[0,:]
			calculatedDisplacement = displacement
			reaction = np.transpose(self.R[num*d:(num+1)*d])[0,:]
			if node.xconstrain is not None:
				displacement[0] = node.xconstrain
			if node.yconstrain is not None:
				displacement[1] = node.yconstrain
			if d is 3 and node.zconstrain is not None:
				displacement[2] = node.zconstrain
			self._SolNodes[num] = NodeSolution(node,displacement,calculatedDisplacement,reaction,maxDisplacement,self.modelSize)

		for num,link in self._Links.items():
			solnode1 = self._SolNodes[link.node1.number]
			solnode2 = self._SolNodes[link.node2.number]
			self._SolLinks[num] = LinkSolution(num,solnode1,solnode2,link.material)

		return

	def getMaxDisplacement(self):
		maxDisplacement = 0
		d = int(self.dimensions)

		if d == 2:
			for i in range(0,int(self.size/d)):
				disp = np.sqrt(self.U[i*d]**2 + self.U[i*d+1]**2)
				maxDisplacement = max(maxDisplacement,disp)
		else:
			for i in range(0,int(self.size/d)):
				disp = np.sqrt(self.U[i*d]**2 + self.U[i*d+1]**2 + self.U[i*d+2]**2)
				maxDisplacement = max(maxDisplacement,disp)

		if maxDisplacement == 0: # to avoid /0 issues
			maxDisplacement = 1

		return maxDisplacement

	def constraintsMet(self):
		d = self.dimensions
		c = self.penaltyMultiplier

		# get maximum nodal displacement
		maxDisp = 0
		for num in self._Nodes:
			disp = np.sqrt(sum(self.U[d*num:d*(num+1)]**2))
			maxDisp = max(maxDisp,disp)

		allowableError = maxDisp/c*2

		# check that all constraints are within error tolerance
		if d == 2:
			for num,node in self._Nodes.items():
				if node.xconstrain is not None and np.abs(node.xconstrain-self.U[num*d]) > allowableError: return False
				if node.yconstrain is not None and np.abs(node.yconstrain-self.U[num*d+1]) > allowableError: return False
		else:
			for num,node in self._Nodes.items():
				if node.xconstrain is not None and np.abs(node.xconstrain-self.U[num*d]) > allowableError: return False
				if node.yconstrain is not None and np.abs(node.yconstrain-self.U[num*d+1]) > allowableError: return False
				if node.zconstrain is not None and np.abs(node.zconstrain-self.U[num*d+2]) > allowableError: return False

		return True

	def getStressStrain(self):
		self.maxStrain = 0
		self.minStrain = 0
		self.maxStress = 0
		self.minStress = 0
		self.minTension = 0
		self.maxTension = 0
		for num,solLink in self._SolLinks.items():
			li = self._Links[num].length
			lf = self._SolLinks[num].length
			strain = (lf-li)/li
			solLink.addStrain(strain)
			stress = solLink.stress # stress is calculated when strain is given
			tension = solLink.tension

			self.maxStrain = max(self.maxStrain,strain)
			self.minStrain = min(self.minStrain,strain)
			self.maxStress = max(self.maxStress,stress)
			self.minStress = min(self.minStress,stress)
			self.maxTension = max(self.maxTension,tension)
			self.minTension = min(self.minTension,tension)
		return

	def getMassProperties(self):
		self._Length = dict()
		self._Mass = dict()
		self.totalMass = 0
		self.totalLength = 0
		for num,link in self._Links.items():
			matNum = link.material.number
			area = link.material.area
			density = link.material.density
			mass = link.length*area*density
			if matNum not in self._Length:
				self._Length[matNum] = link.length
				self._Mass[matNum] = mass
			else:
				self._Length[matNum] += link.length
				self._Mass[matNum] += mass
			self.totalLength += link.length
			self.totalMass += mass
		return


	def solve(self):
		# Check constraint and force directions
		if not self.isConstrained():
			return "Error: Problem is insufficiently constrained"

		# Check for instability
		if not self.isStable():
			return "Error: Unstable structure - check constraints"

		try:
			# create stiffness matrix
			self.K = self.getStiffnessMatrix()
			# create force vector (input forces only, not reactions)
			self.F = self.getForceVector()
			# Solve for displacement with penalty method
			self.U = self.getDisplacement()
			# Use displacement from penalty method to get reaction forces
			self.R = self.getReactions()
		except:
			return "Solve Failed"

		# Create solution data (nodes and links)
		self.compileSolution()

		# Solve for stress and strain
		self.getStressStrain()

		# perform checks to ensure adherance to boudary conditions
		if not self.constraintsMet():
			return "Warning: Solution did not meet the constraints"

		self.getMassProperties()

		return "Success"

	def __init__(self,Model):
		self.dimensions = Model.dimensions
		self._Nodes = Model._Nodes
		self._Links = Model._Links
		self.size = (max(self._Nodes)+1)*self.dimensions
		self.penaltyMultiplier = 1e6
		self._SolNodes = dict()
		self._SolLinks = dict()
		self.modelSize = Model._Scope.modelSize


class NodeSolution(object):
	def plotExaggerated(self,display,showNumbers = True):
		if self.dimensions == 2:
			display.plot(self.exaggerated[0],self.exaggerated[1],'b.')
			if showNumbers:
				display.text(self.exaggerated[0],self.exaggerated[1],'%s' % str(self.number),size=11)
		else:
			display.plot([self.exaggerated[0]],[self.exaggerated[1]],[self.exaggerated[2]],'b.')
			if showNumbers:
				display.text(self.exaggerated[0],self.exaggerated[1],self.exaggerated[2],'%s' % str(self.number),size=11,zorder=1)

	def plot(self,display,showNumbers = True):
		if self.dimensions == 2:
			display.plot(self.position[0],self.position[1],'b.')
			if showNumbers:
				display.text(self.position[0],self.position[1],'%s' % str(self.number),size=11)
		else:
			display.plot([self.position[0]],[self.position[1]],[self.position[2]],'b.')
			if showNumbers:
				display.text(self.position[0],self.position[1],self.position[2],'%s' % str(self.number),size=11,zorder=1)
		return

	def __init__(self,node,displacement,calculatedDisplacement,reaction,maxDisplacement = 1,modelSize = 1):
		self.number = node.number
		self.dimensions = node.dimensions
		self.reaction = reaction
		self.displacement = displacement
		self.calculatedDisplacement = calculatedDisplacement # keep track for stress solving purposes

		maxExag = .05*modelSize

		if self.dimensions == 2:
			self.position = np.array([node.x,node.y]) + displacement
			self.exaggerated = np.array([node.x,node.y]) + displacement/maxDisplacement*maxExag
		else:
			self.position = np.array([node.x,node.y,node.z]) + displacement
			self.exaggerated = np.array([node.x,node.y,node.z]) + displacement/maxDisplacement*maxExag
		self.linkedNodes = node.linkedNodes
		return


class LinkSolution(object):
	def addStrain(self,strain):
		self.strain = strain
		self.stress = self.material.modulus * strain
		self.tension = self.stress*self.material.area
		return

	def getColor(self,maxStress,minStress):
		if maxStress == None:
			colorCode = 'c'
		elif self.stress >= 0:
			colormag = (self.stress/maxStress)
			colorCode = (colormag,0,0) # shade of red for tension
		elif self.stress < 0:
			colormag = (self.stress/minStress)
			colorCode = (0,colormag,0) # green for compression
		return colorCode

	def plotExaggerated(self,display,maxStress = None,minStress = None,showNumbers = True):
		colorCode = self.getColor(maxStress,minStress)
		xmid = self.xEx[0]*.55 + self.xEx[1]*.45
		ymid = self.yEx[0]*.55 + self.yEx[1]*.45
		if self.dimensions == 2:
			display.plot(self.xEx,self.yEx,color = colorCode)
			if showNumbers == True:
				display.text(xmid,ymid,'%s' % str(self.number),size=11,color=colorCode)
		else:
			display.plot(self.xEx,self.yEx,self.zEx,color = colorCode)
			zmid = self.zEx[0]*.55 + self.zEx[1]*.45
			if showNumbers == True:
				display.text(xmid,ymid,zmid,'%s' % str(self.number),size=11,color=colorCode)
		return

	def plot(self,display,showNumbers = True,maxStress = None,minStress = None):
		colorCode = self.getColor(maxStress,minStress)

		if self.dimensions == 2:
			display.plot(self.x,self.y,color = colorCode)
			if showNumbers == True:
				display.text(self.xmid,self.ymid,'%s' % str(self.number),size=11,color=colorCode)
		else:
			display.plot(self.x,self.y,self.z,color = colorCode)
			if showNumbers == True:
				display.text(self.xmid,self.ymid,self.zmid,'%s' % str(self.number),size=11,zorder=1,color=colorCode)
		return

	def __init__(self,num,solnode1,solnode2,material):
		self.number = num
		self.node1 = solnode1 # FEALinkNode.Node object
		self.node2 = solnode2
		self.material = material # FEALinkMaterial.Material object
		self.dimensions = solnode1.dimensions
		self.x = [solnode1.position[0],solnode2.position[0]]
		self.xEx = [solnode1.exaggerated[0],solnode2.exaggerated[0]]
		self.y = [solnode1.position[1],solnode2.position[1]]
		self.yEx = [solnode1.exaggerated[1],solnode2.exaggerated[1]]
		self.xmid = (.55*self.x[0]+.45*self.x[1])
		self.ymid = (.55*self.y[0]+.45*self.y[1])
		if self.dimensions == 2:
			self.length = np.sqrt((self.x[0]-self.x[1])**2 + (self.y[0]-self.y[1])**2)
		else:
			self.z = [solnode1.position[2],solnode2.position[2]]
			self.zEx = [solnode1.exaggerated[2],solnode2.exaggerated[2]]
			self.zmid = (.55*self.z[0]+.45*self.z[1])
			self.length = np.sqrt((self.x[0]-self.x[1])**2 + (self.y[0]-self.y[1])**2 + (self.z[0]-self.z[1])**2)
		return