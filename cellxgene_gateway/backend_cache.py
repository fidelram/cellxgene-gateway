# Copyright 2019 Novartis Institutes for BioMedical Research Inc. Licensed
# under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0. Unless
# required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
# OR CONDITIONS OF ANY KIND, either express or implied. See the License for
# the specific language governing permissions and limitations under the License.

import time
from threading import Thread

from flask_api import status

from cellxgene_gateway import env
from cellxgene_gateway.cache_entry import CacheEntry
from cellxgene_gateway.cellxgene_exception import CellxgeneException
from cellxgene_gateway.subprocess_backend import SubprocessBackend

process_backend = SubprocessBackend()


class BackendCache:
    def __init__(self):
        self.entry_list = []

    def get_ports(self):
        contents = self.entry_list
        return [c.port for c in contents]

    def check_entry(self, dataset):
        contents = self.entry_list
        matches = [c for c in contents if c.dataset == dataset and c.status != "terminated"]

        if len(matches) == 0:
            return None
        elif len(matches) == 1:
            return matches[0]
        else:
            raise CellxgeneException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Found " + str(len(matches)) + " for " + dataset,
            )

    def create_entry(self, dataset, file_path, scripts):
        port = 8000
        existing_ports = self.get_ports()
        while port in existing_ports:
            port += 1

        entry = CacheEntry.for_dataset(dataset, file_path, port)

        background_thread = Thread(
            target=process_backend.launch,
            args=(env.cellxgene_location, scripts, entry),
        )
        background_thread.start()

        self.entry_list.append(entry)

        time.sleep(1)  # Automatic refresh is too fast, needs a second to pause

        return entry
    
    def prune(self, process):
        self.entry_list.remove(process)
        process.terminate()
