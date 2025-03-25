import toga
from toga.style.pack import Pack, COLUMN, ROW
import requests
from bs4 import BeautifulSoup
import webbrowser
import time
import os  # Add this import for environment variables

class NoBullNews(toga.App):
    def startup(self):
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        
        self.categories = ['general', 'business', 'technology', 'science', 'health', 'sports', 'entertainment', 'world', 'politics', 'gaming']
        self.category_picker = toga.Selection(items=self.categories, on_select=self.refresh_news, style=Pack(padding_bottom=5))
        main_box.add(self.category_picker)
        
        self.locations = ['World', 'South Africa', 'Port Elizabeth']
        self.location_picker = toga.Selection(items=self.locations, on_select=self.refresh_news, style=Pack(padding_bottom=5))
        main_box.add(self.location_picker)
        
        self.filters = ['All News', 'No Tabloids', 'No Clickbait']
        self.filter_picker = toga.Selection(items=self.filters, on_select=self.refresh_news, style=Pack(padding_bottom=5))
        main_box.add(self.filter_picker)
        
        self.article_counts = ['5', '10', '15', '20']
        self.count_picker = toga.Selection(items=self.article_counts, value='10', on_select=self.refresh_news, style=Pack(padding_bottom=5))
        main_box.add(self.count_picker)
        
        self.scroll_container = toga.ScrollContainer(style=Pack(flex=1))
        self.news_box = toga.Box(style=Pack(direction=COLUMN))
        self.scroll_container.content = self.news_box
        main_box.add(self.scroll_container)
        
        refresh_button = toga.Button('Refresh News', on_press=self.refresh_news, style=Pack(padding=5))
        main_box.add(refresh_button)
        
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()
        self.refresh_news(None)

    def refresh_news(self, widget):
        # Show loading indicator
        self.news_box.clear()
        loading_label = toga.Label("Loading news...", style=Pack(padding=5))
        self.news_box.add(loading_label)
        self.news_box.refresh()  # Force UI update

        category = self.category_picker.value if widget else 'general'
        location = the.location_picker.value if widget else 'World'
        filter_mode = self.filter_picker.value if widget else 'All News'
        article_count = int(self.count_picker.value) if self.count_picker.value else 10
        
        # Load API key from environment variable
        api_key = os.getenv('NEWSAPI_KEY')
        if not api_key:
            self.news_box.clear()
            self.news_box.add(toga.Label("Error: NEWSAPI_KEY environment variable not set.", style=Pack(padding=5)))
            return
        
        if location == 'South Africa':
            if category in ['world', 'politics', 'gaming']:
                url = f'https://newsapi.org/v2/everything?q={category} south africa&language=en&apiKey={api_key}'
            else:
                url = f'https://newsapi.org/v2/top-headlines?category={category}&country=za&language=en&apiKey={api_key}'
        elif location == 'Port Elizabeth':
            url = f'https://newsapi.org/v2/everything?q={category} "port elizabeth" OR gqeberha&language=en&apiKey={api_key}'
        else:  # World
            if category in ['world', 'politics', 'gaming']:
                url = f'https://newsapi.org/v2/everything?q={category} -sports -entertainment&language=en&apiKey={api_key}'
            else:
                url = f'https://newsapi.org/v2/top-headlines?category={category}&language=en&apiKey={api_key}'
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            print(f"URL: {url}")
            print(f"API Response: {data}")
            
            if 'articles' not in data:
                error_message = data.get('message', 'No articles found')
                if 'rate limit' in error_message.lower():
                    error_message = "API rate limit exceeded. Please try again later."
                self.news_box.clear()
                self.news_box.add(toga.Label(f"Error: {error_message}", style=Pack(padding=5)))
                return
            articles = data['articles']
            
            filtered_articles = articles
            if filter_mode == 'No Tabloids':
                junk_sources = ['dailymail.co.uk', 'thesun.co.uk', 'nypost.com']
                filtered_articles = [a for a in articles if a['source']['id'] not in junk_sources and a['description']]
            elif filter_mode == 'No Clickbait':
                clickbait_words = ['shocking', 'you won’t believe', 'secret', 'celebrity']
                filtered_articles = [a for a in articles if not any(word in a['title'].lower() for word in clickbait_words) and a['description']]
            
            self.news_box.clear()
            if not filtered_articles:
                self.news_box.add(toga.Label("No articles found matching your criteria.", style=Pack(padding=5)))
                return
            
            for article in filtered_articles[:article_count]:
                article_row = toga.Box(style=Pack(direction=ROW, padding=5))
                
                # Article text (no image here)
                text = f"{article['title']} - {article['source']['name']}\n{article['description'] or 'No description'}"
                article_display = toga.MultilineTextInput(
                    value=text,
                    readonly=True,
                    style=Pack(flex=1, height=100, padding_right=5)
                )
                read_button = toga.Button(
                    'Read More',
                    on_press=lambda w, a=article: self.show_full_article(a),
                    style=Pack(width=100)
                )
                article_row.add(article_display)
                article_row.add(read_button)
                self.news_box.add(article_row)
        
        except requests.ConnectionError:
            self.news_box.clear()
            self.news_box.add(toga.Label("Network error: Please check your internet connection and try again.", style=Pack(padding=5)))
        except requests.Timeout:
            self.news_box.clear()
            self.news_box.add(toga.Label("Request timed out: The server took too long to respond. Please try again.", style=Pack(padding=5)))
        except requests.HTTPError as e:
            self.news_box.clear()
            self.news_box.add(toga.Label(f"HTTP error: {str(e)}. Please try again.", style=Pack(padding=5)))
        except Exception as e:
            self.news_box.clear()
            self.news_box.add(toga.Label(f"Unexpected error: {str(e)}. Please try again.", style=Pack(padding=5)))

    def show_full_article(self, article):
        article_window = toga.Window(title=article['title'], size=(600, 400))
        article_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        
        # Add image if available
        if article.get('urlToImage'):
            try:
                image_response = requests.get(article['urlToImage'], timeout=5)
                image_response.raise_for_status()
                image = toga.Image(image_response.content)
                image_view = toga.ImageView(image=image, style=Pack(width=200, height=200, padding_bottom=10, alignment='center'))
                article_box.add(image_view)
            except Exception as e:
                print(f"Failed to load image for {article['title']}: {str(e)}")
                article_box.add(toga.Label("Failed to load article image.", style=Pack(padding_bottom=10)))
        
        content_display = toga.MultilineTextInput(
            value="Loading full article...",
            readonly=True,
            style=Pack(flex=1, padding_bottom=10)
        )
        article_box.add(content_display)
        
        # Show the window immediately to ensure it appears
        article_window.content = article_box
        article_window.show()
        
        try:
            print(f"Fetching URL: {article['url']}")
            response = requests.get(article['url'], headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try multiple selectors to find the article content
            content = (
                soup.find('article') or
                soup.find('div', class_=['content', 'article-body', 'story', 'post-content', 'entry-content', 'Article', 'Article__content']) or
                soup.find('section', class_=['article-content']) or
                soup.find('div', id=['content', 'article', 'story'])
            )
            
            full_text = ""
            if content:
                # Extract paragraphs, excluding unwanted elements
                paragraphs = content.find_all('p', recursive=True)
                full_text = '\n\n'.join(p.text.strip() for p in paragraphs if p.text.strip() and not p.find_parents(['footer', 'aside', 'nav']))
                print(f"Scraped text length: {len(full_text)} chars")
            
            if not full_text:  # Fallback if scraping fails
                full_text = article.get('content') or article.get('description') or 'No full content available from this source.'
                if len(full_text) > 260:  # Check if content is truncated
                    full_text = f"{full_text}\n\n(Note: Full content may be truncated due to API limitations. Visit the website for the complete article.)"
                print(f"Fallback used: {full_text}")
        
        except requests.Timeout:
            full_text = "Request timed out: The article took too long to load. Please visit the website to read the full content."
            print("Timeout occurred while fetching article")
        except requests.HTTPError as e:
            if e.response.status_code == 403:
                full_text = "Access denied: This article may be behind a paywall or restricted. Please visit the website to read the full content."
            else:
                full_text = f"Failed to load full article: HTTP error {str(e)}.\n\nFallback: {article.get('content') or article.get('description') or 'No content available'}"
            print(f"HTTP Exception occurred: {str(e)}")
        except Exception as e:
            full_text = f"Failed to load full article: {str(e)}\n\nFallback: {article.get('content') or article.get('description') or 'No content available'}"
            print(f"Exception occurred: {str(e)}")
        
        # Update the content display
        content_display.value = full_text
        article_box.refresh()  # Force UI update
        
        url_button = toga.Button(
            'Visit Website',
            on_press=lambda w: webbrowser.open(article['url']),
            style=Pack(padding=5)
        )
        article_box.add(url_button)
        article_box.refresh()  # Force UI update

def main():
    return NoBullNews()