import pyaudio
import wave
import io
import json
import requests
from conf import Token

from time import sleep
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer

model_name = "christian-phu/bert-finetuned-japanese-sentiment"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=Token)
model = AutoModelForSequenceClassification.from_pretrained(model_name, use_auth_token=Token)

sentiment_analysis = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)


def analyze_sentiment(text):
    result = sentiment_analysis(text)
    return result[0]["label"]

def adjust_parameters_based_on_sentiment(speaker, sentiment):
    speed = 1.0  # Default speed
    pitch = 0.0  # Default pitch

    if sentiment == "POSITIVE":
        speed = 1.1
        pitch = 0.5
    elif sentiment == "NEGATIVE":
        speed = 0.9
        pitch = -0.5
    elif sentiment == "NEUTRAL":
        speed = 1.0
        pitch = 0.0
    print(sentiment)
    return speaker, speed, pitch

def text_to_voice_with_sentiment(text, speaker, cab_d):
    sentiment = analyze_sentiment(text)
    speaker, speed, pitch = adjust_parameters_based_on_sentiment(speaker, sentiment)
    res = post_audio_query(text, speaker, speed, pitch)
    wav = post_synthesis(res, speaker)
    print(f'开始播放')
    play_wav(wav, cab_d)

def post_audio_query(text: str, speaker: int, speed: float, pitch: float) -> dict:
    """
    发送文本到VOICEVOX，返回JSON格式的响应
    """

    params = {'text': text, 'speaker': speaker, 'speed': speed, 'pitch': pitch}
    res = requests.post('http://localhost:50021/audio_query', params=params)
    return res.json()

def post_synthesis(audio_query_response: dict, speaker: int) -> bytes:
    """
    发送语音查询响应到VOICEVOX，返回语音合成的二进制wav格式数据
    """
    params = {'speaker': speaker}
    headers = {'content-type': 'application/json'}
    audio_query_response_json = json.dumps(audio_query_response)
    res = requests.post(
        'http://localhost:50021/synthesis',
        data=audio_query_response_json,
        params=params,
        headers=headers
    )
    return res.content


def play_wav(wav_file: bytes, device_index: int):
    """
    播放二进制wav格式数据到指定设备
    """
    wr: wave.Wave_read = wave.open(io.BytesIO(wav_file))
    p = pyaudio.PyAudio()
    stream = p.open(
        format=p.get_format_from_width(wr.getsampwidth()),
        channels=wr.getnchannels(),
        rate=wr.getframerate(),
        output=True,
        output_device_index=device_index
    )
    chunk = 1024
    data = wr.readframes(chunk)
    while data:
        stream.write(data)
        data = wr.readframes(chunk)
    sleep(0.5)
    stream.close()
    p.terminate()