import json
from math import pi, cos, radians
from shapely.geometry import Polygon
from matplotlib import pyplot as plt
from math import isclose
from builtins import int

ERROR_TOLERANCE = 0.001 # 0.1%, one thousands as error tolerance

def callWithAbsolutePath(pathString):
    findBuildPolygons(pathString)

def callWithRelativePath(pathString):
    # Create absolute path from relative path
    return True

def findBuildPolygons(inputPath, outputPath):
    """Takes a file with JSON data as input and splits building_limits into smaller polygons based on height_limits
    And writes to output file, overwriting if there already is a file in that location

    Args:
        inputPath: File with JSON data
        outputPath: File to write processed data to
    Returns:
        None
    Raises:
        None
    """

    with open(inputPath, 'r') as file:
        try:
            indata = json.load(file)

            numBuildLimitZones = len(indata['building_limits']['features'])
            numHeightLimitZones = len(indata['height_plateaus']['features'])

            sumBuildLimitZonesArea = 0 # Total sum of building_limit zones in input
            sumSplitArea = 0 # Total sum of split building_limits to be output
            numSplitAreas = 0 # Total number of split building_limits

            # Worst case is that every building_limit zone intersects with every height_limit zone, and we need to save coordinates and height for each combination
            splitBuildLimitsList = [[None] * 2 for i in range(numHeightLimitZones*numBuildLimitZones)] # Holds the merged list of coordinates and height for each split zone

            # Fetches the list of coordinates that outline the building_limits zone
            for bZones in range(numBuildLimitZones):
                # get next building_limit zone
                buildLimitZone = indata['building_limits']['features'][bZones]
                if not validPolygon(buildLimitZone['geometry']['coordinates'][0]): # Check that build_limit zone contains a valid polygon before creating Polygon object
                    print(f'building_limit polygon with index {bZones} is not valid')
                    continue # Current polygon is not valid, continue to next building_limit polygon

                buildLimitPolygon = Polygon(buildLimitZone['geometry']['coordinates'][0])# Create a Polygon object from current building_limit zone
                buildLimitRemainingPoly = buildLimitPolygon # holds the 'remains' of building_limit polygon in case it is not fully covered by height_limit polygons
                sumBuildLimitZonesArea += buildLimitPolygon.area # sum all the build_limit zones to verify that when we have created new split zones the entire area is covered

                for hZones in range(numHeightLimitZones):
                    # get next height_limit zone and create a polygon of it
                    heightLimitZone = indata['height_plateaus']['features'][hZones]
                    if not validPolygon(heightLimitZone['geometry']['coordinates'][0]):
                        print(f'height_limit polygon with index {hZones} is not valid')
                        continue # Current polygon is not valid, continue to next height_limit polygon

                    heightLimitZonePoly = Polygon(heightLimitZone['geometry']['coordinates'][0])
                    # create new split building limit polygon from intersection of building_limit polygon and current height_limit polygon
                    splitBuildLimitPolygon = buildLimitPolygon.intersection(heightLimitZonePoly) # Get intersection of build_limit and height_limit zones
                    splitBuildLimitHeight = heightLimitZone['properties']['elevation'] # Get elevation of height_limit zone

                    # Process the split building limit polygon to create what we need to verify and save output
                    if 0 < splitBuildLimitPolygon.area: # if area is 0 then the build_limit zone does not intersect with the height_limit zone
                        buildLimitRemainingPoly = buildLimitRemainingPoly.difference(splitBuildLimitPolygon)
                        sumSplitArea += splitBuildLimitPolygon.area # Add area of new split build limit polygon to total, should add up to area of original building_limit

                        splitBuildLimitsList[numSplitAreas][0] = createCoordinateListFromPolygon(splitBuildLimitPolygon) # Save coordinate data to new split building_limit zone
                        splitBuildLimitsList[numSplitAreas][1] = splitBuildLimitHeight # Copy height limit from current height_limit zone into the split building_limit zone
                        numSplitAreas += 1 # Increment as last step since indexing starts at 0


                # if not the entire area of building_limit has been claimed by a split zone, then award it to the adjacent one with largest height
                if (sumBuildLimitZonesArea * ERROR_TOLERANCE) < buildLimitRemainingPoly.area: # remaining area is more than ERROR_TOLERANCE of total building_limit area
                    largestHeight = -100 # Save the height of the polygon with largest height
                    highestZone = -1 # Save the index of the polygon with the largest height
                    secondHeighest = -1 # Save the index of the second largest in case we accidentally create a MultiPolygon
                    for zone in range(numSplitAreas):
                        # zone is adjacent and height is larger than previous adjacent zone
                        if buildLimitRemainingPoly.intersects(Polygon(splitBuildLimitsList[zone][0])) and (splitBuildLimitsList[zone][1] > largestHeight):
                            largestHeight = splitBuildLimitsList[zone][1]
                            if -1 < highestZone:
                                secondHeighest + highestZone # if a new
                            highestZone = zone

                    # when adjacent polygon with largest height has been found, join remains to it.
                    if -1 < highestZone: # No adjacent zone was found
                        try:
                            tempPoly = Polygon(splitBuildLimitsList[highestZone][0])
                            tempPoly = tempPoly.union(buildLimitRemainingPoly)
                            tempList = createCoordinateListFromPolygon(tempPoly)
                            sumSplitArea += buildLimitRemainingPoly.area
                            splitBuildLimitsList[highestZone][0] = tempList
                        except TypeError:
                            print('Selected zone could not be merged into single polygon, attempting to select other zone')
                            try:
                                tempPoly = Polygon(splitBuildLimitsList[secondHeighest][0])
                                tempPoly = tempPoly.union(buildLimitRemainingPoly)
                                tempList = createCoordinateListFromPolygon(tempPoly)
                                sumSplitArea += buildLimitRemainingPoly.area
                                splitBuildLimitsList[secondHeighest][0] = tempList
                            except TypeError:
                                print('Could not find any zone to merge with remains, leave it unoccupied')
                                #sumBuildLimitZonesArea -= buildLimitRemainingPoly.area # The remaining area could not be claimed by any split zone
                    else:
                        print('Remaining area in building_limit since no adjacent split building_limit was found')

                # remaining area is negative or there is overlap on split building_limits
                if 0 > buildLimitRemainingPoly.area or sumSplitArea > sumBuildLimitZonesArea:
                    # Compare the split building_limits and remove overlapping area from zones with lowest height property
                    for zone in range(numSplitAreas):
                        #select one split area, and then loop over every other and remove overlap when the other zone has higher height property
                        for compareZone in range(zone+1, numSplitAreas):
                            if splitBuildLimitsList[zone][1] < splitBuildLimitsList[compareZone][1]:
                                # create a polygon that excludes the overlap of the two polygons
                                try:
                                    prevArea = Polygon(splitBuildLimitsList[zone][0]).area
                                    tempPoly = Polygon(splitBuildLimitsList[zone][0]).difference(Polygon(splitBuildLimitsList[compareZone][0]))
                                    tempList = createCoordinateListFromPolygon(tempPoly)
                                    sumSplitArea -= (prevArea - tempPoly.area) # Remove overlapped area from sum, area should only be counted once
                                    splitBuildLimitsList[zone][0] = tempList
                                except:
                                    print('Could not remove overlap from zone')


            # rel_tol is 0.1% of total area, this might be a bit to high but it was selected to have some room in case of floating point rounding errors
            if isclose(sumBuildLimitZonesArea, sumSplitArea, rel_tol=(sumBuildLimitZonesArea * ERROR_TOLERANCE)):
                outData = indata
                # Build new JSON keys for split building_limits
                outData['split_building_limits'] = {}
                outData['split_building_limits']['features'] = [None] * numSplitAreas
                for zone in range(numSplitAreas):
                    # Continue building JSON keys for each split building_limits
                    outData['split_building_limits']['features'][zone] = {}
                    outData['split_building_limits']['features'][zone]['geometry'] = {}
                    outData['split_building_limits']['features'][zone]['properties'] = {}

                    # Create final keys and add values
                    outData['split_building_limits']['features'][zone]['geometry']['coordinates'] = splitBuildLimitsList[zone][0] # Get list of coordinates from list and add to output JSON
                    outData['split_building_limits']['features'][zone]['properties']['elevation'] = splitBuildLimitsList[zone][1] # Get height property for this split building_limit

                with open(outputPath, 'w') as outFile:
                    json.dump(outData, outFile, indent=2)
                    print(f'Preprocessor step complete, output can be found at: {outputPath}')
            else:
                print('Difference in covered area is too large, could not conclusively create split building limit zones')

        except json.JSONDecodeError:
            print('Error while reading json file')
        except FileNotFoundError:
            print(f'The JSON file was not found at the given path: \n{inputPath}')
        except NameError:
            print('JSON file not indexed with correct keys')
        except ValueError:
            print('Could not create split building limits based on provided JSON file')
        except KeyError:
            print('JSON input file does not use the correct keys for key:value pairs')

