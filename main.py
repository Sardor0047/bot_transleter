from config import Token
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CallbackContext, CommandHandler, MessageHandler, Filters
from tinydb import TinyDB, Query
from googletrans import Translator
from nltk.corpus import wordnet
import nltk
nltk.download('wordnet')

db = TinyDB('database.json')
User = Query()

def start(update,context):
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name
    if not db.search(User.user_id == user_id):
        db.insert({'user_id': user_id , 'folders':{}})
    
    welcome_message = (
        f"👋 Hello, {user_name}! Welcome to the Dualcard Bot.\n\n"
        "This bot helps you learn English by creating flashcards with words, definitions, translations, and images.\n\n"
        "Choose an option from the menu below:\n\n"
    )
    keyboard =[
        ["📝 Create Folder", "📁 Show Folders"],
        ["🗑️ Delete Folder", "🧠 Test Knowledge"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard)

    update.message.reply_text(welcome_message,reply_markup=reply_markup)

def help_command(update: Update, context: CallbackContext) -> None:
    help_message = (
        "📚 *How to Use Dualcard Bot*\n\n"
        "Dualcard Bot helps you learn English by creating flashcards with words, definitions, translations, and images.\n\n"
        "*Step-by-step Guide:*\n\n"
        "1️⃣ *Add a Word*: Use the '📝 Create Flashcard' button or type /create to add a new word.\n"
        "   - The bot will automatically fetch the definition from Wikipedia.\n"
        "   - It will also translate the word into your language using Google Translate.\n"
        "   - An image related to the word will be added automatically.\n"
        "   - You can organize words into folders (categories).\n\n"
        "2️⃣ *Create a Folder*: Use the '📁 Create Folder' button or type /create_folder to create a new folder.\n\n"
        "3️⃣ *Delete a Folder*: Use the '🗑️ Delete Folder' button or type /delete_folder to remove a folder and its contents.\n\n"
        "4️⃣ *Test Your Knowledge*: Use the '🧠 Test Knowledge' button or type /test to practice your vocabulary.\n"
        "   - The bot will randomly select words from your folders and ask you to guess their meanings.\n\n"
        "5️⃣ *Get Help*: Use the 'ℹ️ Help' button or type /help to see this guide again.\n\n"
        "For any questions or issues, feel free to contact the developer."
    )

    update.message.reply_text(help_message, parse_mode="Markdown")  

def create_folder(update: Update, context):
    user_id = update.message.from_user.id
    if not db.search(User.user_id == user_id):
        db.insert({'user_id': user_id , 'folders':{}})
    update.message.reply_text("Enter the name of the folder you want to create:")
    context.user_data['state'] = 'WAITING_FOLDER_NAME'

def get_definition(word):
    synsets = wordnet.synsets(word)
    if synsets:
        return synsets[0].definition()
    else:
        return "Definition not found"
word = get_definition('avoid')

def get_translation_and_definition(word):
    translator = Translator()   
    # NLTK orqali definition olish
    definition = get_definition(word)
    
    # Google Translate orqali tarjimani olish
    try:
        translation = translator.translate(word, src='en', dest='uz').text
    except Exception as e:
        translation = "Translation not found"
    
    return definition, translation

def hendle_message(update: Update, context):
    user_id = update.message.from_user.id
    user_text = update.message.text

    if context.user_data.get('state') == 'WAITING_FOLDER_NAME':
        folder_name = user_text
        user_data = db.search(User.user_id == user_id)[0]
        folder = user_data['folders']
        if folder_name  in folder:
            update.message.reply_text(f"Folder {folder_name} already exists. Please enter a different name.")
        else:
            folder[folder_name] = []
            db.update({'folders':folder}, User.user_id == user_id)
            update.message.reply_text(f"Folder {folder_name} has been created successfully.")
            context.user_data.clear()
    if '+' in user_text:
        user_data = db.search(User.user_id == user_id)[0]
        folder_name, word = user_text.split('+',1)
        user_data = db.search(User.user_id == user_id)[0]
        folder = user_data['folders']
        if folder_name not in folder:
            update.message.reply_text(f"Folder {folder_name} does not exist. Please create the folder first.")
        word_exists = False
        for entry in folder[folder_name]:
            if entry['word'] == word:
                word_exists = True
                break
        if not word_exists:
            definition, translation = get_translation_and_definition(word)

            if definition and translation:
                word_entry = {
                    'word': word,
                    'definition': definition,
                    'translation': translation
                }
                folder[folder_name].append(word_entry)
                update.message.reply_text(
                f"✅ The word '{word}' has been added to the folder '{folder_name}'.\n\n"
                f"📖 *Definition:* {definition}\n"
                f"🔤 *Translation:* {translation}",
                parse_mode="Markdown",
                    )
            else :
                word_entry = {
                    'word': word,
                    'definition': 'Definition not found',
                    'translation': 'Translation not found'
                }
                folder[folder_name].append(word_entry)
                db.update({'folders':folder}, User.user_id == user_id)
                update.message.reply_text(
                    f"The word '{word}' has been added to the folder '{folder_name}'.\n\n"
                    "Definition and translation not found."
                )
        else:
            update.message.reply_text(f"The word '{word}' already exists in the folder '{folder_name}'.")





        


def main():
    updater = Updater(Token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start',start))
    dispatcher.add_handler(CommandHandler('help',help_command))
    dispatcher.add_handler(MessageHandler(Filters.text("📝 Create Folder"),callback=create_folder))
    dispatcher.add_handler(MessageHandler(Filters.text, hendle_message))
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()

