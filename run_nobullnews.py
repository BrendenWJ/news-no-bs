import sys
import os

# Add the src/ directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

# Explicit import
from nobullnews import app
NoBullNews = app.NoBullNews

if __name__ == "__main__":
    app = NoBullNews(formal_name="NoBullNews", app_id="com.bwjacobs.nobullnews")
    app.main_loop()