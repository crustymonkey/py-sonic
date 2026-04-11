"""
This file is part of py-opensonic.

py-opensonic is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

py-opensonic is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with py-opensonic.  If not, see <http://www.gnu.org/licenses/>

Generate the synchronous connection from the async one using unasync.
"""

from pathlib import Path

import unasync

def run_unasync():
    """ Do the thing. """
    rules = [
        unasync.Rule(
            fromdir="src/libopensonic/_async/",
            todir="src/libopensonic/_sync/",
            additional_replacements={
                "AsyncConnection": "Connection",
                "aiohttp": "requests",
                "ClientResponse": "Response",
                "ClientSession": "Session",
            },
        ),
    ]

    src_path = Path("src/libopensonic/_async")
    filepaths = [str(p) for p in src_path.glob("*.py")]

    if filepaths:
        # 1. Run the standard unasync transformation
        unasync.unasync_files(filepaths, rules)

        # 2. Perform post-processing for complex strings that unasync can't catch
        # Target the generated sync directory
        sync_path = Path("src/libopensonic/_sync")
        for p in sync_path.glob("*.py"):
            content = p.read_text()
            updated = False

            # Use the string that unasync partially generated (requests.ClientTimeout...)
            target = "requests.ClientTimeout(total=None, sock_connect=30, sock_read=60)"
            if target in content:
                content = content.replace(target, "(30, 60)")
                updated = True

            target = "req_kwargs = {}"
            if target in content:
                content = content.replace(target, "")
                updated = True

            target = ", **req_kwargs"
            if target in content:
                content = content.replace(target, ", stream=is_stream")
                updated = True

            target = "def _do_request(self, method: str, query: dict | None = None)"
            if target in content:
                replace = "def _do_request(self, method: str, query: dict | None = None, is_stream: bool = False)"
                content = content.replace(target, replace)
                updated = True

            target = "('getCoverArt', q)"
            if target in content:
                content = content.replace(target, "('getCoverArt', q, is_stream=True)")
                updated = True

            target = "('stream', q)"
            if target in content:
                content = content.replace(target, "('stream', q, is_stream=True)")
                updated = True

            if updated:
                p.write_text(content)


if __name__ == "__main__":
    run_unasync()
