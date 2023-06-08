#!/bin/bash

# $1 是 docker tag, 如果不传入, 默认为 latest
docker_tag=${1:-latest}

current_file_path=$(cd "$(dirname "$0")" || exit 2; pwd)

rm -rf "$current_file_path"/../program/logs

# 记录当前路径，docker 镜像构建完成后，回到当前路径
current_path=$(pwd)
cd "$current_file_path"/../ || exit 2
docker build -t bayonetta:"$docker_tag" .
cd "$current_path" || exit 2
