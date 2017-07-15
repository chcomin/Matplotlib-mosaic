# Matplotlib-mosaic

Create plot mosaic. Example:


The class has two interfaces. The zero-state interface is used for creating a new plot mosaic. The load-state interface is used for loading a previously saved mosaic.

## Example usage

Creating the plot mosaic from scratch (zero-state interface)

```python

# Function used for creating the smaller plots	
def plotFunc(data, ax):
	x = data[0]
	y = data[1]
	ax.plot(x, y, 'o', ms=3)


points = np.random.rand(10, 2)				# Points in the main axes
x, y = zip(*points)
allData = np.random.rand(10, 2, 100)			# Data corresponding to each point in the main axes
colors = np.random.rand(10)				# Color of each point

mainPlotKwargs = {'marker':'^', 'c':colors, 'cmap':'hot'}
mosaic = PlotMosaic(x, y, allData, dragPlotter=plotFunc, mainPlotKwargs=mainPlotKwargs)


# You can save the mosaic for latter use, as shown below
mosaic.saveState('mosaic.dat')

```

Loading a previously saved mosaic

```

mosaic = PlotMosaic('mosaic.dat')

```
