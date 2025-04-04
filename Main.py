from telegram.ext import Application, CommandHandler, MessageHandler, filters
import logging
import requests
from urllib.parse import quote

def fetch_pokemon_cards(query):
    """Esegue la query sull'API con encoding corretto"""
    encoded_query = quote(query)
    # Removed ordering to get all cards
    url = f"https://api.pokemontcg.io/v2/cards?q={encoded_query}&pageSize=250"
    
    headers = {
        "X-Api-Key": "INSERISCI_LA_TUA_API_KEY_POKEMONTCG"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("data", [])
    except requests.exceptions.RequestException as e:
        print(f"Errore API: {e}")
        return []

async def card_command(update, context):
    if not context.args:
        await update.message.reply_text("Per favore, inserisci il nome della carta dopo il comando /card\nEsempio: /card Charizard")
        return
    
    card_name = ' '.join(context.args)
    cards = fetch_pokemon_cards(f'name:"{card_name}"')
    
    if not cards:
        await update.message.reply_text("Nessuna carta trovata.")
        return
    
    for card in cards:  # Limiting to 5 cards to avoid too long messages
        message = f"📋 {card['name']} ({card['set']['name']})\n"
        message += f"🎴 Rarità: {card.get('rarity', 'N/A')}\n"
        message += f"🔢 Numero: {card.get('number', 'N/A')}\n"
        
        if "tcgplayer" in card:
            prices = card["tcgplayer"].get("prices", {})
            if prices:
                message += "💰 Prezzi (TCGPlayer):\n"
                for cond, price in prices.items():
                    formatted_cond = ''.join(' ' + c if c.isupper() else c for c in cond).strip()
                    message += f"  - {formatted_cond}: ${price.get('market', 'N/A')}\n"

        await update.message.reply_photo(
            photo=card['images']['large'],
            caption=message
        )

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = 'INSERISCI_IL_TUO_TOKEN_BOT_TELEGRAM'

async def start(update, context):
    await update.message.reply_text('Ciao! Sono il tuo bot Pokemon per restare sempre aggiornato.\nUsa /help per ottenere informazioni sui comandi.')

async def help_command(update, context):
    await update.message.reply_text('Usa /card per cercare una carta')

async def echo(update, context):
    await update.message.reply_text(update.message.text)

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_handler(CommandHandler("card", card_command))

    print("Bot started!")
    application.run_polling()

if __name__ == '__main__':
    main()
