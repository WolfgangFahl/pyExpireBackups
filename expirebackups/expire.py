'''
Created on 2022-04-01

@author: wf
'''
from expirebackups.version import Version
import datetime
import os
import pathlib
import sys
import traceback

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

from tempfile import NamedTemporaryFile

__version__ = Version.version
__date__ = Version.date
__updated__ = Version.updated
DEBUG = 0
defaultDays=7
defaultWeeks=6
defaultMonths=8
defaultYears=4

class BackupFile():
    '''
    a Backup file which is potentially to be expired
    '''
    def __init__(self,filePath:str):
        '''
        constructor
        
        Args:
            filePath(str): the filePath of this backup File
        '''
        self.filePath=filePath
        self.modified=self.getModified()
        self.ageInDays=self.getAgeInDays()
        self.isoDate=self.getIsoDateOfModification()
        
    def __str__(self):
        '''
        return a string representation of me
        '''
        text=f"{self.ageInDays:6.1f} days:{self.filePath}"
        return text
        
    def getModified(self)->datetime.datetime:
        '''
        get the datetime when the file was modified
        
        Returns:
            datetime: the file modification time
        '''
        stats=os.stat(self.filePath)
        modified = datetime.datetime.fromtimestamp(stats.st_mtime, tz=datetime.timezone.utc)
        return modified
    
    def getAgeInDays(self)->float:
        '''
        get the age of this backup file in days
        
        Returns:
            float: the number of days this file is old
        '''
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        age=now - self.modified
        return age.days
    
    def getIsoDateOfModification(self):
        '''
        get the data of modification as an ISO date string
        
        Returns:
            str: an iso representation of the modification date
        '''
        isoDate=self.modified.strftime('%Y-%m-%d_%H:%M')
        return isoDate
    
    def delete(self):
        '''
        delete my file
        '''
        if os.path.isfile(self.filePath):
            os.remove(self.filePath)
        
class ExpirationRule():
    '''
    an expiration rule keeps files at a certaion
    '''
    def __init__(self,name,freq:float,minAmount:int):
        '''
        '''
        self.name=name
        self.freq=freq
        self.minAmount=minAmount
        if minAmount<0:
            raise Exception(f"{self.minAmount} {self.name} is invalid - {self.name} must be >=0")
   
class Expiration():
    '''
    Expiration pattern
    '''
    
    def __init__(self,days:int=defaultDays,weeks:int=defaultWeeks,months:int=defaultMonths,years:int=defaultYears):
        '''
        constructor
        '''
        self.rules={
            "days":ExpirationRule("days",1.0,days),
            "weeks":ExpirationRule("weeks",7.0,weeks),
            # the month is in fact 4 weeks
            "months":ExpirationRule("months",28,months),
            # the year is in fact 52 weeks or 13 of the 4 week months
            "years": ExpirationRule("years",364,years)
        }      
        
    def applyRules(self,backupFiles:list):
        '''
        apply my expiration rules to the given list of
        backup Files
        
        Args:
            backupFiles(list): the list of backupFiles to apply the rules to
        Returns:
            list: the sorted and marked list of backupFiles
        '''
        filesByAge=sorted(backupFiles, key=lambda backupFile: backupFile.getAgeInDays())
        return filesByAge    

