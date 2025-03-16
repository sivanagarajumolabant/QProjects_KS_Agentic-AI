from langdetect import DetectorFactory

DetectorFactory.seed = 0

from langdetect import detect
from deep_translator import GoogleTranslator


# simple function to detect and translate text
def detect_and_translate(text, target_lang):
    result_lang = detect(text)
    print(result_lang)
    if result_lang == target_lang:
        return text

    else:
        translate_text = GoogleTranslator(source='auto', target='te').translate(text)
        return translate_text

    # Example


sentence = "I hope that, when I’ve built up my savings, I’ll be able to travel to Mexico"

print(detect_and_translate(sentence, target_lang='en'))
#
#
# from langdetect import DetectorFactory
# DetectorFactory.seed = 0
#
# # show probabilities for the top languages
# from langdetect import detect_langs
#
# sentence = "Tanzania ni nchi inayoongoza kwa utalii barani afrika"
#
# print(detect_langs(sentence))