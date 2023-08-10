# 使用多阶段构建
# 第一阶段：构建镜像
FROM nvidia/cuda:12.2.0-devel-ubuntu20.04 as builder

WORKDIR /app

# 复制所有文件到/app目录下
COPY * /app/

# 安装依赖项，清理缓存
RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    apt-get install -y tzdata python3-pip mecab libmecab-dev swig gcc build-essential ffmpeg && \
    ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    dpkg-reconfigure --frontend noninteractive tzdata && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install torch==1.13.1+cu116 torchvision==0.14.1+cu116 torchaudio==0.13.1 --extra-index-url https://download.pytorch.org/whl/cu116 -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip3 install -r requirements.txt && \
    rm -rf ~/.cache/pip

# 构建monotonic_align
RUN cd monotonic_align && \
    python3 setup.py build_ext --inplace && \
    cp monotonic_align/*.pyd . && \
    cd ..

# 第二阶段：运行镜像
FROM nvidia/cuda:12.2.0-devel-ubuntu20.04

WORKDIR /app

# 从builder镜像中复制所需的文件
COPY --from=builder /app /app

CMD ["python3", "/app/tts_web_api/main.py"]