def createCoordinateListFromPolygon(poly):
    """Takes a Polygon object as input and returns a list of [lat, lon] coordinates with length as amount of vertices"""
    if 'Polygon' == poly.geom_type:
        lat, lon = poly.exterior.xy # Extract lat and lon coordinates from Polygon object to lists
        return mergeListFromCoordinateLists(lat, lon)
    elif 'MultiPolygon' == poly.geom_type:
        raise TypeError('created a MultiPolygon')
    else:
        raise TypeError('created a geometry shape that is not Polygon')

def mergeListFromCoordinateLists(lat, lon):
    """ Merge lat and lon into one list"""
    mergedList = [[None] * 2 for i in range(len(lat))]

    for i in range(len(lat)):
        mergedList[i][0] = lat[i]
        mergedList[i][1] = lon[i]
    return mergedList

def errorCheck(condition):
    """Check that condition is fulfilled and raises ValueError if it isn't

    Args:
        condition: the condition to be checked

    """
    if not condition:
        raise ValueError
        return False
    else:
        return True

def errorN(condition, errorString, value):
    """Check that condition is fulfilled and print errorString and value if it isn't

    Args:
        condition: the condition to be checked
        errorString: the message that will be printed if condition is not fulfilled

    """
    if not condition:
        print(errorString + str(value))
        return True
    else:
        return False

