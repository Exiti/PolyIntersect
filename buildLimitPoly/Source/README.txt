preproccessAPI.py contains the API for processing a file with building_limits and height_plateaus into split building_limits with elevation property.

It can be added to a new project with the line: from preproccessAPI import findBuildPolygons

It is called as such: findBuildPolygons('absoluteInputPath', 'absoluteOutputPath')
It can also be called with relative paths, but they will be relative to where you are launching script from, not from script location on disk

main.py contains three separate calls that can be run as is, putting output in TestDocs folder in the projects Source folder.
They run the following data:
	first call - JSON data provided by SpaceMaker
	second call - JSON data with multiple building_limit polygons as well as gap in coverage by height_limit polygons
	third call - JSON data that in addition to the conditions of the second call, also has two building_limit polygons overlapping each other