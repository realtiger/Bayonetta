# 当前目录
file_absolute_path=$(readlink -f "$0")
dir_absolute_path=$(dirname "$file_absolute_path")

# docker命令是否存在
if ! command -v docker &>/dev/null; then
    echo "docker is not installed"
    exit 1
fi

# 保证 redis 容器存在并且在运行
if docker ps -a | grep redis | grep -q Up; then
    echo "redis 容器正在运行"
else
    # 判断 docker 中是否有 redis 容器
    if docker ps -a | grep redis | grep -q Exited; then
        echo "redis 容器是停止状态，正在启动..."
        # 启动 redis 容器
        docker start redis
        if docker ps -a | grep redis | grep -q Up; then
            echo "redis 容器启动成功"
        else
            echo "redis 容器启动失败"
            exit 1
        fi
    else
        echo "redis 容器不存在，正在创建..."

        echo "创建 redis 容器空间"
        mkdir -p /data/docker/redis/data
        mkdir -p /data/docker/redis/conf

        echo "复制 redis 配置文件"
        cp -f "$dir_absolute_path"/development_environment_files/redis.conf /data/docker/redis/conf/redis.conf

        echo "创建 redis 容器"
        docker run -d --restart=always --name redis -p 6379:6379 -v /data/docker/redis/data:/data -v /data/docker/redis/conf/redis.conf:/etc/redis/redis.conf redis:7.2-alpine redis-server /etc/redis/redis.conf --appendonly yes
        if docker ps -a | grep redis | grep -q Up; then
            echo "redis 容器创建成功"
        else
            echo "redis 容器创建失败"
            exit 1
        fi
    fi
fi

# 保证 mariadb 容器存在并且在运行
if docker ps -a | grep mariadb | grep -q Up; then
    echo "mariadb 容器正在运行"
else
    # 判断 docker 中是否有 mariadb 容器
    if docker ps -a | grep mariadb | grep -q Exited; then
        echo "mariadb 容器是停止状态，正在启动..."
        # 启动 mariadb 容器
        docker start mariadb
        if docker ps -a | grep mariadb | grep -q Up; then
            echo "mariadb 容器启动成功"
        else
            echo "mariadb 容器启动失败"
            exit 1
        fi
    else
        echo "mariadb 容器不存在，正在创建..."

        echo "创建 mariadb 容器空间"
        mkdir -p /data/docker/mariadb/data

        echo "创建 mariadb 容器"
        docker run -d --restart=always --name mariadb -p 3306:3306 -v /data/docker/mariadb/data:/var/lib/mysql \
          -e MARIADB_ROOT_PASSWORD=mysql1! -e MARIADB_DATABASE=cereza -e MARIADB_USER=user -e MARIADB_PASSWORD=pass \
          mariadb:10.5.12 \
          --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
        if docker ps -a | grep mariadb | grep -q Up; then
            echo "mariadb 容器创建成功"
        else
            echo "mariadb 容器创建失败"
            exit 1
        fi
    fi
fi
