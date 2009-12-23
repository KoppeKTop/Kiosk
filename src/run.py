#!/usr/bin/env python

import os, sys

#null_file = '/dev/null'

def Run(prog, args=[], silent=False):
    args.insert(0, prog)
    pid = os.fork()
    if not pid:
        try:
#            if (silent):
#                import subprocess
#                with open(os.devnull, 'w') as f:
#                    subprocess.Popen(args,
#                     stdout=f,
#                     stderr=f)
#            else:
            os.execvp(prog, args)
            sys.exit(0)
        except:
            try:
                os.execv(prog, args)
                sys.exit(0)
            except:
                return 0
    return pid
