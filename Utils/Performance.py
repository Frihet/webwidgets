
import threading, traceback, cgi
import datetime

perf_data = threading.local()

def start_report():
    perf_data.start = True
    perf_data.miss = 0
    perf_data.hit  = 0
    perf_data.start_time = datetime.datetime.now()
    perf_data.attrs = {}
    perf_data.added = {}

def add_sql(time, text):
    add('sql', text, time)

def add(perf_type, text, time):
    if 'start' not in dir(perf_data) or not perf_data.start :
        return
    if perf_type not in dir(perf_data):
        setattr(perf_data,perf_type,[])

    perf_data.added[perf_type] = perf_type
    
    getattr(perf_data,perf_type).append( {'id':len(getattr(perf_data,perf_type)), 'time': time, 'text': cgi.escape(text), 'traceback': cgi.escape("".join(traceback.format_stack())) })

def add_miss():
    if 'start' not in dir(perf_data) or not perf_data.start :
        return
    perf_data.miss += 1

def add_hit():
    if 'start' not in dir(perf_data) or not perf_data.start :
        return
    perf_data.hit += 1

def add_attr(attr):
    if 'start' not in dir(perf_data) or not perf_data.start :
        return
    if attr not in perf_data.attrs:
        perf_data.attrs[attr] = 1
    else:
        perf_data.attrs[attr] += 1


class NoReportAvailable(Exception):
    pass


def get_report():
    if 'start' not in dir(perf_data) or not perf_data.start :
        raise NoReportAvailableError
    if not len(perf_data.added) and perf_data.miss==0 and perf_data.hit==0:
        return None

    res = """
<html>
        <head>
		<script>

function toggleVisible(el)
{
    if(el.style.display=='none') {
        el.style.display = 'block';
        this.innerHTML = '-'
    } else {
        el.style.display = 'none';
        this.innerHTML = '+'
    }
}

		</script>
        </head>
        <body>
                <h1>Performance report</h1>
"""

    t2 = datetime.datetime.now()
    dt = t2-perf_data.start_time
    woot = dt.seconds + 0.000001* dt.microseconds

    res += "\t\tTotal rendering time: %.1f s<br/>\n" % woot
    for perf_type in perf_data.added:
        res += "\t\tTotal %s time: %.1f s<br/>\n" % (perf_type, reduce(lambda x, y: x+y['time'], getattr(perf_data,perf_type), 0.0))
        res += "\t\tTotal number of %s items: %d<br/>\n" % (perf_type, len(getattr(perf_data,perf_type)))

    res += """
		<hr/>
                Cache hits: %s <br/>
                Cache misses: %s<br/>
""" % (perf_data.hit, perf_data.miss)

    for perf_type in perf_data.added:
        res +=  """
                <h2>Details for %s</h2>
""" % perf_type
        for i in sorted(getattr(perf_data,perf_type),lambda x, y: cmp(x['time'],y['time']),reverse=True):
            res += """
		<hr/>
		Query time: %(time).4f s<br/>
		Query:<pre>%(text)s</pre>
		Traceback:
		<button onclick="toggleVisible(getElementById('traceback_%(id)d'));">+</button>
		<pre id='traceback_%(id)d' style='display: none;'>%(traceback)s
                </pre>
""" % i

    res += """
        </body>
</html>
"""
    perf_data.start=False
    return res



if __name__ == '__main__':
    start_report()
    add('sql', 'select hej', 0.1)
    add('sql', 'select hopp', 0.3)
    add('ldap', 'axel', 0.1)
    add('ldap', 'claes', 0.001)
    print get_report()
