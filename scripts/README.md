脚本信息如下：

1. 运行环境

   run_development_environment.sh 用于设置运行环境，包括：

    - redis 默认端口 6379 默认密码 redispass
    - mariadb 默认端口 3306 默认数据库 cereza 默认用户 user 默认密码 pass

   运行方法：

    ```bash
    bash run_development_environment.sh
    ```

2. 生成数据库迁移文件

   makemigrations.sh 用于生成数据库迁移文件

    ```bash
    bash makemigrations.sh "message"
    ```

3. 执行数据库迁移

   migrate.sh 用于执行数据库迁移

    ```bash
    bash migrate.sh
    ```

4. 创建项目镜像

   build.sh 用于创建项目镜像，参数为镜像版本号，最终的镜像名为：`bayonetta:${version}`

    ```bash
    bash build.sh "v230822"
    ```
