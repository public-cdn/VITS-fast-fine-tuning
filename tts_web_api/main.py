import bottle
import json
import os
import io
import vits_tts
import time
from scipy.io import wavfile
import schedule
import atexit
import threading
import signal

app = bottle.Bottle()
worker_thread = None
shutdown_event = threading.Event()

@app.route('/models')
def models():
    # 遍历当前目录下的 models 文件夹，返回所有目录名字, 只要文件夹
    models = []
    for model in os.listdir('models'):
        if os.path.isdir(os.path.join('models', model)):
            models.append(model)

    response = bottle.HTTPResponse(status=200, body=json.dumps(models), headers={'Content-Type': 'application/json'})
    return response

# 用于返回指定模型的所有speaker
@app.route('/models/<model_name>/speakers')
def speakers(model_name):
    # 读取该模型下面的 moegoe_config.json 文件，返回里面的 speakers 字段, 如果没有这个文件则返回404
    config_path = os.path.join('models', model_name, 'moegoe_config.json')
    if not os.path.exists(config_path):
        return bottle.HTTPResponse(status=404, body=json.dumps({"error": "moegoe_config.json is not found"}), headers={'Content-Type': 'application/json'})
    
    with open(config_path, 'r') as f:
        config = json.load(f)
        speakers = [] # 返回的 speaker, 格式 id: name
        
        i = 0
        for speaker in config['speakers']:
            speakers.append({
                'id': i,
                'name': speaker
            })
            i = i + 1
        response = bottle.HTTPResponse(status=200, body=json.dumps(speakers), headers={'Content-Type': 'application/json'})
        return response
    
# 进行 tts 转换
@app.route('/models/<model_name>/speakers/<speaker_id>', method='POST')
def tts(model_name, speaker_id):
    try:
        model = vits_tts.load_model(model_name)
    except ValueError as e:
        return bottle.HTTPResponse(status=404, body=json.dumps({"error": str(e)}), headers={'Content-Type': 'application/json'})
    
    if model is None:
        return bottle.HTTPResponse(status=404, body=json.dumps({"error": "model not found"}), headers={'Content-Type': 'application/json'})
    
    if int(speaker_id) not in model["speakers_ids"].keys():
        return bottle.HTTPResponse(status=404, body=json.dumps({"error": "speaker_id not found", "speakers_ids": model["speakers_ids"]}), headers={'Content-Type': 'application/json'})
    
    # text 字段必须存在
    if 'text' not in bottle.request.json:
        return bottle.HTTPResponse(status=422, body=json.dumps({"error": "text is required"}), headers={'Content-Type': 'application/json'})
    
    model["last_used"] = time.time()
    language  = None
    if 'language' in bottle.request.json:
        language = bottle.request.json['language']

    speed = 0.95

    if 'speed' in bottle.request.json:
        speed = bottle.request.json['speed']

    noise_scale = .667
    if 'noise_scale' in bottle.request.json:
        noise_scale = bottle.request.json['noise_scale']

    noise_scale_w = 0.8
    if 'noise_scale_w' in bottle.request.json:
        noise_scale_w = bottle.request.json['noise_scale_w']
    


    audioResult = model["tts_fn"](bottle.request.json['text'], speaker_id, language, speed, noise_scale, noise_scale_w)
    if audioResult[0] != "Success":
        return bottle.HTTPResponse(status=500, body=json.dumps({"error": "convert fail"}), headers={'Content-Type': 'application/json'})
    
    # 转换成功
    f = io.BytesIO()
    wavfile.write(f, audioResult[1][0], audioResult[1][1])
    bottle.response.content_type = 'audio/wav'

    return f.getvalue()
    
def stop_scheduler():
    schedule.clear()

def run_scheduler():
    while shutdown_event is None or not shutdown_event.is_set():
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    atexit.register(stop_scheduler)
    # 定时清理内存
    schedule.every(60).seconds.do(vits_tts.cache_gc)
    worker_thread = threading.Thread(target=run_scheduler)
    worker_thread.start()


    # 启动服务
    try:
        app.run(host='0.0.0.0', port=3232)
    finally:
        print('Shutting down...')
        shutdown_event.set()
        worker_thread.join()