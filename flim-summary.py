import os #Import OS for cwd, mkdir

def getFileList(path: str, filterExtension="") -> list:
    """Returns list of files in path"""

    fileList = []

    # Get list of all files
    for item in os.listdir(path):
        if os.path.isfile(os.path.join(path, item)):
            if item.endswith(filterExtension):
                fileList.append(item)

    return fileList




if __name__ == "__main__":
    """ MAIN """

    path = r"C:\Dev\python\flim\flim-summary\test"
    extension = ".asc"

    fileList = getFileList(path, extension)

    # Did we find files?
    if len(fileList) == 0:
        print("No files were found...")
        sys.exit(0)
    
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

        # Create directory for channel
        newDirectory = os.path.join(path, ch)
        if not os.path.exists(newDirectory):
            os.mkdir(newDirectory)

        # Get variables in this channel
        varsInChannel = [f[1] for f in sortedZip if f[0]==ch]

        for var in varsInChannel:
            # Create directory for every variable in channel
            # TODO: escape illegal characters

            newDirectory = os.path.join(path, ch, var)
            if not os.path.exists(newDirectory):
                os.mkdir(newDirectory)

            filesToMove = [f[2] for f in sortedZip if (f[0]==ch and f[1]==var)]

            for f in filesToMove:
                pass

    pass

