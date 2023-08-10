FROM nvidia/cuda:12.2.0-devel-ubuntu20.04

WORKDIR /app

COPY * /app/

# RUN apt-get update && apt-get install -y python3-pip mecab libmecab-dev swig gcc build-essential ffmpeg

# RUN pip3 install torch==1.13.1+cu116 torchvision==0.14.1+cu116 torchaudio==0.13.1 --extra-index-url https://download.pytorch.org/whl/cu116 -i https://pypi.tuna.tsinghua.edu.cn/simple

# RUN pip3 install -r requirements.txt

# RUN cd monotonic_align && \
#     python3 setup.py build_ext --inplace && \
#     cp monotonic_align/*.pyd . && \
#     cd ..

RUN apt-get update && \
    apt-get install -y python3-pip mecab libmecab-dev swig gcc build-essential ffmpeg && \
    pip3 install torch==1.13.1+cu116 torchvision==0.14.1+cu116 torchaudio==0.13.1 --extra-index-url https://download.pytorch.org/whl/cu116 -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip3 install -r requirements.txt && \
    cd monotonic_align && \
    python3 setup.py build_ext --inplace && \
    cp monotonic_align/*.pyd . && \
    cd ..

CMD ["python3", "/app/tts_web_api/main.py"]
