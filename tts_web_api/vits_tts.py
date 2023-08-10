import os
import sys
import time


# 加载上层目录的 sovits 模块
current_dir = os.path.dirname(os.path.abspath(__file__))
sovits_dir = os.path.join(current_dir, '..')
sys.path.append(sovits_dir)

import os
import numpy as np
import torch
from torch import no_grad, LongTensor
import commons
from mel_processing import spectrogram_torch
import utils
from models import SynthesizerTrn
import json

from text import text_to_sequence, _clean_text
device = "cuda:0" if torch.cuda.is_available() else "cpu"
language_marks = {
    "Japanese": "",
    "日本語": "[JA]",
    "简体中文": "[ZH]",
    "English": "[EN]",
    "Mix": "",
}
lang = ['日本語', '简体中文', 'English', 'Mix']

model_cache = {}

def get_text(text, hps, is_symbol):
    text_norm = text_to_sequence(text, hps.symbols, [] if is_symbol else hps.data.text_cleaners)
    if hps.data.add_blank:
        text_norm = commons.intersperse(text_norm, 0)
    text_norm = LongTensor(text_norm)
    return text_norm

def create_tts_fn(model, hps):
    def tts_fn(text, speaker_id, language, speed, noise_scale, noise_scale_w):
        speaker_id = int(speaker_id)
        if language is not None:
            text = language_marks[language] + text + language_marks[language]
        else:
            # 默认都是中文
            text = language_marks["简体中文"] + text + language_marks["简体中文"]

        stn_tst = get_text(text, hps, False)
        with no_grad():
            x_tst = stn_tst.unsqueeze(0).to(device)
            x_tst_lengths = LongTensor([stn_tst.size(0)]).to(device)
            sid = LongTensor([speaker_id]).to(device)
            audio = model.infer(x_tst, x_tst_lengths, sid=sid, noise_scale=noise_scale, noise_scale_w=noise_scale_w,
                                length_scale=1.0 / speed)[0][0, 0].data.cpu().float().numpy()
        del stn_tst, x_tst, x_tst_lengths, sid
        return "Success", (hps.data.sampling_rate, audio)
    return tts_fn

# 加载模型
def load_model(model_name):
    if model_name in model_cache:
        return model_cache[model_name]

    config_path = os.path.join('models', model_name, 'moegoe_config.json')
    if not os.path.exists(config_path):
        raise ValueError("Model not found: {}".format(model_name))
    
    checkpoint_path = os.path.join('models', model_name, 'G_latest.pth')
    if not os.path.exists(checkpoint_path):
        raise ValueError("Model pth file not found: {}".format(model_name))
    
    model_configs = {}
    with open(config_path, 'r') as f:
        model_configs = json.load(f)
    
    symbols = model_configs['symbols']
    filter_length = model_configs["data"]['filter_length']
    segment_size = model_configs["train"]['segment_size']
    n_speakers = model_configs["data"]['n_speakers']
    hop_length = model_configs["data"]['hop_length']

    hps = utils.get_hparams_from_file(config_path)

    net_g = SynthesizerTrn(
        len(symbols),
        filter_length // 2 + 1,
        segment_size // hop_length,
        n_speakers=n_speakers,
        **hps.model).to(device)
    _ = net_g.eval()

    _ = utils.load_checkpoint(checkpoint_path, net_g, None)
    speakers_ids = {}
    i = 0
    for speaker in model_configs["speakers"]:
        speakers_ids[i] = speaker
        i += 1

    model_cache[model_name] = {
        "model": net_g,
        "hps": hps,
        "speakers_ids": speakers_ids,
        "speakers": model_configs["speakers"],
        "tts_fn": create_tts_fn(net_g, hps),
        "last_used": time.time()
    }

    return model_cache[model_name]
    
def cache_gc():
    for model_name in model_cache:
        if time.time() - model_cache[model_name]["last_used"] > 600: # 10分钟没用就清理
            del model_cache[model_name]["model"]
            del model_cache[model_name]
            print("Model {} removed from cache".format(model_name))
            # 如果缓存里一个模型都没有了，就退出,就直接清空pytorch的缓存
            if len(model_cache) == 0:
                torch.cuda.empty_cache()
                break

