# Bayonetta

### 介绍

Bayonetta 是一个通用的后端框架，crud 灵感来自 fastapi-crudrouter，做了一些本地化的修改。

### 软件架构

fastapi + sqlalchemy + pydantic

### 安装教程

1. 安装依赖
   ```
   poetry install
   ```
2. 设置环境变量
   ```
   export PYTHONPATH=$(pwd)/program
   ```
3. 修改配置文件
    
    目前项目中的配置文件使用 .env 文件，可以根据自己的需要修改配置文件。
    ```
    cp .env.example .env
    vim .env
    ```
3. 运行入口文件
    ```
    poetry python manager.py
    ```

### 使用说明

#### 单体安装

1. 安装依赖
   ```
   poetry install
   ```
2. 部署项目，这里使用拷贝举例
    ```
    cp -r program /opt/bayonetta
    ```
3. 启动项目
    ```
    cd /opt/bayonetta/program
    poetry run uvicorn main:app --reload
    ```

#### docker 安装

1. 构建镜像
    ```
    bash scripts/build.sh
    ```
   
2. 启动容器
    ```
    docker run -d -p 5000:5000 bayonetta:latest
    ```
   
3. 访问接口
    ```
    curl http://<yourIP>:5000
    ```

### 参与贡献

1. Fork 本仓库
2. 新建 Feat_xxx 分支
3. 提交代码
4. 新建 Pull Request
