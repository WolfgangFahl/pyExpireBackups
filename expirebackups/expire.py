"""
Created on 2022-04-01

@author: wf
"""

import datetime
import os
import pathlib
import sys
import traceback
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from tempfile import NamedTemporaryFile
from typing import Tuple

from expirebackups.version import Version

__version__ = Version.version
__date__ = Version.date
__updated__ = Version.updated
DEBUG = 0

defaultDays = 7
defaultWeeks = 6
defaultMonths = 8
defaultYears = 4
defaultMinFileSize = 1


class BackupFile:
    """
    a Backup file which is potentially to be expired
    """

    def __init__(self, filePath: str):
        """
        constructor

        Args:
            filePath(str): the filePath of this backup File
        """
        self.filePath = filePath
        self.modified, self.size = self.getStats()
        self.sizeValue, self.unit, self.factor = BackupFile.getSize(self.size)
        self.sizeString = BackupFile.getSizeString(self.size)
        self.ageInDays = self.getAgeInDays()
        self.isoDate = self.getIsoDateOfModification()
        self.expire = False

    def __str__(self):
        """
        return a string representation of me
        """
        text = f"{self.ageInDays:6.1f} days {self.getMarker()}({self.sizeString}):{self.filePath}"
        return text

    def getMarker(self):
        """
        get my marker

        Returns:
            str: a symbol ❌ if i am to be deleted a ✅ if i am going to be kept
        """
        marker = "❌" if self.expire else "✅"
        return marker

    @classmethod
    def getSizeString(cls, size: float) -> str:
        """
        get my Size in human readable terms as a s

        Args:
            size(float): Size in Bytes

        Returns:
            str: a String representation
        """
        size, unit, _factor = cls.getSize(size)
        text = f"{size:5.0f} {unit}"
        return text

    @classmethod
    def getSize(cls, size: float) -> Tuple[float, str, float]:
        """
        get my Size in human readable terms

        Args:
            size(float): Size in Bytes

        Returns:
            Tuple(float,str,float): the size, unit and factor of the unit e.g. 3.2, "KB", 1024
        """
        units = [" B", "KB", "MB", "GB", "TB"]
        unitIndex = 0
        factor = 1
        while size > 1024:
            factor = factor * 1024
            size = size / 1024
            unitIndex += 1
        return size, units[unitIndex], factor

    def getStats(self) -> Tuple[datetime.datetime, float]:
        """
        get the datetime when the file was modified

        Returns:
            datetime: the file modification time
        """
        stats = os.stat(self.filePath)
        modified = datetime.datetime.fromtimestamp(stats.st_mtime, tz=datetime.timezone.utc)
        size = stats.st_size
        return modified, size

    def getAgeInDays(self) -> float:
        """
        get the age of this backup file in days

        Returns:
            float: the number of days this file is old
        """
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        age = now - self.modified
        return age.days

    def getIsoDateOfModification(self):
        """
        get the data of modification as an ISO date string

        Returns:
            str: an iso representation of the modification date
        """
        isoDate = self.modified.strftime("%Y-%m-%d_%H:%M")
        return isoDate

    def delete(self):
        """
        delete my file
        """
        if os.path.isfile(self.filePath):
            os.remove(self.filePath)


class ExpirationRule:
    """
    an expiration rule keeps files at a certain
    """

    def __init__(self, name, freq: float, minAmount: int):
        """
        constructor

        name(str): name of this rule
        freq(float): the frequency) in days
        minAmount(int): the minimum of files to keep around
        """
        self.name = name
        self.ruleName = name  # will late be changed by a sideEffect in getNextRule e.g. from "week" to "weekly"
        self.freq = freq
        self.minAmount = minAmount
        if minAmount < 0:
            raise Exception(f"{self.minAmount} {self.name} is invalid - {self.name} must be >=0")

    def reset(self, prevFile: BackupFile):
        """
        reset my state with the given previous File

        Args:
            prevFile: BackupFile - the file to anchor my startAge with
        """
        self.kept = 0
        if prevFile is None:
            self.startAge = 0
        else:
            self.startAge = prevFile.ageInDays

    def apply(self, file: BackupFile, prevFile: BackupFile, debug: bool) -> bool:
        """
        apply me to the given file taking the previously kept File prevFile (which might be None) into account

        Args:

            file(BackupFile): the file to apply this rule for
            prevFile(BackupFile): the previous file to potentially take into account
            debug(bool): if True show debug output
        """
        if prevFile is not None:
            ageDiff = file.ageInDays - prevFile.ageInDays
            keep = ageDiff >= self.freq
        else:
            ageDiff = file.ageInDays - self.startAge
            keep = True
        if keep:
            self.kept += 1
        else:
            file.expire = True
        if debug:
            print(
                f"Δ {ageDiff}({ageDiff-self.freq}) days for {self.ruleName}({self.freq}) {self.kept}/{self.minAmount}{file}"
            )
        return self.kept >= self.minAmount


