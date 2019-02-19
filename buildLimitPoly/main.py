
from preproccessAPI import findBuildPolygons

#Constants
DEFAULT_IN_PATH = "TestDocs/example.txt"
DEFAULT_OUT_PATH = "TestDocs/output.txt"
UNIT_TEST_IN_PATH = "TestDocs/test.txt"
UNIT_TEST_OUT_PATH = "TestDocs/testResult.txt"

# Main declaration
def main():
    findBuildPolygons(DEFAULT_IN_PATH, DEFAULT_OUT_PATH) #main call

    #Unit test tests handling of multiple build zones and gap in height_limit zones, output JSON file may need to be manually verified for sanity
    #findBuildPolygons(UNIT_TEST_IN_PATH, UNIT_TEST_OUT_PATH) #Unit test call

if __name__ == "__main__":
    main()