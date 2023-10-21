# -*- coding: utf-8 -*-
"""
Author: Hoothin
呼叫openai的API，對文字進行偽原創改寫
"""
import openai
import os
import re
import sys

openai.api_key = ''

source_file = "book.txt"
target_file = "data/words.txt"

script_dir = os.path.dirname(os.path.abspath(__file__))

def getBookFile(source_path):
    if not os.path.exists(source_path):
        return ""
    with open(source_path, 'r', encoding='utf-8') as file:
        return file.read()

def getCompletion(prompt, model="gpt-3.5-turbo"):
    messages = [
        {
            "role": "system", 
            "content": "Assistant is a highly acclaimed chinese online writer."
        }, 
        {
            "role": "user", 
            "content": f"""Rephrase the following novel with Chinese, to avoid repetition, while keeping its meaning: {prompt}"""
        }
    ]
    completion = openai.ChatCompletion.create(
        model=model,
        stream=True,
        messages=messages,
        temperature=.1,  # 值越低則輸出文字隨機性越低
    )
    content = ''
    for part in completion:
        delta = part.choices[0].delta
        delta_content = delta.get('content')
        if delta_content:
            content += delta_content
    return content

def splitBook(bookText):
    bookText = re.sub(r'[\n\r]{2,}', r'\n', bookText)
    bookTextLines = bookText.split('\n')
    segments = []
    while len(bookTextLines) > 0:
        segment = ""
        for x in range(len(bookTextLines)):
            curLine = bookTextLines[x];
            if len(segment) + len(curLine) > 1500:
                segment = segment + "\n"
                curLine = re.sub(r'([。？！\?\!]+)([^”’」』])', r'\1\n\2', curLine)
                curLineParts = curLine.split('\n')
                for l in range(len(curLineParts)):
                    curPart = curLineParts[l]
                    segment = segment + curPart
                    if len(segment) > 1000:
                        bookTextLines = bookTextLines[x + 1:]
                        bookTextLines[0] = "".join(curLineParts[l + 1:]) + "\n" + bookTextLines[0]
                        leftWords = "\n".join(bookTextLines)
                        if len(leftWords) < 500:
                            segment = segment + "\n" + leftWords
                            bookTextLines = []
                        segments.append(segment)
                        break
                break
            else:
                segment = segment + "\n" + curLine
                if len(segment) > 1000:
                    bookTextLines = bookTextLines[(x + 1):]
                    leftWords = "\n".join(bookTextLines)
                    if len(leftWords) < 500:
                        segment = segment + "\n" + leftWords
                        bookTextLines = []
                    segments.append(segment)
                    break
    return segments

def rewrite(path):
    bookText = getBookFile(path)
    if bookText == "":
        return
    segments = splitBook(bookText)
    translated_segments = []

    target_dir = os.path.join(script_dir, 'temp')
    os.makedirs(target_dir, exist_ok=True)
    print(f"分割完成，共 {len(segments)} 段，開始改寫")
    for i, segment in enumerate(segments):
        prompt = f"```{segment}```"
        tryTimes = 0
        failed = False
        child_path = target_dir + "/" + str(i) + '.txt';
        while tryTimes < 3:
            try:
                response = ""
                if os.path.exists(child_path):
                    with open(child_path, 'r', encoding='utf-8') as file:
                        response = file.read()
                else:
                    response = getCompletion(prompt)
                    with open(child_path, 'w', encoding='utf-8') as file:
                        file.write(response)
                translated_segments.append(response)
                failed = False
                break
            except Exception as e:
                print("\n", e)
                tryTimes = tryTimes + 1
                print(f"網路錯誤，重試第 {tryTimes} 次")
                time.sleep(3)
                failed = True
        if failed:
            print(f"網路錯誤，退出重試")
            return

        print(f"{i+1} / {len(segments)}", end='\r')

    translated_content = "\n".join(translated_segments)
    for i in range(len(translated_segments)):
        child_path = target_dir + "/" + str(i) + '.txt';
        os.remove(child_path)
    target_dir = os.path.join(script_dir, os.path.dirname(target_file))
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(script_dir, target_file)
    with open(target_path, 'w', encoding='utf-8') as file:
        file.write(translated_content)

    print('改寫完成！')


if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if file_path.endswith(".txt"):
            rewrite(file_path)
        else:
            print("Invalid file format. Please provide a TXT file.")
    else:
        print("改寫文字中……")
        source_path = os.path.join(script_dir, source_file)
        rewrite(source_path)