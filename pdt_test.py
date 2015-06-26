from datetime import datetime
import parsedatetime as pdt
import sys
import pytz

# http://stackoverflow.com/questions/13218506/how-to-get-system-timezone-setting-and-pass-it-to-pytz-timezone
from tzlocal import get_localzone # $ pip install tzlocal
local_tz = get_localzone()

def parse_args(argv=sys.argv):
    cal = pdt.Calendar()
    timestr = ' '.join(argv)
    # ret = cal.parseDT(timestr, sourceTime=datetime.utcnow(), tzinfo=pytz.utc)[0]
    ret = cal.parseDT(timestr, tzinfo=local_tz)[0]
    ret_utc = ret.astimezone(pytz.utc)
    print(ret)
    print(ret_utc)

    ret_loc = ret_utc.astimezone(local_tz)
    print(ret_loc)

if __name__ == '__main__':
    parse_args()
