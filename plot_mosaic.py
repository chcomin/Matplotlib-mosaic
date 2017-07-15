import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist, squareform
from matplotlib.lines import Line2D as pltLine
import cPickle


class PlotMosaic:
	"""
	Create plot mosaic. This class has two interfaces. The zero-state interface is for creating 
	a new plot mosaic. The load-state interface is used for loading a previously saved mosaic.
	
	Parameters (zero-state interface)
	----------
	x : array_like
		x values for main plot
	y : array_like
		y values for main plot
	plotsData : array_like
		List of lists, each i-th sublist containing the x and y data corresponding to the 
		i-th point in the main plot
	dragPlotter : function
		Function with arguments (x, y, ax), where x and y are the data points and ax an 
		axis. This function is used for plotting the draggable axes
	figSize : tuple of two integers
		Figure size in inches
	mainAxesRect : tuple of four integers
		Main axes position in the format [left, bottom, width, height]. Unit is figure
		coordinates between 0 and 1
	dragAxesSize : tuple of two integers
		Width of the draggable axesHeight. Unit is figure coordinates between 0 and 1
	pickerRadius : float
		Radius for point picking detection		
	showMovement : bool
		Set to true for showing data while dragging the plot. False hides the data while 
		dragging
	mainPlotKwargs : dict
		Dictionary containing drawing properties for the main axes

	Parameters (load-state interface)
	----------
	x : string	
		Path to file containing the plot mosaic to be loaded.	
	"""
	
	def __init__(self, x, y=[], plotsData=[], dragPlotter=None, figSize=[15,12], mainAxesRect=[0.3, 0.3, 0.4, 0.4], 
				 dragAxesSize=[0.15, 0.15], pickerRadius=5, showMovement=True, mainPlotKwargs={}):

		if type(x)==str:	
			loadedState = True
			fileName = x
			memberDict = cPickle.load(open(fileName,'rb'))

			x = memberDict['x']
			y = memberDict['y']
			plotsData = memberDict['plotsData']
			dragPlotter = memberDict['dragPlotter']
			figSize = memberDict['figSize']
			mainAxesRect = memberDict['mainAxesRect']
			dragAxesSize = memberDict['dragAxesSize']
			pickerRadius = memberDict['pickerRadius']
			showMovement = memberDict['showMovement']
			mainPlotKwargs = memberDict['mainPlotKwargs']	

			linesData = memberDict['linesData']
			selectedPoints = memberDict['selectedPoints']
			axBounds = memberDict['axBounds']
			addedAxesPointIndex = memberDict['addedAxesPointIndex']
		else:
			loadedState = False
			if len(y)!=len(x):
				raise ValueError("Variables x and y must have the same size")
			if len(x)!=len(allData):
				raise ValueError("Axis 0 of variable plotsData must have same size as x and y")


		self.points = np.array(zip(x, y))
		self.plotsData = plotsData
		self.axesWidth = dragAxesSize[0]
		self.axesHeight = dragAxesSize[1]
		self.dragPlotter = dragPlotter
		self.showMovement = showMovement
		self.mainPlotKwargs = mainPlotKwargs

		fig = plt.figure(figsize=figSize, facecolor='w')
		mainAxes = fig.add_axes(mainAxesRect)
		mainPoints = self.mainPlotter(x, y, mainAxes, mainPlotKwargs)
			
		mainPoints.set_picker(pickerRadius)
		#mainPoints = mainAxes.scatter(x, y, marker='o', picker=pickerRadius)
		mainAxes.margins(0.05)
		
		self.fig = fig
		self.mainAxes = mainAxes
		self.mainPoints = mainPoints

		self.indexSelectedPoint = -1
		self.shouldDraw = False
		self.currentAxes = -1
		self.currentHoverAxes = -1
		self.currentLine = -1
		self.lines = []					# Lines added
		self.selectedPoints = []		# Index of selected points
		self.addedAxes = []				# Axes added around the main plot
		self.addedAxesPointIndex = []	# Index of points related to each axes
		self.isOldPlot = False
		
		mainAxes.figure.canvas.mpl_connect('pick_event', self.onpick)
		mainAxes.figure.canvas.mpl_connect('motion_notify_event', self.mouseMotion)
		fig.canvas.mpl_connect('button_press_event', self.onpress)
		fig.canvas.mpl_connect('draw_event', self.ondraw)
		fig.canvas.mpl_connect('scroll_event', self.onscroll)

		if loadedState==True:
			self.selectedPoints = selectedPoints
			self.addedAxesPointIndex = addedAxesPointIndex
			self.redraw(axBounds, linesData)

		
	def mainPlotter(self, x, y, ax, kwargs):
		mainPoints = ax.scatter(x, y, **kwargs)
		return mainPoints
		
	def dragPlot(self, dataX, dataY, ax):	
		ax.plot(dataX, dataY)
		
	def getClosestPoint(self, points, indexes, x, y):

		hoverPoints = points[indexes]
		d = np.sqrt((x-hoverPoints[:,0])**2 + (y-hoverPoints[:,1])**2)
		hoverPointIndex = indexes[np.argmin(d)]
		
		return hoverPointIndex

	def redraw(self, axBounds, linesData):
		for axBound, selPoint, line in zip(axBounds, self.selectedPoints, linesData):

			dataX, dataY = self.plotsData[selPoint]

			ax1 = self.fig.add_axes(axBound)
			if self.dragPlotter==None:
				self.dragPlot(dataX, dataY, ax1)
			else:
				self.dragPlotter(dataX, dataY, ax1)								

			l = pltLine(line[0], line[1], c='0.7', ls='--', zorder=0)
			l.set_clip_on(False)
			self.mainAxes.add_line(l)	
			self.lines.append(l)
			self.addedAxes.append(ax1)

		#self.shouldDraw = False
		#self.currentLine.set_xdata((linePoint1[0], linePoint2[0]))
		#self.currentLine.set_ydata((linePoint1[1], linePoint2[1]))
		self.currentLine = -1			

		self.fig.canvas.draw()

	def saveState(self, fileName):
		"""
		Save plot mosaic state.
		
		Parameters
		----------
		x : string
			Path to file where the plot mosaic will be saved.
		"""		

		x, y = zip(*self.points)
		plotsData = self.plotsData
		dragPlotter = self.dragPlotter
		figSize = [self.fig.get_figwidth(), self.fig.get_figheight()]
		mainAxesRect = self.mainAxes.bbox._bbox.bounds
		dragAxesSize = [self.axesWidth, self.axesHeight]
		pickerRadius = self.mainPoints.get_pickradius()
		showMovement = self.showMovement
		mainPlotKwargs = self.mainPlotKwargs		

		lines = self.lines
		linesData = [(line.get_xdata(), line.get_ydata()) for line in lines]
		selectedPoints = self.selectedPoints
		addedAxes = self.addedAxes
		axBounds = [ax.bbox._bbox.bounds for ax in addedAxes]
		addedAxesPointIndex = self.addedAxesPointIndex

		memberDict = {
			'x':x, 'y':y, 'plotsData':plotsData, 'dragPlotter':dragPlotter, 
			'figSize':figSize, 'mainAxesRect':mainAxesRect, 'dragAxesSize':dragAxesSize, 
			'pickerRadius':pickerRadius, 'showMovement':showMovement, 
			'mainPlotKwargs':mainPlotKwargs, 'linesData':linesData, 'selectedPoints':selectedPoints,
			'axBounds':axBounds, 'addedAxesPointIndex':addedAxesPointIndex}	

		cPickle.dump(memberDict, open(fileName,'wb'), 2)						

	def loadState(fileName):

		memberDict = cPickle.load(open(fileName,'rb'))

		x = memberDict['x']
		y = memberDict['y']
		plotsData = memberDict['plotsData']
		dragPlotter = memberDict['dragPlotter']
		figSize = memberDict['figSize']
		mainAxesRect = memberDict['mainAxesRect']
		dragAxesSize = memberDict['dragAxesSize']
		pickerRadius = memberDict['pickerRadius']
		showMovement = memberDict['showMovement']
		mainPlotKwargs = memberDict['mainPlotKwargs']	

		linesData = memberDict['linesData']
		selectedPoints = memberDict['selectedPoints']
		axBounds = memberDict['axBounds']
		addedAxesPointIndex = memberDict['addedAxesPointIndex']

		dragInstance = self.__init__(x, y, plotsData, dragPlotter, figSize, mainAxesRect, 
					 dragAxesSize, pickerRadius, showMovement, mainPlotKwargs)

		dragInstance.selectedPoints = selectedPoints
		dragInstance.addedAxesPointIndex = addedAxesPointIndex
		dragInstance.redraw(axBounds, linesData)

		return dragInstance	
		
	def onpick(self, event):
		detectedPoints = event.ind
		#print('Picked point: ', selectedPoints)
		hoverPointIndex = self.getClosestPoint(self.points, detectedPoints, event.mouseevent.xdata, event.mouseevent.ydata)
		self.indexSelectedPoint = hoverPointIndex
		self.shouldDraw = True
		self.selectedPoints.append(self.indexSelectedPoint)
		self.currentAxes = self.currentHoverAxes
		self.currentHoverAxes = -1
		self.isOldPlot = False
		
		xDisplay, yDisplay, W, H = self.currentAxes.get_window_extent().bounds
		linePoint1 = (self.points[self.indexSelectedPoint])
		linePoint2 = self.mainAxes.transData.inverted().transform((xDisplay+W/2., yDisplay+H/2.))

		l = pltLine((linePoint1[0], linePoint2[0]), (linePoint1[1], linePoint2[1]), c='0.7', ls='--', zorder=0)
		l.set_clip_on(False)
		self.currentLine = l
		self.mainAxes.add_line(l)			

		
	def onpress(self, event):
		if event.inaxes!=self.mainAxes:
			#print('Picked point: %d, %d'%(event.x, event.y))
			if self.shouldDraw:
				mainAxes = self.mainAxes
				dataX, dataY = self.plotsData[self.indexSelectedPoint]
				
				xDisplay, yDisplay  = event.x, event.y
				x, y = self.fig.transFigure.inverted().transform((xDisplay, yDisplay))
				
				ax1 = self.currentAxes
				_, _, WDisplay, HDisplay = ax1.get_window_extent().bounds
				W, H = self.fig.transFigure.inverted().transform((WDisplay, HDisplay))
				ax1.set_position([x, y, W, H])
				#ax1 = self.fig.add_axes([x, y, self.axesWidth, self.axesHeight])
				#if self.dragPlotter==None:
				#	self.dragPlot(dataX, dataY, ax1)
				#else:
				#	self.dragPlotter(dataX, dataY, ax1)
					
					
				ax1.figure.canvas.draw()		
				self.shouldDraw = False
				
				#self.currentLine.remove()
				#self.currentLine = -1
				
				xDisplay, yDisplay, W, H = ax1.get_window_extent().bounds
				linePoint1 = (self.points[self.indexSelectedPoint])
				linePoint2 = mainAxes.transData.inverted().transform((xDisplay+W/2., yDisplay+H/2.))
				#print linePoint1, linePoint2
				self.currentLine.set_xdata((linePoint1[0], linePoint2[0]))
				self.currentLine.set_ydata((linePoint1[1], linePoint2[1]))
				#l = pltLine((linePoint1[0], linePoint2[0]), (linePoint1[1], linePoint2[1]), c='0.7', ls='--', zorder=0)
				#l.set_clip_on(False)
				#mainAxes.add_line(l)
				if self.isOldPlot==False:
					self.lines.append(self.currentLine)
					self.addedAxes.append(ax1)
					self.addedAxesPointIndex.append(self.indexSelectedPoint)
				mainAxes.figure.canvas.draw()
				self.currentLine = -1
				
			else:
				xDisplay, yDisplay  = event.x, event.y
				for axIndex, ax in enumerate(self.addedAxes):
					if event.inaxes==ax:
						self.shouldDraw = True
						self.currentAxes = ax
						self.currentLine = self.lines[axIndex]
						self.indexSelectedPoint = self.addedAxesPointIndex[axIndex]
						self.isOldPlot = True
						break				
				
				
	def mouseMotion(self, event):
		#if event.inaxes!=mainAxes: return
		#print('Hover point: %f, %f'%(event.xdata, event.ydata))
		contains, attDict = self.mainPoints.contains(event)
		mainAxes = self.mainAxes
		if self.shouldDraw:
			if not self.showMovement:
				self.currentAxes.cla()	
			xDisplay, yDisplay  = event.x, event.y
			x, y = self.fig.transFigure.inverted().transform((xDisplay, yDisplay))
			_, _, WDisplay, HDisplay = self.currentAxes.get_window_extent().bounds
			W, H = self.fig.transFigure.inverted().transform((WDisplay, HDisplay))
			self.currentAxes.set_position([x, y, W, H])

			if self.currentLine!=-1:
				xDisplay, yDisplay, W, H = self.currentAxes.get_window_extent().bounds
				linePoint1 = (self.points[self.indexSelectedPoint])
				linePoint2 = mainAxes.transData.inverted().transform((xDisplay+W/2., yDisplay+H/2.))
				self.currentLine.set_xdata((linePoint1[0], linePoint2[0]))
				self.currentLine.set_ydata((linePoint1[1], linePoint2[1]))			

			mainAxes.figure.canvas.draw()	
		else:
			if (contains==True):
				if self.currentHoverAxes!=-1:
					self.currentHoverAxes.remove()
				hoverPointsIndexes = attDict['ind']
				
				hoverPointIndex = self.getClosestPoint(self.points, hoverPointsIndexes, event.xdata, event.ydata)
								
				dataX, dataY = self.plotsData[hoverPointIndex]

				xDisplay, yDisplay  = event.x, event.y
				x, y = self.fig.transFigure.inverted().transform((xDisplay, yDisplay))
				ax1 = self.fig.add_axes([x+0.005, y+0.005, 0.15, 0.15])
				if self.dragPlotter==None:
					self.dragPlot(dataX, dataY, ax1)
				else:
					self.dragPlotter(dataX, dataY, ax1)					
				ax1.figure.canvas.draw()		
				self.currentHoverAxes = ax1
			elif (contains==False) and (self.currentHoverAxes!=-1):
				self.currentHoverAxes.remove()
				mainAxes.figure.canvas.draw()
				self.currentHoverAxes = -1
				
	def ondraw(self, event):			
		lines = self.lines
		selectedPoints = self.selectedPoints
		addedAxes = self.addedAxes
		
		for line, pointIndex, ax in zip(lines, selectedPoints, addedAxes):			
			xDisplay, yDisplay, W, H = ax.get_window_extent().bounds
			linePoint1 = (self.points[pointIndex])
			linePoint2 = self.mainAxes.transData.inverted().transform((xDisplay+W/2., yDisplay+H/2.))
			line.set_xdata((linePoint1[0], linePoint2[0]))
			line.set_ydata((linePoint1[1], linePoint2[1]))
			#self.mainAxes.figure.canvas.draw()	

	def onscroll(self, event):
		ax1 = self.currentAxes
		xDisplay, yDisplay, WDisplay, HDisplay = ax1.get_window_extent().bounds
		x, y = self.fig.transFigure.inverted().transform((xDisplay, yDisplay))
		scrollChange = event.step
		resizeFactor = 0.1*scrollChange
		Wold, Hold = self.fig.transFigure.inverted().transform((WDisplay, HDisplay))
		Wnew = Wold + Wold*resizeFactor
		Hnew = Hold + Hold*resizeFactor
		ax1.set_position([x, y, Wnew, Hnew])
		self.fig.canvas.draw()
					

# Example usage
if __name__=='__main__':	
	# Function used for creating the smaller plots	
	def plotFunc(x, y, ax):
		ax.plot(x, y, 'o')


	points = np.random.rand(10, 2)
	x, y = zip(*points)
	allData = np.random.rand(10, 2, 1000)
	colors = np.random.rand(10)

	mainPlotKwargs = {'marker':'^', 'c':colors, 'cmap':'hot'}
	dragInstance = PlotMosaic(x, y, allData, dragPlotter=plotFunc, mainPlotKwargs=mainPlotKwargs)


	# You can save the mosaic for latter use, as shown below
	# dragInstance.saveState('mosaic.dat')
	# dragInstance = DraggablePlots('mosaic.dat')





