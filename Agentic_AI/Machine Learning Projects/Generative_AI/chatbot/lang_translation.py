from deep_translator import GoogleTranslator

sentence = "మీరు ఎలా ఉన్నారు"
sentence1 = "కనక మహాలక్ష్మి"

# sentence = "how are you"
# sentence1 = "my name is sivanagaraju"
tran = GoogleTranslator(source='auto', target='en').translate(sentence)
tran1 = GoogleTranslator(source='auto', target='en').translate(sentence1)
print(tran)
print(tran1)
