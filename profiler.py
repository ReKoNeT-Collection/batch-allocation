import atexit
from datetime import datetime

import yappi

from app import create_app


# End profiling and save the results into file
def output_profiler_stats_file():
    profile_file_name = 'yappi.' + datetime.now().isoformat()
    func_stats = yappi.get_func_stats()
    func_stats.save(profile_file_name, type='pstat')
    yappi.stop()
    yappi.clear_stats()


yappi.start()
atexit.register(output_profiler_stats_file)

# Flask app launch code
app = create_app()
