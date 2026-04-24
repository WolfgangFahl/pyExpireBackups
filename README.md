# pyExpireBackups
Backup expiration based on rules (yearly, monthly, weekly, daily ...)

[![pypi](https://img.shields.io/pypi/pyversions/pyExpireBackups)](https://pypi.org/project/pyExpireBackups/)
[![Github Actions Build](https://github.com/WolfgangFahl/pyExpireBackups/actions/workflows/build.yml/badge.svg)](https://github.com/WolfgangFahl/pyExpireBackups/actions/workflows/build.yml)
[![PyPI Status](https://img.shields.io/pypi/v/pyExpireBackups.svg)](https://pypi.python.org/pypi/pyExpireBackups/)
[![GitHub issues](https://img.shields.io/github/issues/WolfgangFahl/pyExpireBackups.svg)](https://github.com/WolfgangFahl/pyExpireBackups/issues)
[![GitHub closed issues](https://img.shields.io/github/issues-closed/WolfgangFahl/pyExpireBackups.svg)](https://github.com/WolfgangFahl/pyExpireBackups/issues/?q=is%3Aissue+is%3Aclosed)
[![API Docs](https://img.shields.io/badge/API-Documentation-blue)](https://WolfgangFahl.github.io/pyExpireBackups/)
[![License](https://img.shields.io/github/license/WolfgangFahl/pyExpireBackups.svg)](https://www.apache.org/licenses/LICENSE-2.0)

`pyExpireBackups` expires backup files to save disk space for unneeded
backups. With a pattern of days, weeks, months and years a limit on the total
number of backup files is set — a classic
*grandfather–father–son* retention scheme.

It is a small, dependency-free Python 3.10+ tool that can be run from the
command line or embedded as a library.

## Install

From PyPI:

```bash
pip install pyExpireBackups
```

From source:

```bash
git clone https://github.com/WolfgangFahl/pyExpireBackups.git
cd pyExpireBackups
pip install .
```

## Usage

```text
expireBackups -h
usage: expireBackups [-h] [-d] [--days DAYS] [--weeks WEEKS] [--months MONTHS] [--years YEARS]
                     [--minFileSize MINFILESIZE] [--rootPath ROOTPATH] [--baseName BASENAME] [--ext EXT]
                     [--createTestFiles CREATETESTFILES] [-f] [-V]

Backup expiration based on rules (yearly,monthly,weekly,daily ...)

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           show debug info
  --days DAYS           number of consecutive days to keep a daily backup (default: 7)
  --weeks WEEKS         number of consecutive weeks to keep a weekly backup (default: 6)
  --months MONTHS       number of consecutive month to keep a monthly backup (default: 8)
  --years YEARS         number of consecutive years to keep a yearly backup (default: 4)
  --minFileSize MINFILESIZE
                        minimum File size in bytes to filter for (default: 1)
  --rootPath ROOTPATH
  --baseName BASENAME   the basename to filter for (default: None)
  --ext EXT             the extension to filter for (default: None)
  --createTestFiles CREATETESTFILES
                        create the given number of temporary test files (default: None)
  -f, --force
  -V, --version         show program's version number and exit
```

### Flag reference

| Flag                        | Description                                             | Default |
| --------------------------- | ------------------------------------------------------- | ------: |
| `--rootPath`                | Directory to scan (recursive)                           |   `.`   |
| `--baseName`                | Keep only files whose name starts with this prefix      |  none   |
| `--ext`                     | Keep only files whose name ends with this extension     |  none   |
| `--minFileSize`             | Ignore files below this size (bytes)                    |   `1`   |
| `--days`                    | Daily backups to keep                                   |   `7`   |
| `--weeks`                   | Weekly backups to keep                                  |   `6`   |
| `--months`                  | Monthly backups to keep                                 |   `8`   |
| `--years`                   | Yearly backups to keep                                  |   `4`   |
| `-f`, `--force`             | Actually delete files (omit for a dry run)              |  off    |
| `-d`, `--debug`             | Print rule-evaluation details                           |  off    |
| `--createTestFiles N`       | Create N temporary test files in the temp dir and exit  |  none   |
| `-V`, `--version`           | Show version                                            |         |

Files smaller than `--minFileSize` are always marked for expiry — a safeguard
against incomplete or zero-byte backups. Set a retention count to `0` to
skip that tier entirely.

## How retention works

The expiration engine applies four rules in order, from newest to oldest:

| Rule      | Frequency    | Default count | Keeps the newest file in every ... |
| --------- | ------------ | -------------:| ---------------------------------- |
| `dayly`   | 1 day        | 7             | day                                |
| `weekly`  | 7 days       | 6             | week                               |
| `monthly` | 28 days      | 8             | 4-week window                      |
| `yearly`  | 364 days     | 4             | 52-week window                     |

The algorithm walks the file list sorted by age (newest first). It keeps the
first file of the current rule, then skips over files that are closer
together than the rule's frequency, keeping one representative per window.
Once the rule has kept its configured number of files, the next (coarser)
rule takes over at the age of the last kept file.

With the defaults this yields roughly 7 daily + 6 weekly + 8 monthly +
4 yearly = up to 25 kept files spanning about four years.

### Calendar-day semantics (since 0.1.3, [#11])

The daily rule compares files by **calendar day**, not by elapsed hours.
Two backups taken at slightly different times of day — e.g. a cron job whose
runtime drifts by a few minutes — are still recognised as "one day apart".
The fractional age shown in the output is kept for display and sorting only.

**Scheduling guidance:** schedule your backup jobs so that a single run
starts and finishes on the same calendar day (UTC). NTP-synchronised clocks
are assumed.

## Examples

### Dry run (default — nothing is deleted)

```bash
expireBackups --ext .tgz
keeping 7 files for dayly backup
keeping 6 files for weekly backup
keeping 8 files for monthly backup
keeping 4 files for yearly backup
expiring 269 files dry run
#   1✅:   0.0 days(    5 GB/    5 GB)→./sql_backup.2022-04-02.tgz
#   2✅:   3.0 days(    5 GB/    9 GB)→./sql_backup.2022-03-30.tgz
#   3✅:   4.0 days(    5 GB/   14 GB)→./sql_backup.2022-03-29.tgz
#   4✅:   5.0 days(    5 GB/   18 GB)→./sql_backup.2022-03-28.tgz
#   5✅:   7.0 days(    5 GB/   23 GB)→./sql_backup.2022-03-26.tgz
#   6✅:   9.0 days(    5 GB/   27 GB)→./sql_backup.2022-03-24.tgz
#   7✅:  11.0 days(    5 GB/   32 GB)→./sql_backup.2022-03-22.tgz
#   8❌:  15.0 days(    5 GB/   37 GB)→./sql_backup.2022-03-18.tgz
#   9❌:  17.0 days(    5 GB/   41 GB)→./sql_backup.2022-03-16.tgz
#  10✅:  18.0 days(    5 GB/   46 GB)→./sql_backup.2022-03-15.tgz
...
# 269❌:1509.0 days(    4 GB/    1 TB)→./sql_backup.2018-02-12.tgz
kept 24 files   105 GB
```

A leading `✅` means the file is kept, `❌` means it would be (or will be,
with `-f`) deleted.

### Actual run with `-f`

```bash
expireBackups --ext .tgz -f
keeping 7 files for dayly backup
keeping 6 files for weekly backup
keeping 8 files for monthly backup
keeping 4 files for yearly backup
expiring 24 files dry run
#   1✅:   0.0 days(    5 GB/    5 GB)→./sql_backup.2022-04-02.tgz
#   2✅:   3.0 days(    5 GB/    9 GB)→./sql_backup.2022-03-30.tgz
#   3✅:   4.0 days(    5 GB/   14 GB)→./sql_backup.2022-03-29.tgz
#   4✅:   5.0 days(    5 GB/   18 GB)→./sql_backup.2022-03-28.tgz
#   5✅:   7.0 days(    5 GB/   23 GB)→./sql_backup.2022-03-26.tgz
#   6✅:   9.0 days(    5 GB/   27 GB)→./sql_backup.2022-03-24.tgz
#   7✅:  11.0 days(    5 GB/   32 GB)→./sql_backup.2022-03-22.tgz
#   8✅:  18.0 days(    5 GB/   37 GB)→./sql_backup.2022-03-15.tgz
#   9✅:  35.0 days(    4 GB/   41 GB)→./sql_backup.2022-02-26.tgz
#  10✅:  43.0 days(    4 GB/   46 GB)→./sql_backup.2022-02-18.tgz
#  11✅:  50.0 days(    4 GB/   50 GB)→./sql_backup.2022-02-11.tgz
#  12✅:  58.0 days(    4 GB/   54 GB)→./sql_backup.2022-02-03.tgz
#  13✅:  65.0 days(    4 GB/   59 GB)→./sql_backup.2022-01-27.tgz
#  14✅:  94.0 days(    4 GB/   63 GB)→./sql_backup.2021-12-29.tgz
#  15✅: 148.0 days(    4 GB/   67 GB)→./sql_backup.2021-11-05.tgz
#  16✅: 177.0 days(    4 GB/   71 GB)→./sql_backup.2021-10-07.tgz
#  17✅: 205.0 days(    4 GB/   75 GB)→./sql_backup.2021-09-09.tgz
#  18✅: 236.0 days(    4 GB/   80 GB)→./sql_backup.2021-08-09.tgz
#  19✅: 267.0 days(    4 GB/   84 GB)→./sql_backup.2021-07-09.tgz
#  20✅: 295.0 days(    4 GB/   87 GB)→./sql_backup.2021-06-11.tgz
#  21✅: 324.0 days(    4 GB/   91 GB)→./sql_backup.2021-05-13.tgz
#  22✅: 691.0 days(    6 GB/   97 GB)→./sql_backup.2020-05-11.tgz
#  23✅:1062.0 days(    5 GB/  102 GB)→./sql_backup.2019-05-06.tgz
#  24✅:1426.0 days(    4 GB/  105 GB)→./sql_backup.2018-05-07.tgz
kept 24 files   105 GB
```

After the first `-f` run, running the same command again is a no-op: only
the 24 kept files remain, all within their retention windows.

### Debug dry run

`-d` prints each rule evaluation (`Δ age_diff(headroom_after_freq)`):

```bash
expireBackups --ext .tgz -d
keeping 7 files for dayly backup
Δ 0(-1.0) days for dayly(1.0) 1/7   0.0 days ✅(    5 GB):./sql_backup.2022-04-02.tgz
Δ 3(2.0) days for dayly(1.0) 2/7   3.0 days ✅(    5 GB):./sql_backup.2022-03-30.tgz
Δ 1(0.0) days for dayly(1.0) 3/7   4.0 days ✅(    5 GB):./sql_backup.2022-03-29.tgz
Δ 1(0.0) days for dayly(1.0) 4/7   5.0 days ✅(    5 GB):./sql_backup.2022-03-28.tgz
Δ 2(1.0) days for dayly(1.0) 5/7   7.0 days ✅(    5 GB):./sql_backup.2022-03-26.tgz
Δ 2(1.0) days for dayly(1.0) 6/7   9.0 days ✅(    5 GB):./sql_backup.2022-03-24.tgz
Δ 2(1.0) days for dayly(1.0) 7/7  11.0 days ✅(    5 GB):./sql_backup.2022-03-22.tgz
keeping 6 files for weekly backup
Δ 7(0.0) days for weekly(7.0) 1/6  18.0 days ✅(    5 GB):./sql_backup.2022-03-15.tgz
Δ 17(10.0) days for weekly(7.0) 2/6  35.0 days ✅(    4 GB):./sql_backup.2022-02-26.tgz
Δ 8(1.0) days for weekly(7.0) 3/6  43.0 days ✅(    4 GB):./sql_backup.2022-02-18.tgz
Δ 7(0.0) days for weekly(7.0) 4/6  50.0 days ✅(    4 GB):./sql_backup.2022-02-11.tgz
Δ 8(1.0) days for weekly(7.0) 5/6  58.0 days ✅(    4 GB):./sql_backup.2022-02-03.tgz
Δ 7(0.0) days for weekly(7.0) 6/6  65.0 days ✅(    4 GB):./sql_backup.2022-01-27.tgz
keeping 8 files for monthly backup
Δ 29(1.0) days for monthly(28.0) 1/8  94.0 days ✅(    4 GB):./sql_backup.2021-12-29.tgz
Δ 54(26.0) days for monthly(28.0) 2/8 148.0 days ✅(    4 GB):./sql_backup.2021-11-05.tgz
Δ 29(1.0) days for monthly(28.0) 3/8 177.0 days ✅(    4 GB):./sql_backup.2021-10-07.tgz
Δ 28(0.0) days for monthly(28.0) 4/8 205.0 days ✅(    4 GB):./sql_backup.2021-09-09.tgz
Δ 31(3.0) days for monthly(28.0) 5/8 236.0 days ✅(    4 GB):./sql_backup.2021-08-09.tgz
Δ 31(3.0) days for monthly(28.0) 6/8 267.0 days ✅(    4 GB):./sql_backup.2021-07-09.tgz
Δ 28(0.0) days for monthly(28.0) 7/8 295.0 days ✅(    4 GB):./sql_backup.2021-06-11.tgz
Δ 29(1.0) days for monthly(28.0) 8/8 324.0 days ✅(    4 GB):./sql_backup.2021-05-13.tgz
keeping 4 files for yearly backup
Δ 367(3.0) days for yearly(364.0) 1/4 691.0 days ✅(    6 GB):./sql_backup.2020-05-11.tgz
Δ 371(7.0) days for yearly(364.0) 2/41062.0 days ✅(    5 GB):./sql_backup.2019-05-06.tgz
Δ 364(0.0) days for yearly(364.0) 3/41426.0 days ✅(    4 GB):./sql_backup.2018-05-07.tgz
```

### Try it risk-free with test files

`--createTestFiles N` generates N dummy files with fake mtimes so you can
experiment without touching your real backups:

```bash
expireBackups --createTestFiles 30
created 30 test files with extension '.tst' in /tmp
Please try out
expireBackups --rootPath /tmp --baseName expireBackup --ext .tst --minFileSize 0
then try appending the -f option to the command that will actually delete files
(which are in a temporary directory) and run the command another time with that
option to see that no files are deleted any more on second run

expireBackups --rootPath /tmp --baseName expireBackup --ext .tst --minFileSize 0
keeping 7 files for dayly backup
keeping 6 files for weekly backup
expiring 30 files dry run
#   1✅:   1.0 days(    0  B/    0  B)→/tmp/expireBackupTest-1daysOld-ss9tl1g_.tst
#   2✅:   2.0 days(    0  B/    0  B)→/tmp/expireBackupTest-2daysOld-j4m0jk00.tst
#   3✅:   3.0 days(    0  B/    0  B)→/tmp/expireBackupTest-3daysOld-q7b8de0g.tst
#   4✅:   4.0 days(    0  B/    0  B)→/tmp/expireBackupTest-4daysOld-xqa8z0k8.tst
#   5✅:   5.0 days(    0  B/    0  B)→/tmp/expireBackupTest-5daysOld-mrqx5raw.tst
#   6✅:   6.0 days(    0  B/    0  B)→/tmp/expireBackupTest-6daysOld-y0gunu9t.tst
#   7✅:   7.0 days(    0  B/    0  B)→/tmp/expireBackupTest-7daysOld-2par7sek.tst
#   8❌:   8.0 days(    0  B/    0  B)→/tmp/expireBackupTest-8daysOld-jg9_fpin.tst
...
#  14✅:  14.0 days(    0  B/    0  B)→/tmp/expireBackupTest-14daysOld-x4mpow_c.tst
...
#  21✅:  21.0 days(    0  B/    0  B)→/tmp/expireBackupTest-21daysOld-g_mq3yke.tst
...
#  28✅:  28.0 days(    0  B/    0  B)→/tmp/expireBackupTest-28daysOld-fk4c5m9q.tst
#  29❌:  29.0 days(    0  B/    0  B)→/tmp/expireBackupTest-29daysOld-nwmyvgf8.tst
#  30❌:  30.0 days(    0  B/    0  B)→/tmp/expireBackupTest-30daysOld-5ncjuw56.tst
kept 10 files     0  B
```

## Cron example

```cron
# daily at 02:00 — keep 7 daily, 4 weekly, 6 monthly backups
0 2 * * * expireBackups --rootPath /var/backups --ext .tgz \
             --days 7 --weeks 4 --months 6 --years 0 -f \
             >> /var/log/expirebackups.log 2>&1
```

Make sure the backup job that produces the files has finished before
`expireBackups` runs, and that both start and finish on the same calendar day.

## Library usage

```python
from expirebackups.expire import ExpireBackups, Expiration

expiration = Expiration(days=7, weeks=4, months=6, years=2, minFileSize=1024)
eb = ExpireBackups(
    rootPath="/var/backups",
    ext=".tgz",
    expiration=expiration,
    dryRun=True,
)
eb.doexpire(withDelete=False)   # dry run
# eb.doexpire(withDelete=True)  # really delete
```

Key classes (in `expirebackups/expire.py`):

* `BackupFile` — one file on disk with age, size and kept/expire flag
* `ExpirationRule` — one retention tier (frequency in days, minimum count)
* `Expiration` — bundle of daily/weekly/monthly/yearly rules
* `ExpireBackups` — glue that scans the directory and applies the rules

## Development

```bash
git clone https://github.com/WolfgangFahl/pyExpireBackups.git
cd pyExpireBackups
pip install -e ".[test,dev]"
scripts/test       # run unit tests
scripts/blackisort # format (black + isort)
```

## Project history

Initial tickets that shaped the tool (all closed):

| # | Title |
| -: | ----- |
| 1 | refactor com.bitplan.backup Java solution |
| 2 | allow to create TestFiles via commandLine |
| 3 | show # age and size of file and total (sum) of file sizes |
| 4 | allow to specify minimum size of files |
| 5 | allow dry run |
| 6 | show debug information |
| 7 | show summary about kept files |
| 8 | always keep the most recent file |
| 11 | weird selection of files to keep — fixed in 0.1.2 (sub-day age) and 0.1.3 (cron-drift / calendar-day rule) |

## Further documentation

* API docs: https://WolfgangFahl.github.io/pyExpireBackups/
* Wiki: http://wiki.bitplan.com/index.php/PyExpireBackups

## Authors

* [Wolfgang Fahl](http://www.bitplan.com/Wolfgang_Fahl)

## License

Apache License 2.0 — see [LICENSE](LICENSE).

[#11]: https://github.com/WolfgangFahl/pyExpireBackups/issues/11