class Expiration:
    """
    Expiration pattern
    """

    def __init__(
        self,
        days: int = defaultDays,
        weeks: int = defaultWeeks,
        months: int = defaultMonths,
        years: int = defaultYears,
        minFileSize: int = defaultMinFileSize,
        debug: bool = False,
    ):
        """
        constructor

        Args:
            days(float): how many files to keep for the daily backup
            weeks(float): how many files to keep for the weekly backup
            months(float): how many files to keep for the monthly backup
            years(float):  how many files to keep for the yearly backup
            debug(bool): if true show debug information (rule application)
        """
        self.rules = {
            "dayly": ExpirationRule("days", 1.0, days),
            "weekly": ExpirationRule("weeks", 7.0, weeks),
            # the month is in fact 4 weeks
            "monthly": ExpirationRule("months", 28.0, months),
            # the year is in fact 52 weeks or 13 of the 4 week months
            "yearly": ExpirationRule("years", 364.0, years),
        }
        self.minFileSize = minFileSize
        self.debug = debug

    def getNextRule(self, ruleIter, prevFile: BackupFile, verbose: bool) -> ExpirationRule:
        """
        get the next rule for the given ruleIterator

        Args:
            ruleIter(Iter): Iterator over ExpirationRules
            prevFile(BackupFile): the previousFile to take into account / reset/anchor the rule with
            verbose(bool): if True show a message that the rule will be applied
        Returns:
            ExpirationRule: the next ExpirationRule
        """
        ruleKey = next(ruleIter)
        rule = self.rules[ruleKey]
        rule.ruleName = ruleKey
        if verbose:
            print(f"keeping {rule.minAmount} files for {rule.ruleName} backup")
        rule.reset(prevFile)
        return rule

    def applyRules(self, backupFiles: list, verbose: bool = True):
        """
        apply my expiration rules to the given list of
        backup Files

        Args:
            backupFiles(list): the list of backupFiles to apply the rules to
            verbose(debug): if true show what the rules are doing
        Returns:
            list: the sorted and marked list of backupFiles
        """
        filesByAge = sorted(backupFiles, key=lambda backupFile: backupFile.getAgeInDays())
        ruleIter = iter(self.rules)
        rule = self.getNextRule(ruleIter, None, verbose)
        prevFile = None
        for file in filesByAge:
            if file.size < self.minFileSize:
                file.expire = True
            else:
                ruleDone = rule.apply(file, prevFile, debug=self.debug)
                if not file.expire:
                    prevFile = file
                if ruleDone:
                    rule = self.getNextRule(ruleIter, prevFile, verbose)
        return filesByAge


class ExpireBackups(object):
    """
    Expiration of Backups - migrated from com.bitplan.backup java solution
    """

    def __init__(
        self,
        rootPath: str,
        baseName: str = None,
        ext: str = None,
        expiration: Expiration = None,
        dryRun: bool = True,
        debug: bool = False,
    ):
        """
        Constructor

        Args:
            rootPath(str): the base path for this backup expiration
            baseName(str): the basename to filter for (if any)
            ext(str): file extensions to filter for e.g. ".tgz" (if any)
            expiration(Expiration): the Expiration Rules to apply
            dryRun(bool): donot delete any files but only show deletion plan
        """
        self.rootPath = rootPath
        self.baseName = baseName
        self.ext = ext
        # if no expiration is specified use the default one
        if expiration is None:
            expiration = Expiration()
        self.expiration = expiration
        self.dryRun = dryRun
        self.debug = debug

    @classmethod
    def createTestFile(cls, ageInDays: float, baseName: str = None, ext: str = ".tst"):
        """
        create a test File with the given extension and the given age in Days

        Args:
            ageInDays(float): the age of the file in days
            baseName(str): the prefix of the files (default: None)
            ext(str): the extension to be used - default ".tst"

        Returns:
            str: the full path name of the testfile
        """
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        dayDelta = datetime.timedelta(days=ageInDays)
        wantedTime = now - dayDelta
        timestamp = datetime.datetime.timestamp(wantedTime)
        prefix = "" if baseName is None else f"{baseName}-"
        testFile = NamedTemporaryFile(prefix=f"{prefix}{ageInDays}daysOld-", suffix=ext, delete=False)
        with open(testFile.name, "a"):
            times = (timestamp, timestamp)  # access time and modification time
            os.utime(testFile.name, times)
        return testFile.name

    @classmethod
    def createTestFiles(cls, numberOfTestfiles: int, baseName: str = "expireBackupTest", ext: str = ".tst"):
        """
        create the given number of tests files

        Args:
            numberOfTestfiles(int): the number of files to create
            baseName(str): the prefix of the files (default: '')
            ext(str): the extension of the files (default: '.tst')

        Returns:
            tuple(str,list): the path of the directory where the test files have been created
            and a list of BackupFile files
        """
        backupFiles = []
        for ageInDays in range(1, numberOfTestfiles + 1):
            testFile = ExpireBackups.createTestFile(ageInDays, baseName=baseName, ext=ext)
            backupFiles.append(BackupFile(testFile))
        path = pathlib.Path(testFile).parent.resolve()
        return path, backupFiles

    def getBackupFiles(self) -> list:
        """
        get the list of my backup Files
        """
        backupFiles = []
        for root, _dirs, files in os.walk(self.rootPath):
            for file in files:
                include = False
                if self.baseName is not None:
                    include = file.startswith(self.baseName)
                if self.ext is not None:
                    include = file.endswith(self.ext)
                if include:
                    backupFile = BackupFile(os.path.join(root, file))
                    backupFiles.append(backupFile)
        return backupFiles

    def doexpire(self, withDelete: bool = False, show=True, showLimit: int = None):
        """
        expire the files in the given rootPath

        withDelete(bool): if True really delete the files
        show(bool): if True show the expiration plan
        showLimit(int): if set limit the number of lines to display
        """
        backupFiles = self.getBackupFiles()
        filesByAge = self.expiration.applyRules(backupFiles)
        total = 0
        keptTotal = 0
        kept = 0
        if show:
            deletehint = "by deletion" if withDelete else "dry run"
            print(f"expiring {len(filesByAge)} files {deletehint}")
        for i, backupFile in enumerate(filesByAge):
            total += backupFile.size
            totalString = BackupFile.getSizeString(total)
            marker = backupFile.getMarker()
            line = f"#{i+1:4d}{marker}:{backupFile.ageInDays:6.1f} days({backupFile.sizeString}/{totalString})→{backupFile.filePath}"
            showLine = show and (showLimit is None or i < showLimit)
            if showLine:
                print(line)
            if not backupFile.expire:
                kept += 1
                keptTotal += backupFile.size
            if withDelete and backupFile.expire:
                backupFile.delete()
        if show:
            keptSizeString = BackupFile.getSizeString(keptTotal)
            print(f"kept {kept} files {keptSizeString}")


