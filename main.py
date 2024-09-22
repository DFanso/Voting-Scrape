import requests
from bs4 import BeautifulSoup
import schedule
from discord_webhook import DiscordWebhook, DiscordEmbed

# URL of the website to scrape
url = 'https://results.elections.gov.lk/index.php'

# Discord webhook URL (replace this with your actual webhook URL)
WEBHOOK_URL = 'https://discord.com/api/webhooks/1287147542869708990/zjbSh53bN7u9FUCn1EA_tvOTdxgnxuafsb8Kd4GLhS8jCzvRP1X3t1DEKQn8e-yAsKa0'

# Store the previous results to track changes
previous_results = None

# Party colors for the progress bars (hex values for colors)
party_colors = {
    'NPP': 0xff0000,  # Red
    'SJB': 0x00ff00,  # Green
    'IND16': 0x0000ff,  # Blue
    'SLPP': 0xff00ff,  # Pink
    'Others': 0xcccccc  # Grey for "Other" parties
}

# Election board logo URL (use your actual URL here)
election_logo_url = 'https://results.elections.gov.lk/assets/images/logo.png'

# Function to scrape the website and get the voting percentages
def scrape_election_results():
    global previous_results  # To access the global previous_results

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Initialize list to store all party results
    all_parties = []

    # Locate the divs containing party results
    party_wrappers = soup.find_all('div', class_='wrapper d-flex align-items-center justify-content-between py-2 border-bottom')

    for party_wrapper in party_wrappers:
        # Extract party name
        party_name = party_wrapper.find('small', class_='text-center mt-1').text.strip()

        # Extract candidate name
        candidate_name = party_wrapper.find('p', class_='ms-1 mb-1 fw-bold').text.strip()

        # Extract vote count and percentage
        vote_percentage_wrapper = party_wrapper.find('div', class_='d-flex justify-content-between align-items-center mt-1')
        votes = vote_percentage_wrapper.find_all('small')[0].text.strip().replace(',', '')
        percentage = float(vote_percentage_wrapper.find_all('small')[1].text.strip().replace('%', ''))

        # Append the results to the all_parties list
        all_parties.append({
            'party_name': party_name,
            'candidate': candidate_name,
            'votes': int(votes),
            'percentage': percentage
        })

   # Sort parties by percentage in descending order
    all_parties_sorted = sorted(all_parties, key=lambda x: x['percentage'], reverse=True)

    # Separate the top 5 and the rest
    top_5 = all_parties_sorted[:5]
    others = all_parties_sorted[5:]

    # Calculate the total percentage for "Other" parties
    other_percentage = sum([party['percentage'] for party in others])

    # Prepare current results including "Others"
    current_results = top_5 + [{'party_name': 'Others', 'percentage': other_percentage}]

    # Check if results have changed
    if previous_results != current_results:
        # Send results to Discord webhook
        send_discord_webhook(top_5, other_percentage)
        # Update previous results
        previous_results = current_results

# Function to send results to Discord via webhook
def send_discord_webhook(top_4, other_percentage):
    webhook = DiscordWebhook(url=WEBHOOK_URL)

    embed = DiscordEmbed(title="🇱🇰 Sri Lanka Presidential Election Results 2024", description="Latest Real-Time Results", color=0x3498db)
    embed.set_footer(text="Real-Time Election Updates by DFanso")
    embed.set_timestamp()  # Automatically add timestamp

    # Add top 4 parties results as embed fields
    for party in top_4:
        progress_bar = '▓' * int(party['percentage'] // 10) + '░' * (10 - int(party['percentage'] // 10))  # Create a 10-character progress bar
        color_hex = party_colors.get(party['party_name'], 0xcccccc)  # Get the party color, default to grey

        embed.add_embed_field(
            name=f"**{party['party_name']}** - {party['candidate']}",
            value=(
                f"🗳 **Votes:** {party['votes']:,}\n"  # Formatting votes with commas
                f"📊 {progress_bar} **{party['percentage']}%**\n"
                f"───────────────────────────"
            ),
            inline=False
        )

    # Add the "Others" category as a single field
    others_progress_bar = '▓' * int(other_percentage // 10) + '░' * (10 - int(other_percentage // 10))  # Progress bar for Others
    embed.add_embed_field(
        name=f"**Other Parties**",
        value=f"{others_progress_bar} **{other_percentage:.2f}%**",
        inline=False
    )

    # Attach the election board logo
    embed.set_thumbnail(url=election_logo_url)

    # Send the embed message to the webhook
    webhook.add_embed(embed)
    webhook.execute()

# Schedule the scraping function to run every 5 minutes
schedule.every(20).seconds.do(scrape_election_results)

# Keep the script running
while True:
    schedule.run_pending()