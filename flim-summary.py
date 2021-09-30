import os #Import OS for cwd, mkdir
import numpy as np

def getFileList(path: str, filterExtension="") -> list:
    """Returns list of files in path"""

    fileList = []

    # Get list of all files
    for item in os.listdir(path):
        if os.path.isfile(os.path.join(path, item)):
            if item.endswith(filterExtension):
                fileList.append(item)

    return fileList

class Measurement:
    def __init__(self, path: str):
        self.Path = path

    def loadData(self, path):
        """Loads ASCII File into NumPy Array"""
        data = np.loadtxt(path)
        self.Data = data

    def max(self):
        return np.max(self.Data)

    def min(self):
        return np.max(self.Data)

    def mean(self):
        return np.mean(self.Data)


class Variable:
    def __init__(self, var: str):
        self.Var = var
        self.Measurements = list()


class Channel:
    def __init__(self, ch: str):
        self.Ch = ch
        self.Variables = list()
    

class Project:
    def __init__(self):
        self.Channels = list()


if __name__ == "__main__":
    """ MAIN """

    path = r"C:\Dev\python\flim\flim-summary\test"
    extension = ".asc"

    fileList = getFileList(path, extension)

    # Did we find files?
    if len(fileList) == 0:
        print("No files were found...")
        sys.exit(0)

    # Create Project Object
    project = Project()
    
    # Split along underscores
    fileSplit = [f[:-len(extension)].split("_") for f in fileList]
    variables = [f[-1] for f in fileSplit]
    channel = [f[-2] for f in fileSplit]

    # Fix weird channel namings
    # ie. "-Ch1-Ch1-" to "Ch1"
    channel = [var[var.find("Ch"):var.find("Ch")+3] for var in channel]

    zippedFiles = zip(channel, variables, fileList)
    sortedZip = sorted(zippedFiles, key = lambda x: (x[0], x[1]))

    channelsSet = set(channel)
    for ch in channelsSet:

        # Add channel to project
        chobj = Channel(ch)
        project.Channels.append(chobj)

        # Create directory for channel
        newDirectory = os.path.join(path, ch)
        if not os.path.exists(newDirectory):
            os.mkdir(newDirectory)

        # Get variables in this channel
        varsInChannel = [f[1] for f in sortedZip if f[0]==ch]

        for var in varsInChannel:

            # Add variable to channel
            varobj = Variable(var)
            chobj.Variables.append(varobj)

            # Create directory for every variable in channel
            # TODO: escape illegal characters
            

            newDirectory = os.path.join(path, ch, var)
            if not os.path.exists(newDirectory):
                os.mkdir(newDirectory)

            filesToMove = [f[2] for f in sortedZip if (f[0]==ch and f[1]==var)]

            # Move files to subdirectories and append measurements to Variable objects
            for filename in filesToMove:
                source = os.path.join(path, filename)
                target = os.path.join(path, ch, var, filename)

                # Add measurement to Variable                
                measobj = Measurement(source)
                varobj.Measurements.append(measobj)
                
                try:
                    os.rename(source, target)
                except:
                    pass

            
                

    pass

