import json

def callWithAbsolutePath(pathString):
    findBuildPolygons(pathString)

def callWithRelativePath(pathString):
    # Create absolute path from relative path
    return True

def findBuildPolygons(pathString):

    with open(pathString, 'r') as jsonfile:
        data = jsonfile.read()

    dictObj = json.loads(data)

    json.dumps(dictObj, indent=4)



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
    if validType(pointA) and validType(pointB):
        if validPosition(pointA) and validPosition(pointB):
            lineSlope = (pointA[1] - pointB[1]) / (pointA[0] - pointB[0])
            lineIntercept = pointA[1] - 2*pointA[0]
            return [lineSlope, lineIntercept]
        else:
            return ValueError
    else:
        return TypeError

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

def isPointInside(buildPoint, heightLimitArea):
    return True

def errorCheck(condition, errorString):
    """Check that condition is fulfilled and print errorString if it isn't

    Args:
        condition: the condition to be checked
        errorString: the message that will be printed if condition is not fulfilled

    """
    if not condition:
        print(errorString)
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
