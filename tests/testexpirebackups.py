'''
Created on 01.04.2022

@author: wf
'''
import unittest
from contextlib import redirect_stderr
from tempfile import NamedTemporaryFile
import datetime
import io
import os
import re
from expirebackups.expire import ExpireBackups, BackupFile,Expiration
import expirebackups.expire

class TestExpireBackups(unittest.TestCase):
    '''
    test Expire Backups
    '''

    def setUp(self):
        self.debug=False
        pass


    def tearDown(self):
        pass
    
    def createTestFile(self,ext:str,ageInDays:int):
        '''
        create a test File with the given extension and the given age in Days
        '''
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        dayDelta = datetime.timedelta(days = ageInDays)
        wantedTime=now-dayDelta
        timestamp=datetime.datetime.timestamp(wantedTime)
        testFile=NamedTemporaryFile(prefix=f"{ageInDays}daysOld",suffix=ext,delete=False)
        with open(testFile.name, 'a'):
            times=(timestamp,timestamp) # access time and modification time
            os.utime(testFile.name, times)
        return testFile.name
        
    
    def doTestPattern(self,days:int,weeks:int,months:int,years:int,failMsg:str, expectedMatch:str):
        '''
        test the given pattern
        '''
        try:
            _expiration=Expiration(days=days,weeks=weeks,months=months,years=years)
            self.fail(failMsg)
        except Exception as ex:
            self.assertTrue(re.match(expectedMatch,str(ex)))
            
    def testCreateTestFiles(self):
        '''
        '''
        ext=".tst"
        testFile=self.createTestFile(ext, 10)
        if self.debug:
            print (testFile)
        for ageInDays in range(1,101):
            testFile=self.createTestFile(ext, ageInDays)
            backupFile=BackupFile(testFile)
            print (f"{ageInDays:3d}:{backupFile.getAgeInDays():3d}:{testFile}")
    
    def testPatterns(self):
        '''
        test different patterns for being valid
        '''
        patterns=[
            (0,1,1,1,"pattern with 0 days not allowed",r"^0 days is invalid - value must be >=1")
        ]
        for days,weeks,months,years,failMsg,expectedMatch in patterns:
            self.doTestPattern(days, weeks, months, years, failMsg, expectedMatch)


    def testArgs(self):
        '''
        test Arguments
        '''
        args=["a","b"];
        result=None
        stderr = io.StringIO()
        try:
            with redirect_stderr(stderr):
                expirebackups.expire.main(args)
            self.fail("There should be a System Exception")
        except SystemExit as se:
            self.assertEqual(2,se.code)
            result = stderr.getvalue()
            if self.debug:
                print(result)
            self.assertTrue("usage:" in result)
            pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()