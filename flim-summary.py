import os  # Import OS for cwd, mkdir
import numpy as np
import logging

LOG_MSGFORMAT = "%(asctime)s - %(message)s"
LOG_TIMEFORMAT = "%H:%M:%S"
logging.basicConfig(format=LOG_MSGFORMAT, datefmt=LOG_TIMEFORMAT, level=logging.DEBUG)


def getFileListRoot(path: str, filterExtension="") -> list:
    """Returns list of files in path"""

    fileList = []

    # Get list of all files
    for item in os.listdir(path):
        if os.path.isfile(os.path.join(path, item)):
            if item.endswith(filterExtension):
                fileList.append(item)

    return fileList


def getFileListSubdir(path: str, filterExtension="") -> list:

    fileList = []

    # Walk through all subdirectories and files
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(filterExtension):
                fileList.append(os.path.join(root, file))

    return fileList


def parseFilenames(fileList: list) -> list:
    """Parse list of filenames and extract channel and variable"""

    # Split along underscores
    fileSplit = [f[: -len(extension)].split("_") for f in fileList]
    variables = [f[-1] for f in fileSplit]
    channel = [f[-2] for f in fileSplit]

    # Fix weird channel namings
    # ie. "-Ch1-Ch1-" to "Ch1"
    channel = [var[var.find("Ch") : var.find("Ch") + 3] for var in channel]

    zippedFiles = zip(channel, variables, fileList)
    sortedZip = sorted(zippedFiles, key=lambda x: (x[0], x[1]))

    return sortedZip


class Measurement:
    def __init__(self, path: str):
        self.Path = path

    @property
    def Filename(self):
        path = os.path.split(self.Path)
        return path[-1]

    def loadData(self):
        """Loads ASCII File into NumPy Array"""
        data = np.loadtxt(self.Path)
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
    def __init__(self, path=".", extension=".asc", moveFiles=False):
        # Attributes
        self.Channels = list()
        self.FileList = list()
        self.UseSubDirectories = False

        # Directly import data
        self.importdata(path, extension, moveFiles)

    @property
    def Measurements(self):
        return [
            measurement
            for channel in self.Channels
            for variable in channel.Variables
            for measurement in variable.Measurements
        ]

    def importdata(self, path=".", extension=".asc", moveFiles=False):
        """Import Data into project"""

        # Set self.FileList
        if not self.getFileList(path, extension):
            logging.warning("No files were found.")
            return None

        # Get a list of tuples containing (channel, variable, pathtofile)
        parsedFileList = parseFilenames(self.FileList)

        # Go through every unique channel
        # TODO: pass zip object instead of list instead
        channelsSet = set([x[0] for x in parsedFileList])

        for ch in channelsSet:

            # Add channel to project
            chobj = Channel(ch)
            self.Channels.append(chobj)

            # Create directory for channel
            if moveFiles:
                newDirectory = os.path.join(path, ch)
                if not os.path.exists(newDirectory):
                    logging.debug("Creating new directory for Channel: {}".format(ch))
                    os.mkdir(newDirectory)

            # Get variables in this channel
            varsInChannel = [f[1] for f in parsedFileList if f[0] == ch]

            for var in varsInChannel:

                # Add variable to channel
                varobj = Variable(var)
                chobj.Variables.append(varobj)

                # Create directory for every variable in channel
                # TODO: escape illegal characters
                if moveFiles:
                    newDirectory = os.path.join(path, ch, var)
                    if not os.path.exists(newDirectory):
                        os.mkdir(newDirectory)

                filesToMove = [
                    f[2] for f in parsedFileList if (f[0] == ch and f[1] == var)
                ]

                # Move files to subdirectories and append measurements to Variable objects
                for filename in filesToMove:
                    source = os.path.join(path, filename)
                    target = os.path.join(path, ch, var, filename)

                    if moveFiles:
                        try:
                            os.rename(source, target)
                            pass
                        except:
                            pass

                    source = target

                    # Add measurement to Variable
                    measobj = Measurement(source)
                    varobj.Measurements.append(measobj)

        # Load data into measurements
        print("Found {} measurements. Loading data...".format(len(self.Measurements)))
        for meas in self.Measurements:
            meas.loadData()
            print("Loaded " + meas.Filename)

    def getFileList(self, path=".", extension=".asc") -> bool:
        # Get list of files
        fileList = getFileListRoot(path, extension)

        # Did we find files?
        if len(fileList) > 0:
            self.FileList = fileList
            return True

        # Search in subdirectories
        fileList = getFileListSubdir(path, extension)
        if len(fileList) > 0:
            self.FileList = fileList
            self.UseSubDirectories = True
            return True

        return False


if __name__ == "__main__":
    """MAIN"""

    path = r"C:\Dev\python\flim\flim-summary\sampledata\test2"
    extension = ".asc"

    # Create Project Object and Load Data
    project = Project(path, extension, moveFiles=False)

    pass
