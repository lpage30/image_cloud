#!/bin/bash
script_path=$( cd -- "$(dirname "${BASH_SOURCE[0]}x")" >/dev/null 2>&1 ; pwd -P )

source ${script_path}/clean.sh

pushd ${script_path}
python3 -m build
popd