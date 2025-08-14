# NodeSeekMCP

NodeSeek 论坛 MCP Server

## 如何启动项目？

### （✅必要）安装 docker

原理是利用 1panel 自动安装脚本，帮我们把 docker 装好

    1. 安装 1panel（到下面的链接，找到你当前系统对应的命令行，跟着提示下一步下一步下一步...）
    https://1panel.cn/docs/v2/installation/online_installation/#2
    
    2. 装好 1panel 后，输入下面的命令，一键卸载 1panel
    1pctl uninstall
    
    3. 此时 docker 不会被卸载，运行下面命令，如果输出版本则表示安装成功
    docker -v

### （✅必要）克隆项目

    git clone https://github.com/0x0208v0/NodeSeekMCP.git

### （🌟推荐）docker-compose 启动

    # 编译 docker 镜像
    docker-compose build 
    # 或者 
    docker compose build
    
    # 启动 docker 容器
    docker-compose up -d 
    # 或者 
    docker compose up -d

### docker 启动

    # 编译 docker 镜像
    docker build -f Dockerfile -t nodeseekmcp .
    
    # 启动 docker 容器（IPv4版）
    docker run -d \
      --name nodeseekmcp \
      --hostname nodeseekmcp \
      --user root \
      --workdir /opt/nodeseekmcp \
      --restart always \
      -v .:/opt/nodeseekmcp \
      --add-host host.docker.internal:host-gateway \
      --log-driver json-file \
      --log-opt max-size=100M \
      --log-opt max-file=10 \
      -p 0.0.0.0:80:8866 \
      nodeseekmcp:latest \
      sh -c "supervisord -c supervisor.conf -n"
    
    # 启动 docker 容器（IPv6版）
    docker run -d \
      --name nodeseekmcp \
      --hostname nodeseekmcp \
      --user root \
      --workdir /opt/nodeseekmcp \
      --restart always \
      -v .:/opt/nodeseekmcp \
      --add-host host.docker.internal:host-gateway \
      --log-driver json-file \
      --log-opt max-size=100M \
      --log-opt max-file=10 \
      -p [::]:80:8866 \
      nodeseekmcp:latest \
      sh -c "supervisord -c supervisor.conf -n"

## 其他

## 安装 mcp 调试工具

    nvm exec --lts npx --yes @modelcontextprotocol/inspector

## Cursor 配置 MCP Tools

```json
{
  "mcpServers": {
    "nodeseek": {
      "url": "http://xxx.yyy.com/sse",
      "env": {
        "API_KEY": "value"
      }
    }
  }
}
```
