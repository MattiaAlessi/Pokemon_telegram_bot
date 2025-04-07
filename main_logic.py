from telegram.ext import Application, CommandHandler, MessageHandler, filters
import logging
import requests
from urllib.parse import quote
from PIL import Image
import io

def fetch_pokemon_cards(query):
    """Esegue la query sull'API con encoding corretto"""
    encoded_query = quote(query)
    # Removed ordering to get all cards
    url = f"https://api.pokemontcg.io/v2/cards?q={encoded_query}&pageSize=250"
    
    headers = {
        "X-Api-Key": "8c905568-44b1-43f0-bb2e-8965ffded91f"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("data", [])
    except requests.exceptions.RequestException as e:
        print(f"Errore API: {e}")
        return []

async def search_command(update, context):
    # Store user data
    context.user_data['search_state'] = 'waiting_name'
    await update.message.reply_text("Se non sai alcune informazioni usa - ")
    await update.message.reply_text("Inserisci il nome della carta:")

async def handle_search_response(update, context):
    if 'search_state' not in context.user_data:
        return

    state = context.user_data['search_state']
    response = update.message.text

    if state == 'waiting_name':
        context.user_data['name'] = response
        context.user_data['search_state'] = 'waiting_set'
        await update.message.reply_text("Inserisci il set (inserisci - per ignorare):")
    
    elif state == 'waiting_set':
        context.user_data['set'] = response
        context.user_data['search_state'] = 'waiting_rarity'
        await update.message.reply_text("Inserisci la rarità (inserisci - per ignorare):")
    
    elif state == 'waiting_rarity':
        context.user_data['rarity'] = response
        context.user_data['search_state'] = 'waiting_artist'
        await update.message.reply_text("Inserisci l'artista (inserisci - per ignorare):")
    
    elif state == 'waiting_artist':
        context.user_data['artist'] = response
        context.user_data['search_state'] = 'waiting_number'
        await update.message.reply_text("Inserisci il numero della carta (inserisci - per ignorare):")
    
    elif state == 'waiting_number':
        query_parts = []
        
        if context.user_data['name']:
            query_parts.append(f'name:"{context.user_data["name"]}"')
        
        if context.user_data['set'] and context.user_data['set'] != '-':
            query_parts.append(f'set.name:"{context.user_data["set"]}"')
        
        if context.user_data['rarity'] and context.user_data['rarity'] != '-':
            query_parts.append(f'rarity:"{context.user_data["rarity"]}"')
        
        if context.user_data['artist'] and context.user_data['artist'] != '-':
            query_parts.append(f'artist:"{context.user_data["artist"]}"')
        
        if response and response != '-':
            query_parts.append(f'number:"{response}"')

        # Clear the search state
        context.user_data.clear()
        
        # Execute search
        query = " ".join(query_parts)
        cards = fetch_pokemon_cards(query)
        
        if not cards:
            await update.message.reply_text("Nessuna carta trovata.")
            return
        
        for card in cards[:10]:
            message = f"📋 {card['name']} ({card['set']['name']})\n"
            message += f"🎴 Rarità: {card.get('rarity', 'N/A')}\n"
            message += f"🔢 Numero: {card.get('number', 'N/A')}\n"
            message += f"👨‍🎨 Artista: {card.get('artist', 'N/A')}\n"
            
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

TOKEN = '7769264407:AAEM8lklmGg8lhz2fUUxkYhfoIMMN34obrU'

async def start(update, context):
    await update.message.reply_text('Ciao! Sono il tuo bot Pokemon per restare sempre aggiornato.\nUsa /help per ottenere informazioni sui comandi.')

async def about_command(update, context):
    about_text = (
        "🎮 *Pokemon TCG Card Finder*\n\n"
        "Ciao! Sono un bot specializzato nella ricerca di carte Pokemon.\n"
        "Posso aiutarti a trovare qualsiasi carta, mostrandoti immagini, "
        "prezzi e dettagli specifici.\n\n"
        "*Creato da:* \n"
        "*API:* Pokemon TCG API\n"
        "*Versione:* 1.0.0"
    )
    
    await update.message.reply_text(about_text, parse_mode='Markdown')

import random

async def game_command(update, context):
    # Get a random Pokemon card
    cards = fetch_pokemon_cards("supertype:Pokémon subtypes:Basic")
    if not cards:
        await update.message.reply_text("Errore nel caricamento del gioco.")
        return
    
    card = random.choice(cards)
    context.user_data['game_card'] = card
    
    # Download and crop the image
    try:
        response = requests.get(card['images']['large'])
        image = Image.open(io.BytesIO(response.content))
        
        # Get dimensions
        width, height = image.size
        # Crop just the top and bottom borders, keeping the full artwork
        crop_top = height // 8
        crop_bottom = height // 6
        cropped_image = image.crop((0, crop_top, width, height - crop_bottom))
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        cropped_image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # Send cropped image
        await update.message.reply_text("❓ Indovina il Pokemon! Osserva l'immagine e scrivi il nome.")
        await update.message.reply_photo(
            photo=img_byte_arr,
            caption="❓❓❓"
        )
    except Exception as e:
        print(f"Error processing image: {e}")
        await update.message.reply_text("Errore nel caricamento dell'immagine. Riprova.")
        return

async def handle_game_guess(update, context):
    if 'game_card' not in context.user_data:
        return False
    
    guess = update.message.text.lower()
    card = context.user_data['game_card']
    correct_name = card['name'].lower()
    
    if guess == correct_name:
        await update.message.reply_text(f"🎉 Corretto! È {card['name']}!")
        await update.message.reply_photo(
            photo=card['images']['large'],
            caption=f"✨ {card['name']} dal set {card['set']['name']}"
        )
        del context.user_data['game_card']
        return True
    else:
        await update.message.reply_text("❌ Sbagliato! Prova ancora o usa /surrender per arrenderti.")
        return True

async def surrender_command(update, context):
    if 'game_card' not in context.user_data:
        await update.message.reply_text("Non c'è nessuna partita in corso!")
        return
    
    card = context.user_data['game_card']
    await update.message.reply_text(f"Il Pokemon era {card['name']}!")
    await update.message.reply_photo(
        photo=card['images']['large'],
        caption=f"✨ {card['name']} dal set {card['set']['name']}"
    )
    del context.user_data['game_card']

# Update help command
async def help_command(update, context):
    help_text = (
        '🎮 *Comandi Disponibili:*\n\n'
        '🔍 */card* nome\n'
        '   • Cerca una carta per nome\n'
        '   • Esempio: /card Charizard\n\n'
        '🔎 */search*\n'
        '   • Avvia ricerca avanzata interattiva\n'
        '   • Cerca per nome, set, rarità, artista e numero\n'
        '   • Usa - per saltare i campi non necessari\n\n'
        '🎲 */game*\n'
        '   • Inizia un gioco di indovina il Pokemon\n'
        '   • /surrender per arrenderti\n\n'
        'ℹ️ */about*\n'
        '   • Mostra informazioni sul bot\n\n'
        '💡 *Suggerimento:* Per risultati migliori, usa nomi precisi'
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Update main function
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("card", card_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("game", game_command))
    application.add_handler(CommandHandler("surrender", surrender_command))
    
    # Update message handler to check for game guesses
    async def message_handler(update, context):
        if not await handle_game_guess(update, context):
            if 'search_state' in context.user_data:
                await handle_search_response(update, context)
            else:
                await echo(update, context)

    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        message_handler
    ))

    print("Bot started!")
    application.run_polling()

if __name__ == '__main__':
    main()