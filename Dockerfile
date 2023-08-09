FROM python:3.9-slim

WORKDIR /app

COPY * /app/
RUN apt-get update && apt-get install -y mecab libmecab-dev swig gcc build-essential

RUN apt-get install ffmpeg ffmpeg-devel -y
RUN ffmpeg -h

RUN pip3 install -r requirements.txt

RUN cd monotonic_align && \
    python setup.py build_ext --inplace && \
    cp monotonic_align/*.pyd . && \
    cd ..

CMD ["python3", "/app/tts_web_api/main.py"]
