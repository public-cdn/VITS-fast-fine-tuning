FROM python:3.9-slim

WORKDIR /app

COPY * /app/
RUN apt-get update && apt-get install -y mecab libmecab-dev swig gcc build-essential
#RUN pip3 install -r requirements.txt  -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip3 install -r requirements.txt

RUN cd "monotonic_align"
RUN mkdir monotonic_align
RUN python setup.py build_ext --inplace
RUN cp monotonic_align/*.pyd .
RUN cd ..

CMD ["python3", "/app/tts_web_api/main.py"]
