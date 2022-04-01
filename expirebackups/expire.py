'''
Created on 2022-04-01

@author: wf
'''
from expirebackups.version import Version
import os
import sys
import traceback
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

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
    '''

class Expiration():
    '''
    Expiration pattern
    '''
    
    def __init__(self,days:int=defaultDays,weeks:int=defaultWeeks,months:int=defaultMonths,years:int=defaultYears):
        '''
        constructor
        '''
        if days<=1:
            raise Exception(f"{days} days is invalid - value must be >=1")
        self.days=days
        self.weeks=weeks
        self.months=months
        self.yearx=years 

class ExpireBackups(object):
    '''
    Expiration of Backups - migrated from com.bitplan.backup java solution
    '''

    def __init__(self,testMode:bool=False, debug:bool=False):
        '''
        Constructor
        '''
        self.testMode=testMode
        self.debug=debug
        
    def doexpire(self):
        pass
        
def main(argv=None): # IGNORE:C0111
    '''main program.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)    
        
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
        parser.add_argument("--extensions",nargs='+')
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        
        args = parser.parse_args(argv)
        expiration=Expiration(days=args.days,month=args.month,weeks=args.weeks,years=args.years)
        eb=ExpireBackups(args=args,debug=args.debug)
        eb.doexpire(args.extensions,expiration)
        
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