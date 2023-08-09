FROM python:3.9-slim

WORKDIR /app

COPY * /app/
RUN apt-get update && apt-get install -y mecab libmecab-dev swig gcc build-essential
RUN pip3 install -r requirements.txt  -i https://pypi.tuna.tsinghua.edu.cn/simple


CMD ["python3", "/app/tts_web_api/main.py"]
