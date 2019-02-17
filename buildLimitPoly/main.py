
from preproccessAPI import findBuildPolygons

#import tkinter
#import tkFileDialog

#import easygui

DEFAULT_PATH = "./TestDocs/example.txt"

def main():

    #Tkinter.Tk().withdraw() # Close the root window.
    #in_path = tkFileDialog.askopenfilename()
    #print(in_path)
    #jsonFile = open(DEFAULT_PATH, "r")

    findBuildPolygons(DEFAULT_PATH)

if __name__ == "__main__":
    main()