def main(argv=None):  # IGNORE:C0111
    """main program."""

    if argv is None:
        argv = sys.argv

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = "%%(prog)s %s (%s)" % (program_version, program_build_date)
    program_shortdesc = Version.description
    user_name = "Wolfgang Fahl"
    program_license = """%s

  Created by %s on %s.
  Copyright 2008-2022 Wolfgang Fahl. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
""" % (
        program_shortdesc,
        user_name,
        str(__date__),
    )

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-d", "--debug", dest="debug", action="store_true", help="show debug info")

        # expiration schedule selection
        parser.add_argument(
            "--days",
            type=int,
            default=defaultDays,
            help="number of consecutive days to keep a daily backup (default: %(default)s)",
        )
        parser.add_argument(
            "--weeks",
            type=int,
            default=defaultWeeks,
            help="number of consecutive weeks to keep a weekly backup (default: %(default)s)",
        )
        parser.add_argument(
            "--months",
            type=int,
            default=defaultMonths,
            help="number of consecutive month to keep a monthly backup (default: %(default)s)",
        )
        parser.add_argument(
            "--years",
            type=int,
            default=defaultYears,
            help="number of consecutive years to keep a yearly backup (default: %(default)s)",
        )

        # file filter selection arguments
        parser.add_argument(
            "--minFileSize",
            type=int,
            default=defaultMinFileSize,
            help="minimum File size in bytes to filter for (default: %(default)s)",
        )
        parser.add_argument("--rootPath", default=".")
        parser.add_argument("--baseName", default=None, help="the basename to filter for (default: %(default)s)")
        parser.add_argument("--ext", default=None, help="the extension to filter for (default: %(default)s)")

        parser.add_argument(
            "--createTestFiles",
            type=int,
            default=None,
            help="create the given number of temporary test files (default: %(default)s)",
        )

        parser.add_argument("-f", "--force", action="store_true")
        parser.add_argument("-V", "--version", action="version", version=program_version_message)

        args = parser.parse_args(argv[1:])
        if args.createTestFiles:
            path, _backupFiles = ExpireBackups.createTestFiles(args.createTestFiles)
            print(f"created {args.createTestFiles} test files with extension '.tst' in {path}")
            print(
                f"Please try out \nexpireBackups --rootPath {path} --baseName expireBackup --ext .tst --minFileSize 0"
            )
            print(
                "then try appending the -f option to the command that will actually delete files (which are in a temporary directory"
            )
            print(
                "and run the command another time with that option to see that no files are deleted any more on second run"
            )
        else:
            dryRun = True
            if args.force:
                dryRun = False
            expiration = Expiration(
                days=args.days,
                months=args.months,
                weeks=args.weeks,
                years=args.years,
                minFileSize=args.minFileSize,
                debug=args.debug,
            )
            eb = ExpireBackups(
                rootPath=args.rootPath,
                baseName=args.baseName,
                ext=args.ext,
                expiration=expiration,
                dryRun=dryRun,
                debug=args.debug,
            )
            eb.doexpire(args.force)

    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 1
    except Exception as e:
        if DEBUG:
            raise (e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        if args.debug:
            print(traceback.format_exc())
        return 2


if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-d")
    sys.exit(main())
