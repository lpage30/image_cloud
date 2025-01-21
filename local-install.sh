#!/bin/bash
script_path=$( cd -- "$(dirname "${BASH_SOURCE[0]}x")" >/dev/null 2>&1 ; pwd -P )

source ${script_path}/build.sh

pushd ${script_path}
python3 -m pip install -e . --break-system-packages
popd