def validPolygon(polygon):
    if lastPointIsFirstPoint(polygon):
        for i in range(len(polygon)-1):
            if validType(polygon[i]):
                if not validPosition(polygon[i]):
                    print(f'Vertice in polygon is not a valid GPS coordinate: {polygon[i]}')
                    raise ValueError
            else:
                print(f'Vertice in polygon is of the wrong type: {polygon[i]}')
                raise TypeError
        return True
    else:
        print('Polygon not complete, it is not possible to draw a continuous polygon from provided vertices')
        raise ValueError

def latitudeValid(pointLatitude):
    if 90 < pointLatitude:
        print(f'Vertice above maximum value of GPS latitude: {pointLatitude}')
        return False
    elif -90 > pointLatitude:
        print(f'Vertice below minimum value of GPS latitude: {pointLatitude}')
        return False
    else:
        return True

def longitudeValid(pointLongitude):
    if 180 < pointLongitude:
        print(f'Vertice above maximum value of GPS longitude: {pointLongitude}')
        return False
    elif -180 > pointLongitude:
        print(f'Vertice below minimum value of GPS longitude: {pointLongitude}')
        return False
    else:
        return True

def validPosition(point):
    if latitudeValid(point[0]) and longitudeValid(point[1]):
        return True
    else:
        return False

def validType(point):
    if (isinstance(point[0], float) and isinstance(point[1], float)) or (isinstance(point[0], int) and isinstance(point[1], int)):
        return True
    else:
        return False

def lastPointIsFirstPoint(polygon):
    """Checks that the last point of a polygon is the same as the first point """
    lastIndex = len(polygon)-1 # finds the index of last point
    return (polygon[0][0] == polygon[lastIndex][0]) and (polygon[0][1] == polygon[lastIndex][1])

