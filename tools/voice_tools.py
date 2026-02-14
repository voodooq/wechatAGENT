
import speech_recognition as sr
import pyttsx3
import os

def listen_and_recognize():
    """
    监听麦克风输入，并将语音转换为文本。
    """
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("请说话...")
        audio = r.listen(source)
    try:
        text = r.recognize_google(audio, language='zh-CN')
        print(f"你说了: {text}")
        return {"status": "success", "text": text}
    except sr.UnknownValueError:
        return {"status": "error", "message": "无法识别语音"}
    except sr.RequestError as e:
        return {"status": "error", "message": f"语音服务请求失败: {e}"}

def speak_text(text):
    """
    将文本转换为语音并播放。
    """
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    return {"status": "success", "message": "语音播放完成"}

