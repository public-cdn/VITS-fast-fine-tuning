# 把 vits 的 tts 封装成API接口, 用于语音合成

## 用法

把 Dockerfile 放到 vits 的根目录下, 然后把模型文件放到 tts_web_api/model/{模型名} 目录下, 然后执行:  

```bash
docker build -t tts_web_api .
docker run -d -p 80:3232 tts_web_api
```

## tts_web_api/model/{模型名} 文件要有
* G_latest.pth
* moegoe_config.json

如果要用清华源来安装 python 包, 请把 `Dockerfile` 这一行该下
```
RUN pip3 install -r requirements.txt
```
改成
```
RUN pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 接口文档

### 模型列表
GET /models  

返回模型数组
```json
[
  "demo"
]
```

### 模型里的角色列表
GET /models/{模型名字}/speakers

返回模型里的角色列表, 格式: id:角色名  
```json
[
    {
        "id": 0,
        "name": "山吹八千代"
    },
    {
        "id": 1,
        "name": "大藏里想奈"
    },
    {
        "id": 2,
        "name": "樱小路露娜"
    },
    {
        "id": 3,
        "name": "水無月あいる"
    },
    {
        "id": 4,
        "name": "尤希尔"
    },
    {
        "id": 5,
        "name": "丹羽風薰"
    },
    {
        "id": 6,
        "name": "specialweek"
    },
    {
        "id": 7,
        "name": "zhongli"
    },
    {
        "id": 8,
        "name": "vctk"
    }
]
```


### 文字转语音
POST /models/{模型名字}/speakers/{角色ID}

参数:  
* text 需要转换的文字(必须), 如果是 language=Mix 的情况下就需要带上语言标签
* speed 语速(可选), 越小越慢, 默认为0.95
* noise_scale 感情变化程度(可选) 默认为 0.667
* noise_scale_w 音素发音长度(可选) 默认为0.8
* language 语言(可选) 默认为:简体中文, 选项有: 日本語, 简体中文,English

返回:   

wav 格式的文件
