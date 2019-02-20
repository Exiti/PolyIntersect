
from preproccessAPI import findBuildPolygons

#Constants
DEFAULT_IN_PATH = "TestDocs/example.txt"
DEFAULT_OUT_PATH = "TestDocs/output.txt"
UNIT_TEST1_IN_PATH = "TestDocs/test.txt"
UNIT_TEST1_OUT_PATH = "TestDocs/testResult.txt"
TEST_OVERLAP_IN_PATH = "TestDocs/testOverlap.txt"
TEST_OVERLAP_OUT_PATH = "TestDocs/resultsOverlap.txt"

# Main declaration
def main():

    findBuildPolygons(DEFAULT_IN_PATH, DEFAULT_OUT_PATH) #main call

    #Unit test tests handling of multiple build zones and gap in height_limit zones, output JSON file may need to be manually verified for sanity
    #findBuildPolygons(UNIT_TEST1_IN_PATH, UNIT_TEST1_OUT_PATH) #Unit test call
    #Unit test that checks handling of overlapping building_limit zones
    #findBuildPolygons(TEST_OVERLAP_IN_PATH, TEST_OVERLAP_OUT_PATH)

if __name__ == "__main__":
    main()