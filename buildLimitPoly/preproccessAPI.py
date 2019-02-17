import json
from math import pi, cos, radians
from shapely.geometry import Polygon
from point_in_polygon import wn_PnPoly # open source software from softsurfer.com used to perform winding number test for point in polygon


def callWithAbsolutePath(pathString):
    findBuildPolygons(pathString)

def callWithRelativePath(pathString):
    # Create absolute path from relative path
    return True

def findBuildPolygons(pathString):

    with open(pathString, 'r') as file:
        try:
            indata = json.load(file)
            print(indata, '\n')
            numLimitZones = len(indata['height_plateaus']['features'])
            numOfBuildPoints = len(indata['building_limits']['features'][0]['geometry']['coordinates']) - 1
            pointZoneDistribution = [None] * numOfBuildPoints

            buildPoint = indata['building_limits']['features'][0]['geometry']['coordinates'][0]
            for buildPointIndex in range(0, numOfBuildPoints):
                for i in range(0, numLimitZones):
                    heightLimitPolygon = indata['height_plateaus']['features'][0]['geometry']['coordinates'][i]

                    if 0 != wn_PnPoly(buildPoint[buildPointIndex], heightLimitPolygon): # wn_PnPoly returns 0 only if point is outside polygon
                        pointZoneDistribution[buildPointIndex] = i

                if None == pointZoneDistribution[buildPointIndex]:
                    raise ValueError(f'This point was not inside any height_limit polygon: {buildPoint[buildPointIndex]}')

            #TODO Remove debug print
            #print(indata['height_plateaus']['features']) # this is a collection of all height_limit geometry zones
            #print(indata['height_plateaus']['features'][0]['geometry']['coordinates'][0]) # This is a collection of all point of a height_limit zone
            #print(indata['height_plateaus']['features'][0]['geometry']['coordinates'][0][0]) # This is a height_limit point
        except json.JSONDecodeError:
            print('error while reading json file')
        except FileNotFoundError:
            print(f'The JSON file was not found at the given path: \n{pathString}')
        except NameError:
            print('JSON file not indexed with correct keys')

    #allColumns = fileContents[0].keys()



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

def errorCheck(condition, errorString):
    """Check that condition is fulfilled and print errorString if it isn't

    Args:
        condition: the condition to be checked
        errorString: the message that will be printed if condition is not fulfilled

    """
    if not condition:
        raise ValueError(errorString)
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
        for i in range(0, len(polygon)-1):
            if validType(polygon[i]):
                if not validPosition(polygon[i]):
                    raise ValueError('a point in polygon is not a valid GPS coordinate')
            else:
                raise ValueError('a point in polygon is of the wrong type')
    else:
        raise ValueError('Polygon not continuous')

def latitudeValid(pointLatitude):
    if errorN(90 >= pointLatitude, "Point above maximum value of GPS latitude: ", pointLatitude):
        return False
    elif errorN(-90 <= pointLatitude, "Point below minimum value of GPS latitude: ", pointLatitude):
        return False
    else:
        return True

def longitudeValid(pointLongitude):
    if errorN(180 >= pointLongitude, "Point above maximum value of GPS longitude: ", pointLongitude):
        return False
    elif errorN(-180 <= pointLongitude, "Point below minimum value of GPS longitude: ", pointLongitude):
        return False
    else:
        return True

def validPosition(point):
    if latitudeValid(point[0]) and longitudeValid(point[1]):
        return True
    else:
        return False

def validType(point):
    if isinstance(point[0], float) and isinstance(point[1], float):
        return True
    else:
        return False

def lastPointIsFirstPoint(polygon):
    """Checks that the last point of a polygon is the same as the first point """
    lastIndex = len(polygon)-1 # finds the index of last point
    return (polygon[0][0] == polygon[lastIndex][0]) and (polygon[0][1] == polygon[lastIndex][1])