class ExpireBackups(object):
    '''
    Expiration of Backups - migrated from com.bitplan.backup java solution
    '''

    def __init__(self,rootPath:str,ext:str,expiration:Expiration=None,dryRun:bool=True, debug:bool=False):
        '''
        Constructor
        
        Args:
            rootPath(str): the base path for this backup expiration
            ext(str): file extensions to filter for e.g. ".tgz"
            expiration(Expiration): the Expiration Rules to apply
            dryRun(bool): donot delete any files but only show deletion plan 
        '''
        self.rootPath=rootPath
        self.ext=ext
        # if no expiration is specified use the default one
        if expiration is None:
            expiration=Expiration()
        self.expiration=expiration
        self.dryRun=dryRun
        self.debug=debug
        
    @classmethod    
    def createTestFile(cls,ageInDays:float,baseName:str="",ext:str=".tst"):
        '''
        create a test File with the given extension and the given age in Days
        
        Args:
            ageInDays(float): the age of the file in days
            baseName(str): the prefix of the files (default: '')
            ext(str): the extension to be used - default ".tst"
            
        Returns:
            str: the full path name of the testfile
        '''
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        dayDelta = datetime.timedelta(days = ageInDays)
        wantedTime=now-dayDelta
        timestamp=datetime.datetime.timestamp(wantedTime)
        testFile=NamedTemporaryFile(prefix=f"{baseName}-{ageInDays}daysOld",suffix=ext,delete=False)
        with open(testFile.name, 'a'):
            times=(timestamp,timestamp) # access time and modification time
            os.utime(testFile.name, times)
        return testFile.name
    
    @classmethod
    def createTestFiles(cls,numberOfTestfiles:int,baseName:str="",ext:str=".tst"):
        '''
        create the given number of tests files
        
        Args:
            numberOfTestfiles(int): the number of files to create
            baseName(str): the prefix of the files (default: '')
            ext(str): the extension of the files (default: '.tst')
            
        Returns:
            tuple(str,list): the path of the directory where the test files have been created
            and a list of BackupFile files
        '''
        backupFiles=[]
        for ageInDays in range(1,numberOfTestfiles+1):
            testFile=ExpireBackups.createTestFile(ageInDays,baseName=baseName,ext=ext)
            backupFiles.append(BackupFile(testFile))
        path=pathlib.Path(testFile).parent.resolve()
        return path,backupFiles
     
    def getBackupFiles(self)->list:
        '''
        get the list of my backup Files
        '''    
        backupFiles=[]
        for root, _dirs, files in os.walk(self.rootPath):
            for file in files:
                if file.endswith(self.ext):
                    backupFile=BackupFile(os.path.join(root, file))
                    backupFiles.append(backupFile)
        return backupFiles            
        
    def doexpire(self):
        '''
        expire the files in the given rootPath
        '''
        backupFiles=self.getBackupFiles()
        filesByAge=self.expiration.applyRules(backupFiles)
        for backupFile in filesByAge:
            print(backupFile)
        
def main(argv=None): # IGNORE:C0111
    '''main program.'''

    if argv is None:
        argv = sys.argv   
        
    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = Version.description
    user_name="Wolfgang Fahl"
    program_license = '''%s

  Created by %s on %s.
  Copyright 2008-2022 Wolfgang Fahl. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, user_name,str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-d", "--debug", dest="debug", action="store_true", help="show debug info")
        parser.add_argument("--days",type=int,default=defaultDays,help = "number of consecutive days to keep a daily backup (default: %(default)s)")
        parser.add_argument("--weeks",type=int,default=defaultWeeks,help = "number of consecutive weeks to keep a weekly backup (default: %(default)s)")
        parser.add_argument("--months",type=int,default=defaultMonths,help = "number of consecutive month to keep a monthly backup (default: %(default)s)")
        parser.add_argument("--years",type=int,default=defaultYears,help = "number of consecutive years to keep a yearly backup (default: %(default)s)") 
        parser.add_argument("--ext",default=".tgz",help="the extension to filter for (default: %(default)s)")
        parser.add_argument("--createTestFiles",type=int,default=None,help="create the given number of temporary test files (default: %(default)s)")
        parser.add_argument("--baseName",help="the basename to filter for")  
        parser.add_argument("--rootPath",default=".")
        parser.add_argument("-f","--force",action="store_true")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        
        args = parser.parse_args(argv[1:])
        if args.createTestFiles:
            path,_backupFiles=ExpireBackups.createTestFiles(args.createTestFiles,baseName=args.baseName,ext=args.ext)
            print(f"created {args.createTestFiles} test files in {path}")
        else:
            dryRun=True
            if args.force:
                dryRun=False    
            expiration=Expiration(days=args.days,months=args.months,weeks=args.weeks,years=args.years)
            eb=ExpireBackups(rootPath=args.rootPath,ext=args.ext,expiration=expiration,dryRun=dryRun,debug=args.debug)
            eb.doexpire()
        
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 1
    except Exception as e:
        if DEBUG:
            raise(e)
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