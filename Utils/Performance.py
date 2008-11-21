
import threading, traceback, cgi
import datetime

perf_data = threading.local()

def start_report():
    perf_data.start = True
    perf_data.miss = 0
    perf_data.hit  = 0
    perf_data.sql  = [];
    perf_data.start_time = datetime.datetime.now()
    perf_data.attrs = {}

def add_sql(time, sql):
    if 'start' not in dir(perf_data) or not perf_data.start :
        return
    perf_data.sql.append( {'id':len(perf_data.sql), 'time': time, 'sql': cgi.escape(sql), 'traceback': cgi.escape("".join(traceback.format_stack())) })
#    perf_data.sql.append( (time, sql + "\n\n\n" + "\n".join(traceback.format_stack()) ))

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
    if not len(perf_data.sql) and perf_data.miss==0 and perf_data.hit==0:
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
                <h1>Performance report</h1>"""

    t2 = datetime.datetime.now()
    dt = t2-perf_data.start_time
    woot = dt.seconds + 0.000001* dt.microseconds

    res += "Total rendering time: %.1f s<br/>" % woot
    res += "Total query time: %.1f s<br/>" % reduce(lambda x, y: x+y['time'], perf_data.sql, 0.0)
    res += "Total number of queries: %d<br/>" % len(perf_data.sql)

    res += "<hr>Cache hits: %s <br/>Cache misses: %s<br/>" % (perf_data.hit, perf_data.miss)

    for i in sorted(perf_data.sql,lambda x, y: cmp(x['time'],y['time']),reverse=True):
        res += """<hr/>
        Query time: %(time).4f s<br/>
        Query:<pre>%(sql)s</pre>
        Traceback:<button onclick="toggleVisible(getElementById('traceback_%(id)d'));">+</button><pre id='traceback_%(id)d' style='display: none;'>%(traceback)s</pre>""" % i

#    res += "<hr/>\nAttribute access statistics:\n"
#    for i in sorted(map(lambda x: (x[1],x[0]), perf_data.attrs.iteritems()), reverse=True):
#        res += "Count: %d name:%s<br/>\n" % i

    res += "</body></html>"
    perf_data.start=False
    return res

