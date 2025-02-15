from googletrans import Translator
translator = Translator()
result = translator.translate("gave", src='en', dest='uz')
print(result.text) 