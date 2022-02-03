import os  # Import OS for cwd, mkdir
import numpy as np
from numpy.core.numeric import NaN
import pandas as pd
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
    def __init__(self, path: str, variable):
        self.Path = path
        self.Parent = variable

        self.Data = None

    @property
    def Filename(self):
        path = os.path.split(self.Path)
        return path[-1]

    @property
    def Name(self):
        """
        Return the name of the measurement.
        TODO: maybe hardcode name of measurement into class
        """
        filenameparts = self.Filename.split("_")
        return "_".join(filenameparts[0:-2])

    @property
    def cleandata(self):
        """Omitting 0s and max intensity values"""
        maxval = np.max(self.Data)
        return np.where((self.Data == 0) | (self.Data == maxval), np.NaN, self.Data)

    def loadData(self):
        """Loads ASCII File into NumPy Array"""

        if self.Data is not None:
            # Data already loaded
            return

        data = np.loadtxt(self.Path)
        self.Data = data

        print(
            "Loaded ({0}) ({1}) ({2})".format(
                self.Parent.Parent.Name,
                self.Parent.Name,
                self.Filename,
            )
        )

    def unload_data(self):
        self.Data = None

    def max(self):
        """Return maximum value, while omitting 0s and max intensity values"""
        return np.nanmax(self.cleandata)

    def min(self):
        return np.nanmin(self.cleandata)

    def mean(self):
        return np.nanmean(self.cleandata)

    def std(self):
        return np.nanstd(self.cleandata)


class Variable:
    def __init__(self, var: str, channel):
        self.Name = var
        self.Parent = channel
        self.Measurements = list()

    def load_on_request(self, func):
        # Decorator, load data on request and unload files
        def wrapper(self):
            self.load_data(self)
            func()
            self.unload_data(self)

        return wrapper

    @load_on_request
    def means(self):
        """Return list of single values of the measurements"""
        return [measurement.mean() for measurement in self.Measurements]

    @load_on_request
    def stds(self):
        """Return list of single values of the measurements"""
        return [measurement.std() for measurement in self.Measurements]

    def load_data(self):
        for measurement in self.Measurements:
            measurement.loadData()

    def unload_data(self):
        for measurement in self.Measurements:
            measurement.unload_data()


class Channel:
    def __init__(self, ch: str, project):
        self.Name = ch
        self.Parent = project
        self.Variables = list()


class Project:
    def __init__(self, path=".", extension=".asc", moveFiles=False):
        # Attributes
        self.Channels = list()
        self.FileList = list()
        self.UseSubDirectories = False

        # Directly import data
        self.importdata(path, extension, moveFiles)

        self.print_summary()

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
            chobj = Channel(ch, self)
            self.Channels.append(chobj)

            # Create directory for channel
            if moveFiles:
                newDirectory = os.path.join(path, ch)
                if not os.path.exists(newDirectory):
                    logging.debug("Creating new directory for Channel: {}".format(ch))
                    os.mkdir(newDirectory)

            # Get variables in this channel
            varsInChannel = [f[1] for f in parsedFileList if f[0] == ch]

            unique_variables = list(set(varsInChannel))

            for var in unique_variables:

                # Add variable to channel
                varobj = Variable(var, chobj)
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

                    if moveFiles:
                        target = os.path.join(path, ch, var, filename)

                        try:
                            os.rename(source, target)
                            pass
                        except:
                            logging.warning("Could not move file: {}".format(source))
                        else:
                            source = target

                    # Add measurement to Variable
                    measobj = Measurement(source, varobj)
                    varobj.Measurements.append(measobj)

    def print_summary(self):
        # Print summary
        print("{0:d} measurements.".format(len(self.Measurements)))

        # List variables
        for channel in self.Channels:
            variable_names = [var.Name for var in channel.Variables]
            print("{0} -- {1}".format(channel.Name, ", ".join(variable_names)))

    def load_data(self):
        # Load data into measurements
        for measurement in self.Measurements:
            measurement.loadData()

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

    def exportSummary(self, path="."):
        """Export a summary of all variables"""

        index = list(set([measurement.Name for measurement in self.Measurements]))

        logging.debug("Index length: {0:d}".format(len(index)))

        d = dict()
        for channel in self.Channels:
            for variable in self.Channels[0].Variables:
                d[channel.Name + "-" + variable.Name] = variable.means()

        logging.debug("Highest number of measurements: {0:d}".format(len(d)))

        try:
            df = pd.DataFrame(d, index=index)
        except:
            logging.error(
                'Index does not match number of measurements. Check for ambiguous file naming, such as "-Ch1-Ch2-"'
            )
            return

        print("Summary Table created:")
        print(df)

        targetfile = os.path.join(path, "export.xlsx")

        print("Exporting to Excel Files...")

        try:
            df.to_excel(targetfile, sheet_name="Averages")
        except:
            print("FAILED")
        else:
            print("Successfully exported to: {0}".format(targetfile))

        pass


if __name__ == "__main__":
    """MAIN"""

    path = r"C:\Dev\python\flim\flim-summary\sampledata\test1"
    extension = ".asc"

    # Create Project Object and Load Data
    project = Project(path, extension, moveFiles=False)

    project.exportSummary(path)
    pass
