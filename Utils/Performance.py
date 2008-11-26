
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
    
    getattr(perf_data,perf_type).append( {'id':len(getattr(perf_data,perf_type)), 'time': time, 'text': cgi.escape(text), 'traceback': cgi.escape("".join(traceback.format_stack())), 'type': perf_type })

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

    res = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
"http://www.w3.org/TR/html4/strict.dtd">
<html>
        <head>
                <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
                <style type="text/css">
body
{
        font-size: small;
        font-family: "Bitstream Charter";
}

button
{
        width: 1.6em;
        height: 1.6em;
        border: 1px solid black;
        background: white;
        margin: 0px;
        padding: 0px;
}

ul li
{
        list-style: none;
}

th
{
        text-align: left;
}

                </style>
		<script type="text/javascript">

function toggleVisible(el, btn)
{
    if(el.style.display=='none') {
        el.style.display = 'block';
        btn.innerHTML = '-'
    } else {
        el.style.display = 'none';
        btn.innerHTML = '+'
    }
}

		</script>
                <title>Performance report</title>
        </head>
        <body>
                <h1><a name='anchor_top'>Performance report</a></h1>
"""

    res += """
                <h2>Table of contents</h2>
                <ul>
                        <li><a href='#anchor_overview'>Overview</a></li>
"""
    for perf_type in perf_data.added:
        res += """
                        <li><a href='#anchor_%(type)s'>Details for %(type)s</a></li>
""" % {'type':perf_type}
    res += """
                </ul>
                <h2><a name='anchor_overview'>Overview</a></h2>
"""
        
    t2 = datetime.datetime.now()
    dt = t2-perf_data.start_time
    woot = dt.seconds + 0.000001* dt.microseconds

    res += """
                <table>
                        <tbody>
                                <tr>
                                        <th>Total rendering time</th>
                                        <td>%.1f s</td>
                                </tr>
""" % woot

    for perf_type in perf_data.added:
        res += """
                                <tr>
                                        <th>Total %s time</th>
                                        <td> %.1f s</td>
                                </tr>
""" % (perf_type, reduce(lambda x, y: x+y['time'], getattr(perf_data,perf_type), 0.0))
        res += """
                                <tr>
                                        <th>Total number of %s calls</th>
                                        <td>%d</td>
                                </tr>
""" % (perf_type, len(getattr(perf_data,perf_type)))

    res += """
                        </tbody>
                </table>
		<hr>
                <p>
                Cache hits: %s <br>
                Cache misses: %s<br>
                </p>
                <p>
                <a href='#anchor_top'>Back to top</a>
                </p>
""" % (perf_data.hit, perf_data.miss)

    for perf_type in perf_data.added:
        res +=  """
                <h2><a name='anchor_%(type)s'>Details for %(type)s</a></h2>
""" % {'type':perf_type}
        for i in sorted(getattr(perf_data,perf_type),lambda x, y: cmp(x['time'],y['time']),reverse=True):
            res += """
		<hr>
                <p>
		Query time: %(time).4f s<br>
		Query:</p>
                <pre>%(text)s</pre>
                <p>
		Traceback:
		<button onclick="toggleVisible(getElementById('traceback_%(type)s_%(id)d'), getElementById('button_%(type)s_%(id)d'));" id='button_%(type)s_%(id)d'>+</button>
                </p>
		<pre id='traceback_%(type)s_%(id)d' style='display: none;'>%(traceback)s
                </pre>
""" % i
        res += """
                <p>
                <a href='#anchor_top'>Back to top</a>
                </p>
"""        
    res += """
                <p>
                        <a href="http://validator.w3.org/check?uri=referer"><img
        src="http://www.w3.org/Icons/valid-html401-blue"
        alt="Valid HTML 4.01 Strict" height="31" width="88">
                        </a>
                </p>
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