def debugPlot(splitBuildLimitsList, indata):
    """Used to plot Polygons to visually verify intended behavior"""
    #xb, yb = buildLimitPolygon.exterior.xy
    x0, y0 = Polygon(splitBuildLimitsList[0][0]).exterior.xy
    x1, y1 = Polygon(splitBuildLimitsList[1][0]).exterior.xy
    x2, y2 = Polygon(splitBuildLimitsList[2][0]).exterior.xy
    x3, y3 = Polygon(splitBuildLimitsList[3][0]).exterior.xy
    x4, y4 = Polygon(splitBuildLimitsList[4][0]).exterior.xy
    #xGeom, yGeom = Polygon(indata['height_plateaus']['features'][2]['geometry']['coordinates'][0]).exterior.xy

    fig = plt.figure(1, figsize=(5,5), dpi=90)
    ax = fig.add_subplot(111)
    #ax.plot(xb, yb, color='#6699cc', alpha=0.7, linewidth=3, solid_capstyle='round', zorder=1)
    ax.plot(x0, y0, color='#0000FF', alpha=0.7, linewidth=1, solid_capstyle='round', zorder=2)
    ax.plot(x1, y1, color='#FF0000', alpha=0.7, linewidth=1, solid_capstyle='round', zorder=3)
    ax.plot(x2, y2, color='#00FF00', alpha=0.7, linewidth=1, solid_capstyle='round', zorder=4)
    ax.plot(x3, y3, color='#FFFF00', alpha=0.7, linewidth=1, solid_capstyle='round', zorder=5)
    ax.plot(x4, y4, color='#00FFFF', alpha=0.7, linewidth=1, solid_capstyle='round', zorder=6)
    #ax.plot(xGeom, yGeom, color='#6699cc', alpha=0.3, linewidth=3, solid_capstyle='round', zorder=1)
    ax.set_title('Polygon')
    plt.show()

def calcLine(pointA, pointB):
    """Calculate coefficient and offset for the line intersecting pointA and pointB.

    Args:
        pointA: the first point.
        pointB: the second point.
    Returns:
        array in format [slope, intercept]
    Raises:
        TypeError: if either point is not an array with two float values
        ValueError: latitude or longitude of a point is invalid.

    """
    if pointA[0] <= pointB[0]:
        leftPoint = pointA
        rightPoint = pointB
    else:
        leftPoint = pointB
        rightPoint = pointA

    xRun = rightPoint[0] - leftPoint[0]
    yRise = rightPoint[1] - leftPoint[1]
    simpleSlope = yRise / xRun
    simpleIntercept = ( (leftPoint[1] - simpleSlope*leftPoint[0]) + (leftPoint[1] - simpleSlope*leftPoint[0]) ) / 2
    print(simpleSlope, simpleIntercept)
    # Gives the correct formula

    if validType(pointA) and validType(pointB):
        if validPosition(pointA) and validPosition(pointB):
            if pointA[0] == pointB[0]:
                #Do special equation if line is vertical
                lineSlope = 1 #vertical line does not have a slope
                lineIntercept = ((pointA[1] - lineSlope*pointA[0]) + (pointB[1] - lineSlope*pointB[0])) / 2 # take average of intercept calculated from both points since rounding errors might change results otherwise)
            else:
                lineSlope = (pointB[1] - pointA[1]) / (pointB[0] - pointA[0])
                lineIntercept = ((pointA[1] - lineSlope*pointA[0]) + (pointB[1] - lineSlope*pointB[0])) / 2 # take average of intercept calculated from both points since rounding errors might change results otherwise
                return [lineSlope, lineIntercept]
        else:
            raise ValueError
    else:
        raise TypeError

def findBoarderAndIntersectPoint(polygon1, polygon2, buildingPointA, buildingPointB):
    sharedPoint1 = [None, None]
    sharedPoint2 = [None, None]

    if validPolygon(polygon1) and validPolygon(polygon2):

        # Try to handle irregular shaped polygons(might not have the same amount of points)
        if len(polygon1) <= len(polygon2):
            polygonBig = polygon1
            maxLenBig = len(polygon1)-1
            polygonSmall = polygon2
            maxLenSmall = len(polygon2)-1
        else:
            polygonBig = polygon2
            maxLenBig = len(polygon2)-1
            polygonSmall = polygon1
            maxLenSmall = len(polygon1)-1


        for i in range(0, maxLenBig):
            # if two points are not found in the same line then look for two new points
            firstPointFound = False
            secondPointFound = False
            ## Make lines from the polygon with most points
            lineEquation = calcLine(polygonBig[i], polygonBig[i+1])
            print(lineEquation)

            for j in range(0, maxLenSmall):
                # Check if a point is on the line
                if pointIsOnLine(lineEquation, polygonSmall[j]):
                    if not firstPointFound:
                        firstPointFound = True
                        sharedPoint1 = polygonSmall[j]
                    elif not secondPointFound:
                        secondPointFound = True
                        sharedPoint2 = polygonSmall[j]

                if firstPointFound and secondPointFound:
                    # if both points were found then we have likely found our shared line
                    # see if there is an intersection with buildSite points
                    newPoint = findIntersection(sharedPoint1, sharedPoint2, buildingPointA, buildingPointB)
                    # new point has to be on line between sharedPoint1 and sharedPoint2
                    if ( (sharedPoint1[0] >= newPoint[0] and sharedPoint2[0] <= newPoint[0]) or (sharedPoint1[0] <= newPoint[0] and sharedPoint2[0] >= newPoint[0]) ) and ( (sharedPoint1[1] >= newPoint[1] and sharedPoint2[1] <= newPoint[1]) or (sharedPoint1[1] <= newPoint[1] and sharedPoint2[1] >= newPoint[1]) ):
                        print(newPoint)
                        return newPoint
                    else:
                        sharedPoint1 = [[None], [None]]
                        continue # If point found is not correctly on the line, attempt to find next line(polygons might share several sides)
    sharedPoint1 = [[None], [None]]
    sharedPoint2 = [[None], [None]]

