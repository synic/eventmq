# This file is part of eventmq.
#
# eventmq is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option)
# any later version.
#
# eventmq is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with eventmq.  If not, see <http://www.gnu.org/licenses/>.
"""
:mod:`worker` -- Worker Classes
===============================
Defines different short-lived workers that execute jobs
"""
from importlib import import_module
import logging
from multiprocessing import Process

logger = logging.getLogger(__name__)


class MultiprocessWorker(Process):
    """
    Defines a worker that spans the job in a multiprocessing task
    """
    def __init__(self, input_queue, output_queue):
        super(MultiprocessWorker, self).__init__()
        self.input_queue = input_queue
        self.output_queue = output_queue

    def run(self):
        """
        process a run message and execute a job

        This is designed to run in a seperate process.
        """
        # Pull the payload off the queue and run it
        for payload in iter(self.input_queue.get, None):
            if ":" in payload["path"]:
                _pkgsplit = payload["path"].split(':')
                s_package = _pkgsplit[0]
                s_cls = _pkgsplit[1]
            else:
                s_package = payload["path"]
                s_cls = None

            s_callable = payload["callable"]

            package = import_module(s_package)
            if s_cls:
                cls = getattr(package, s_cls)

                if "class_args" in payload:
                    class_args = payload["class_args"]
                else:
                    class_args = ()

                if "class_kwargs" in payload:
                    class_kwargs = payload["class_kwargs"]
                else:
                    class_kwargs = {}

                obj = cls(*class_args, **class_kwargs)
                callable_ = getattr(obj, s_callable)
            else:
                callable_ = getattr(package, s_callable)

            if "args" in payload:
                args = payload["args"]
            else:
                args = ()

            if "kwargs" in payload:
                kwargs = payload["kwargs"]
            else:
                kwargs = {}

            try:
                callable_(*args, **kwargs)
            except Exception as e:
                logger.exception(e)

            # Signal that we're done with this job
            self.output_queue.put('DONE')