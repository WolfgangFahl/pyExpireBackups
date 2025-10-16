"""
Created on 01.04.2022

@author: wf
"""

import io
import re
import unittest
from contextlib import redirect_stderr

import expirebackups.expire
from expirebackups.expire import Expiration, ExpireBackups


class TestExpireBackups(unittest.TestCase):
    """
    test Expire Backups
    """

    def setUp(self):
        self.debug = False
        pass

    def tearDown(self):
        pass

    def doTestPattern(self, days: int, weeks: int, months: int, years: int, failMsg: str, expectedMatch: str):
        """
        test the given pattern
        """
        try:
            _expiration = Expiration(days=days, weeks=weeks, months=months, years=years)
            self.fail(failMsg)
        except Exception as ex:
            self.assertTrue(re.match(expectedMatch, str(ex)))

    def testCreateTestFiles(self):
        """
        test creating test files to be expired
        """
        ext = ".tst"
        testFile = ExpireBackups.createTestFile(10, ext=ext)
        debug = self.debug
        debug = True
        if debug:
            print(testFile)
        path, backupFiles = ExpireBackups.createTestFiles(20, ext=ext)
        if debug:
            print(path)
        for i, backupFile in enumerate(backupFiles):
            if debug:
                print(f"{i+1:3d}:{backupFile.getAgeInDays():3d}:{testFile}")
            backupFile.delete()

    def testExpireBackus(self):
        """
        test expiration of backups
        """
        # ebt= expire backup test
        ext = ".ebt"
        numberOfFiles = (
            expirebackups.expire.defaultDays
            + expirebackups.expire.defaultWeeks * 7
            + expirebackups.expire.defaultMonths * 28
        )
        path, _backupFiles = ExpireBackups.createTestFiles(numberOfFiles, ext=ext)
        eb = ExpireBackups(rootPath=path, ext=ext)
        # test files are only touched so allow minimum fileSize 0
        eb.expiration.minFileSize = 0
        debug = self.debug
        # debug=True
        eb.expiration.debug = debug
        # show=True
        showLimit = 38
        eb.doexpire(withDelete=True, showLimit=showLimit)

    def testPatterns(self):
        """
        test different patterns for being valid
        """
        patterns = [(-1, 0, 0, 0, "days"), (0, -1, 0, 0, "weeks"), (0, 0, -1, 0, "months"), (0, 0, 0, -1, "years")]
        for days, weeks, months, years, name in patterns:
            failMsg = f"pattern for {name} failed"
            expectedMatch = rf"^-1 {name} is invalid - {name} must be >=0$"
            self.doTestPattern(days, weeks, months, years, failMsg, expectedMatch)

    def testArgs(self):
        """
        test Arguments
        """
        args = ["a", "b"]
        result = None
        stderr = io.StringIO()
        try:
            with redirect_stderr(stderr):
                expirebackups.expire.main(args)
            self.fail("There should be a System Exception")
        except SystemExit as se:
            self.assertEqual(2, se.code)
            result = stderr.getvalue()
            if self.debug:
                print(result)
            self.assertTrue("usage:" in result)
            pass


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
