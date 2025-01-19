#!/bin/bash
script_path=$( cd -- "$(dirname "${BASH_SOURCE[0]}x")" >/dev/null 2>&1 ; pwd -P )

call ${script_path}/clean.sh

pushd ${script_path}
python3 -m build
popd