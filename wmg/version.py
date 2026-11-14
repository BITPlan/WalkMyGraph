"""
Created on 2026-02-01

@author: wf
"""

from dataclasses import dataclass

import wmg


@dataclass
class Version:
    """
    Version handling for WalkMyGraph
    """

    name = "WalkMyGraph"
    version = wmg.__version__
    date = "2026-02-01"
    updated = "2026-11-14"
    description = "WalkMyGraph (WMG) is a specification by example software development using Knowledge Graph Traversals and Named Parameterized Queries"
    authors = "Wolfgang Fahl"
    doc_url = "https://wiki.bitplan.com/index.php/WalkMyGraph"
    chat_url = "https://github.com/BITPlan/WalkMyGraph/discussions"
    cm_url = "https://github.com/BITPlan/WalkMyGraph"
    license = """Copyright 2026 contributors. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied."""

    longDescription = f"""{name} version {version}
{description}

  Created by {authors} on {date} last updated {updated}"""
