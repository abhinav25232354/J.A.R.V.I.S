import requests
from Speech_Drive.Short_speech import *

def speak(audio):
    '''This function convert text into speech'''
    asyncio.run(speech(audio))
    playsound("output.mp3")

def fetch_news(query):
    try:
        API_KEY = 'AIzaSyAIBilOvhV-sz93OXf8yjN2V2iJpaaUYMA'
        CX = '0107174b522264ad7'
    
        url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={CX}&q={query}"
    
        try:
            response = requests.get(url)
            response.raise_for_status()  # Check if request was successful
            data = response.json()
        except requests.exceptions.RequestException:
            return "❌ Unable to fetch news. Please check your internet connection."

        items = data.get('items', [])[:5]  # Get top 5 search results

        if not items:
            return "ℹ️ No news found for this query."

        # Extract snippets safely
        snippets = [item.get('snippet', '') for item in items if item.get('snippet')]
    
        if not snippets:
            return "ℹ️ No relevant news summaries found."

        summary = " ".join(snippets)  # Combine all snippets into a paragraph

        print(summary)
        speak(summary)
        # return f"📰 **Today's News Summary:**\n\n{summary}"
    except Exception as e:
        print(e)

# Example usage
if __name__ == "__main__":
    fetch_news("Apple")

# def fetch_news(query):
#     API_KEY = 'AIzaSyAIBilOvhV-sz93OXf8yjN2V2iJpaaUYMA'
#     CX = '0107174b522264ad7'
#     # QUERY = 'Indian Government'

#     # Step 1: Make the API call
#     url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={CX}&q={query}"
#     response = requests.get(url)
#     data = response.json()

#     # Step 2: Extract top 5 titles + snippets
#     items = data.get('items', [])[:5]
#     text_chunks = [f"{item['title']}. {item['snippet']}" for item in items]

#     # Step 3: Combine all into one block of text
#     combined_text = " ".join(text_chunks)

#     # Step 4: Generate a simple paragraph-like summary
#     summary = f"Here are some of the top headlines today: {combined_text}"

#     print(summary)