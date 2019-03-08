import json
from math import pi, cos, radians
from shapely.geometry import Polygon
from matplotlib import pyplot as plt
from math import isclose
from builtins import int

ERROR_TOLERANCE = 0.001 # 0.1%, one thousands as error tolerance

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
