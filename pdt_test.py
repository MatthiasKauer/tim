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

    isostring= ret_utc.isoformat()

    print(isostring)
    ret_loc2 = cal.parseDT(isostring)[0]
    print(ret_loc2)

    test_str= "2015-06-26T23:30:00+0000"

    #%z is only available after Python 3.2; http://stackoverflow.com/a/23122493
    if(sys.version_info > (3,2)):
        ret_loc3 = datetime.strptime(test_str, '%Y-%m-%dT%H:%M:%S%z')
        print("test %z", ret_loc3)

    custom_str = datetime.strftime(ret_utc, '%Y-%m-%dT%H:%M:%SZ')
    ret_loc4 = pytz.utc.localize(datetime.strptime(custom_str, '%Y-%m-%dT%H:%M:%SZ'))
    print(ret_loc4)

if __name__ == '__main__':
    parse_args()
