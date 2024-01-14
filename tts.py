# -*- coding: utf-8 -*-
"""
Author: Hoothin
调用微软官网的API，生成文本合成语音
"""
import os
import sys
import re
import requests
import time
from xml.etree import ElementTree
from pydub import AudioSegment

# 微软TTS的API key
subscription_key = ""
server_local = "japaneast"
input_path = "data/words.txt"
result_path = "merged_audio"

"""
晓晓 zh-CN-XiaoxiaoNeural 一般 青年 女
晓辰 zh-CN-XiaochenNeural 内敛 青年 女
晓涵 zh-CN-XiaohanNeural 妃子 青年 女
晓墨 zh-CN-XiaomoNeural 清亮 青年 女 🔥
晓梦 zh-CN-XiaomengNeural 土气 青年 女
晓秋 zh-CN-XiaoqiuNeural 沉稳 中年 女
晓睿 zh-CN-XiaoruiNeural 沉稳 老年 女
晓双 zh-CN-XiaoshuangNeural 天真 儿童 女
晓悠 zh-CN-XiaoyouNeural 班干部 儿童 女
晓伊 zh-CN-XiaoyiNeural 大孩子 儿童 女
晓萱 zh-CN-XiaoxuanNeural 厌世 青年 女
晓颜 zh-CN-XiaoyanNeural 邻家 青年 女
晓臻 zh-CN-XiaozhenNeural 台湾 青年 女
云夏 zh-CN-YunxiaNeural 儿童 男
云扬 zh-CN-YunyangNeural 一般 青年 男
云枫 zh-CN-YunfengNeural 大侠 青年 男
云皓 zh-CN-YunhaoNeural 播音员 青年 男
云希 zh-CN-YunxiNeural 帅哥 青年 男 🔥
云野 zh-CN-YunyeNeural 捏鼻子 中年 男
云健 zh-CN-YunjianNeural 沉稳 中年 男
云泽 zh-CN-YunzeNeural 温柔 中年 男
"""
timbre = "zh-CN-XiaomoNeural"
"""
https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-synthesis-markup-voice

<voice name="zh-CN-XiaomoNeural">
    <mstts:express-as role="YoungAdultFemale" style="calm">
        “您来的挺快的，怎么过来的？”
    </mstts:express-as>
    <mstts:express-as role="OlderAdultMale" style="calm">
        “刚打车过来的，路上还挺顺畅。”
    </mstts:express-as>
    <mstts:express-as style="sad" styledegree="2">
        快走吧，路上一定要注意安全，早去早回。
    </mstts:express-as>
    <prosody rate="+30.00%" volume="+20.00%">
        Enjoy using text to speech.
    </prosody>
</voice>
"""