def pointIsOnLine(lineSlopeAndIntercept, point):
    # return y == kx + m
    return point[1] == (lineSlopeAndIntercept[0] * point[0]) + lineSlopeAndIntercept[1]

def findIntersection(heightPointA, heightPointB, buildPointA, buildPointB):
    # assumes coordinates in form [lat, long]
    intersectionCoordinates = [10.71696696494792, 59.944454785331715]

    heightLine = calcLine(heightPointA, heightPointB)
    buildLine = calcLine(buildPointA, buildPointB)

    # to find the latitude value where both slope-intercept form line equations have the the same longitude value
    # x = (intercept1 + intercept2) / (slope1 - slope2)
    intersectionCoordinates[0] = (heightLine[1] + buildLine[1]) / (heightLine[0] - buildLine[0])
    # to find intersection longitude value, input found latitude in either line equation
    intersectionCoordinates[1] = ( heightLine[0] * intersectionCoordinates[0] ) + heightLine[1]

    return intersectionCoordinates

def isPointInside(buildPoint, heightLimitPoly):

    if(lastPointIsFirstPoint(heightLimitPoly)):
        #polygonArea = calcHeightLimitArea(heightLimitPoly)
        polygon = Polygon(heightLimitPoly)
        polygonArea = polygon.area
        pointPolyTotArea = 0 # holds the sum of all the triangles between the point and a pair of point in the heightLimitPolygon
        for i in range(0, len(heightLimitPoly)-1):
            pointPolyTotArea += calcTriangleArea(buildPoint, heightLimitPoly[i], heightLimitPoly[i+1])

        print(polygonArea)
        print(pointPolyTotArea)
        return polygonArea == pointPolyTotArea
    else:
        raise ValueError('height_plateau polygon is not a continuous polygon')

def calcTriangleArea(pointA, pointB, pointC):
    """| (Ax(By−Cy)+Bx(Cy−Ay)+Cx(Ay−By)) / 2 |"""
    return abs( ( pointA[0]*(pointB[1]-pointC[1]) + (pointB[0]*(pointC[1]-pointA[1])) + pointC[0]*(pointA[1]-pointB[1]) ) / 2 )

def calcHeightLimitArea(heightLimitArea):
    x = [None] * len(heightLimitArea)
    y = [None] * len(heightLimitArea)

    for i in range(0, len(heightLimitArea)):
        x[i], y[i] = reproject(heightLimitArea[0], heightLimitArea[1])
    # x and y should now contain reprojected values for each point in heightLimitArea
    return areaOfPolygon(x, y)

def reproject(latitude, longitude):
    """Returns the x & y coordinates in meters using a sinusoidal projection"""
    earth_radius = 6371009 # in meters
    lat_dist = pi * earth_radius / 180.0

    y = [lat * lat_dist for lat in latitude]
    x = [long * lat_dist * cos(radians(lat))
                for lat, long in zip(latitude, longitude)]
    return x, y

def areaOfPolygon(x, y):
    """Calculates the area of an an arbitrary polygon given its verticies."""
    area = 0.0
    for i in range (-1, len(x)-1):
        area += x[i] * (y[i+1] - y[i-1]) # area += latitudefPoint * (longitudeOfNextPoint - longitudeOfPrevPoint)
    return abs(area) / 2.0
