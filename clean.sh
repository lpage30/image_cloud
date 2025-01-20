#!/bin/bash
script_path=$( cd -- "$(dirname "${BASH_SOURCE[0]}x")" >/dev/null 2>&1 ; pwd -P )

rm -rf ${script_path}/build/
rm -rf ${script_path}/dist/
rm -rf ${script_path}/imagecloud.egg-info/
rm -rf ${script_path}/imagecloud/__pycache__/
rm -f ${script_path}/imagecloud/*.c
rm -f ${script_path}/imagecloud/*.so
rm -f ${script_path}/*.so
rm -f ${script_path}/imagecloud/*.html