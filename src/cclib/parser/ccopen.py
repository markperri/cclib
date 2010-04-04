"""
cclib (http://cclib.sf.net) is (c) 2006, the cclib development team
and licensed under the LGPL (http://www.gnu.org/copyleft/lgpl.html).
"""

__revision__ = "$Revision$"


import os
import sys
import bz2 # New in Python 2.3.
import gzip
import zipfile
import fileinput
import logging
import StringIO

import adfparser
import gamessparser
import gamessukparser
import gaussianparser
import jaguarparser
import molproparser
import turbomoleparser


def openlogfile(filename):
    """Return a file object given a filename.

    Given the filename of a log file or a gzipped, zipped, or bzipped
    log file, this function returns a regular Python file object.
    
    Given a list of filenames, this function returns a FileInput object,
    which can be used for seamless iteration without concatenation.
    """

    # If there is a single string argument given.
    if type(filename) == str:
    
        extension = os.path.splitext(filename)[1]
        
        if extension == ".gz":
            fileobject = gzip.open(filename, "r")

        elif extension == ".zip":
            zip = zipfile.ZipFile(filename, "r")
            assert (len(zip.namelist()) == 1,
                    "ERROR: Zip file contains more than 1 file")
            fileobject = StringIO.StringIO(zip.read(zip.namelist()[0]))

        elif extension in ['.bz', '.bz2']:
            fileobject = bz2.BZ2File(filename, "r")

        else:
            fileobject = open(filename, "r")

        return fileobject
    
    elif hasattr(filename, "__iter__"):
    
        # Compression (gzip and bzip) is supported as of Python 2.5.
        if sys.version_info[0] >= 2 and sys.version_info[1] >= 5:
            fileobject = fileinput.input(filename, openhook=fileinput.hook_compressed)
        else:
            fileobject = fileinput.input(filename)
        
        return fileobject

def ccopen(filename, progress=None, loglevel=logging.INFO, logname="Log"):
    """Guess the identity of a particular log file and return an instance of it.
    
    Inputs:
      filename - the location of a single logfile, or a list of logfiles

    Outputs: one of ADF, GAMESS, GAMESS UK, Gaussian, Jaguar, Molpro, Turbomole, or
             None (if it cannot figure it out or the file does not exist).
    """

    filetype = None

    # Try to open the logfile(s), using openlogfile.
    try:
      inputfile = openlogfile(filename)
    except IOError, (errno, strerror):
      print "I/O error %s (%s): %s" %(errno, filename, strerror)
      return None

    # Read through the logfile(s) and search for a clue.
    for line in inputfile:

        if line.find("Amsterdam Density Functional") >= 0:
            filetype = adfparser.ADF
            break

        # Don't break in this case as it may be a GAMESS-UK file.
        elif line.find("GAMESS") >= 0:
            filetype = gamessparser.GAMESS

        # This can break, since it is non-GAMESS-UK specific.
        elif line.find("GAMESS VERSION") >= 0:
            filetype = gamessparser.GAMESS
            break

        elif line.find("G A M E S S - U K") >= 0:
            filetype = gamessukparser.GAMESSUK
            break

        elif line.find("Gaussian, Inc.") >= 0:
            filetype = gaussianparser.Gaussian
            break

        elif line.find("Jaguar") >= 0:
            filetype = jaguarparser.Jaguar
            break

        elif line.find("PROGRAM SYSTEM MOLPRO") >= 0:
            filetype = molproparser.Molpro
            break

        # Molpro log files don't have the line above. Set this only if
        #   nothing else is detected, and notice it can be overwritten,
        #   since it does not break the loop.
        elif line[0:8] == "1PROGRAM" and not filetype:
            filetype = molproparser.Molpro

        # Note: Turbomole output files don't have "Turbomole" in them,
        #   but you can put it in there.
        elif line.find("Turbomole") >=0 or line.find("TURBOMOLE") >= 0:
            filetype = turbomoleparser.Turbomole
            break

        # This is not truly specific, but no other programs have this combination,
        #   which makes it unnecessary to add "Turbomole" anywhere.
        # Do not break, though, just in case.
        elif line[0] == "$" and line[1].islower():
            filetype = turbomoleparser.Turbomole

    # Need to close before creating an instance.
    inputfile.close()
    
    if filetype: # Create an instance of the chosen class
        filetype = apply(filetype, [filename, progress, loglevel])
        
    return filetype

if __name__ == "__main__":
    import doctest, utils
    doctest.testmod(utils, verbose=False)