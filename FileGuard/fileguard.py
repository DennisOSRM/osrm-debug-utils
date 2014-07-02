#!/usr/bin/env python2
#
# Runs the commands in CMDS and checks paths that are passed to open()
# with a whitelist of regexp patterns.
#

import time
import subprocess
import re
import shlex
import sys

LOGPATH = "fileguard.log"
STRACE_CMD = "strace -e trace=open -o %(strace-log)s "
PARAMS = {
    'osm-data':  "berlin-latest.osm.pbf",
    'osrm-data': "berlin-latest.osrm",
    'profile':   "../profile.lua",
    'strace-log': "strace.log"
}
CMDS = [
"./osrm-extract %(osm-data)s -p %(profile)s",
"./osrm-prepare %(osrm-data)s -p %(profile)s",
"./osrm-datastore %(osrm-data)s",
"./osrm-routed -s",
"./osrm-routed %(osrm-data)s"
]
# -1 means wait for termination
TIMEOUTS = [
-1.0,
-1.0,
-1.0,
5.0,
5.0,
]
WHITELIST = [
"^/proc/.*",
"^/sys/.*",
"^/dev/shm/.*",
"^/tmp/OSRM-.*",
"^/dev/urandom",
"^/etc/ld.so.cache",
".*\.so[\.\d]*$",
"%(profile)s",
"%(osm-data)s",
"%(osrm-data)s",
"%(osrm-data)s.ramIndex",
"%(osrm-data)s.fileIndex",
"%(osrm-data)s.nodes",
"%(osrm-data)s.edges",
"%(osrm-data)s.restrictions",
"%(osrm-data)s.geometries",
"%(osrm-data)s.hsgr",
"%(osrm-data)s.names",
".*\.stxxl$",
".*stxxl.log$",
".*stxxl.errlog$",
"^/usr/lib/locale/.*",
"^/usr/lib/gconv/gconv-modules.cache",
"^/usr/lib/gconv/gconv-modules",
"^/usr/lib/x86_64-linux-gnu/gconv/gconv-modules.cache",
"^/usr/lib/x86_64-linux-gnu/gconv/gconv-modules",
"^/var/tmp/stxxl"
]

whitelist_cache = [re.compile(p % PARAMS) for p in WHITELIST]
def check_whitelist(fn):
    for p in whitelist_cache:
        if p.match(fn):
            return True
    return False

def process_log(filename):
    suspicious_files = []
    with open(filename) as log:
        lines = log.readlines()
        open_call = re.compile("^open\(\"([^\"\)]*)\", [^\)]*\)")
        for l in lines:
            m = open_call.match(l)
            if m:
                fn = m.group(1)
                if not check_whitelist(fn):
                    suspicious_files.append(fn)
    return suspicious_files

def run_cmd(cmd, timeout):
    full_cmd = (STRACE_CMD + cmd) % PARAMS
    cli = shlex.split(full_cmd)
    p = subprocess.Popen(cli)
    if timeout > 0:
        time.sleep(timeout)
        # kill process and children
        subprocess.call(shlex.split("pkill -P %i" % p.pid))
    p.wait()
    return process_log(PARAMS['strace-log'])

if len(TIMEOUTS) != len(CMDS):
    stderr.write("Error: You forgot to add or remove a timeout value!")
    sys.exit(1)

num_suspicous = 0
with open(LOGPATH, "w+") as log:
    for i in range(len(CMDS)):
        suspicious_files = run_cmd(CMDS[i], TIMEOUTS[i])
        if len(suspicious_files) > 0:
            num_suspicous += len(suspicious_files)
            log.write("For command %s the following files are suspicious:\n" % CMDS[i])
            for f in suspicious_files:
                log.write("%s\n" % f)

if num_suspicous > 0:
    sys.exit(1)
else:
    sys.exit(0)