class TextToSpeech(object):
    def __init__(self, subscription_key, timbre, server_local):
        self.subscription_key = subscription_key
        self.tts = ""
        self.timestr = time.strftime("%Y%m%d-%H%M")
        self.access_token = None
        self.timbre = timbre
        self.server_local = server_local

    def get_token(self):
        fetch_token_url = "https://" + self.server_local + ".api.cognitive.microsoft.com/sts/v1.0/issuetoken"
        headers = {
            'Ocp-Apim-Subscription-Key': self.subscription_key
        }
        response = requests.post(fetch_token_url, headers=headers)
        self.access_token = str(response.text)

    def save_audio(self, data, child_path):
        if os.path.exists(child_path + '.wav'):
            return True
        base_url = 'https://' + self.server_local + '.tts.speech.microsoft.com/'
        path = 'cognitiveservices/v1'
        constructed_url = base_url + path
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
            'Content-Type': 'application/ssml+xml',
            'X-Microsoft-OutputFormat': 'riff-24khz-16bit-mono-pcm',
            'User-Agent': 'TTSForPython'
        }
        body = ""
        if data.startswith("<voice"):
            ElementTree.register_namespace("", "http://www.w3.org/2001/10/synthesis")
            ElementTree.register_namespace("mstts", "http://www.w3.org/2001/mstts")
            ElementTree.register_namespace("emo", "http://www.w3.org/2009/10/emotionml")
            body = ElementTree.tostring(ElementTree.fromstring('<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-us">' + data + '</speak>'))
        else:
            xml_body = ElementTree.Element('speak', version='1.0')
            xml_body.set('{http://www.w3.org/XML/1998/namespace}lang', 'en-us')
            voice = ElementTree.SubElement(xml_body, 'voice')
            voice.set('{http://www.w3.org/XML/1998/namespace}lang', 'en-US')
            voice.set('name', self.timbre)
            voice.set('rate', '1')
            voice.text = data
            if data.endswith("!") or data.endswith("！"):
                voice.set('style', 'cheerful');
            body = ElementTree.tostring(xml_body)
        try:
            response = requests.post(constructed_url, headers=headers, data=body)
            if response.status_code == 200:
                with open(child_path + '.wav', 'wb') as audio:
                    audio.write(response.content)
                response.close()
            else:
                if response.status_code == 401:
                    print("\nStatus code: 401")
                else:
                    print("\nStatus code: " + str(response.status_code) + " Reason: " + str(response.reason) + "\nSomething went wrong. Check your subscription key.\n")
                response.close()
                return False
        except Exception as e:
            print("\n", e)
            return False
        return True

    def merge_audio_files(self, audio_files, output_path):
        combined_audio = AudioSegment.empty()
        for file in audio_files:
            audio = AudioSegment.from_wav(file)
            combined_audio += audio
        combined_audio.export(output_path, format="wav")

    def generate_srt_file(self, sentences, audio_files, output_path):
        with open(output_path, 'w', encoding='utf-8') as file:
            start_time = 0
            srt_index = 0
            for i, sentence in enumerate(sentences, start=1):
                audio_file = audio_files[i-1]
                audio = AudioSegment.from_wav(audio_file)
                audioLen = len(audio)
                totalEndTime = start_time + audioLen

                sentence = re.sub(r'([，：]+$|^[，：]+)', '', sentence)
                sentence = re.sub(r'，+', '，', sentence)
                sentence = re.sub(r'：+', '：', sentence)
                sentence = re.sub(r'<.*?>|</.*?>', '', sentence)
                sentence = re.sub(r' +', ' ', sentence)
                totalLen = len(re.sub(r'([，：])', '', sentence))
                parts = [part.strip() for part in re.split(r'[，：。！？,:\.!\?][”’\'"」』]?', sentence)]
                for index, part in enumerate(parts):
                    part_time = int(audioLen * len(part) / totalLen)
                    end_time = start_time + part_time
                    if index == len(parts) - 1:
                        end_time = totalEndTime
                    if part.strip() != "":
                        srt_index = srt_index + 1
                        srt_content = f"{srt_index}\n{self.format_time(start_time)} --> {self.format_time(end_time)}\n{part}\n\n"
                        file.write(srt_content)
                    start_time = end_time

    def format_time(self, milliseconds):
        if milliseconds == 0:
            milliseconds = 1
        hours = int(milliseconds // 3600000)
        minutes = int(milliseconds % 3600000 // 60000)
        seconds = int(milliseconds % 60000 // 1000)
        milliseconds = int(milliseconds % 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def is_chinese(string):
    if string == '':
        return False
    for ch in string:
        if u'\u0030' <= ch <= u'\u0039':
            return True
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False

def split_text(text):
    result = []
    voice_pattern = re.compile(r"<voice.*?</voice>", re.DOTALL)
    voice_matches = voice_pattern.findall(text)
    text_without_voice = voice_pattern.sub(r"__VOICE_BLOCK__", text)
    split_pattern = re.compile(r"(__VOICE_BLOCK__|.*?([。？！…\.\?\!]+[”’'\"」』]?|\n))", re.DOTALL)
    split_matches = split_pattern.findall(text_without_voice)
    for match in split_matches:
        if match[0].strip() != "":
            if match[0].strip() == "__VOICE_BLOCK__" and voice_matches:
                result.append(voice_matches.pop(0))
            else:
                result.append(match[0].strip())
    return result

def load_source_data_text(file_path, failed):
    app = TextToSpeech(subscription_key, timbre, server_local)
    try:
        app.get_token()
    except Exception as e:
        if failed < 30:
            print("检测到异常，自动重启中……")
            time.sleep(3)
            load_source_data_text(file_path, failed + 1)
        else:
            print("执行异常，重启继续执行")
        return
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    sentences = [sentence.strip().replace('\n', '') for sentence in split_text(text) if is_chinese(sentence.strip())]
    audio_files = []
    for index, sentence in enumerate(sentences):
        new_path = file_path.split(".txt")[0].replace("data", "data_audio")
        if not os.path.exists(new_path):
            os.makedirs(new_path)
        path_child = os.path.join(new_path, str(index))
        result = app.save_audio(sentence, path_child)
        if result == False:
            if failed < 30:
                print("检测到异常，自动重启中……")
                time.sleep(3)
                load_source_data_text(file_path, failed + 1)
            else:
                print("执行异常，重启继续执行")
            return
        audio_files.append(path_child + '.wav')
        print(str(index + 1), "/", str(len(sentences)), end='\r')

    print("\n开始合并语音。。。")
    merged_output_path = file_path.split("words.txt")[0].replace("data", result_path)
    if merged_output_path != "":
        if not os.path.exists(merged_output_path):
            os.makedirs(merged_output_path)
    app.merge_audio_files(audio_files, merged_output_path + 'sound.wav')
    srt_output_path = merged_output_path + 'sound.srt'
    app.generate_srt_file(sentences, audio_files, srt_output_path)
    for i in range(len(audio_files)):
        os.remove(audio_files[i])
    print("语音生成完毕")
    return merged_output_path


if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if file_path.endswith(".txt"):
            load_source_data_text(file_path, 0)
        else:
            print("Invalid file format. Please provide a TXT file.")
    else:
        print("读取文本中……")
        load_source_data_text(input_path, 0)