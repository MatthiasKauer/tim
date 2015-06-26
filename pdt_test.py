from datetime import datetime
import parsedatetime as pdt
import sys
import pytz

def parse_args(argv=sys.argv):
    cal = pdt.Calendar()
    timestr = ' '.join(argv)
    ret = cal.parseDT(timestr, sourceTime=datetime.utcnow(), tzinfo=pytz.utc)[0]

    # ret = make_local(ret)

    print(ret)

if __name__ == '__main__':
    parse_args()
