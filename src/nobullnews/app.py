import toga
from toga.style.pack import Pack, COLUMN, ROW
import requests
from bs4 import BeautifulSoup
import webbrowser

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
        category = self.category_picker.value if widget else 'general'
        location = self.location_picker.value if widget else 'World'
        filter_mode = self.filter_picker.value if widget else 'All News'
        article_count = int(self.count_picker.value) if self.count_picker.value else 10
        
        api_key = 'd09378c1f3124cebb0ce7e50aca5d11e'
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
            response = requests.get(url)
            data = response.json()
            print(f"URL: {url}")
            print(f"API Response: {data}")
            if 'articles' not in data:
                self.news_box.clear()
                self.news_box.add(toga.Label(f"API Error: {data.get('message', 'No articles found')}", style=Pack(padding=5)))
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
            for article in filtered_articles[:article_count]:
                article_row = toga.Box(style=Pack(direction=ROW, padding=5))
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
        except Exception as e:
            self.news_box.clear()
            self.news_box.add(toga.Label(f"Error fetching news: {str(e)}", style=Pack(padding=5)))

    def show_full_article(self, article):
        article_window = toga.Window(title=article['title'], size=(600, 400))
        article_box = toga.Box(style=Pack(direction=COLUMN, padding=10))
        
        full_text = "Loading full article..."
        content_display = toga.MultilineTextInput(
            value=full_text,
            readonly=True,
            style=Pack(flex=1, padding_bottom=10)
        )
        article_box.add(content_display)
        
        try:
            print(f"Fetching URL: {article['url']}")
            response = requests.get(article['url'], headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            print(f"HTTP Status: {response.status_code}")
            soup = BeautifulSoup(response.text, 'html.parser')
            content = soup.find('article') or soup.find('div', class_=['content', 'article-body', 'story'])
            full_text = '\n\n'.join(p.text.strip() for p in content.find_all('p') if p.text.strip()) if content else ''
            print(f"Scraped text length: {len(full_text)} chars")
            if not full_text:
                full_text = article.get('content') or article.get('description') or 'No full content available from this source.'
                print(f"Fallback used: {full_text}")
        except Exception as e:
            full_text = f"Failed to load full article: {str(e)}\n\nFallback: {article.get('content') or article.get('description') or 'No content available'}"
            print(f"Exception occurred: {str(e)}")
        
        content_display.value = full_text
        
        url_button = toga.Button(
            'Visit Website',
            on_press=lambda w: webbrowser.open(article['url']),
            style=Pack(padding=5)
        )
        article_box.add(url_button)
        
        article_window.content = article_box
        article_window.show()

def main():
    return NoBullNews()