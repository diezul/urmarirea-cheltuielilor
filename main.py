from kivy.app import App
from kivy.uix.webview import WebView

class MyApp(App):
    def build(self):
        webview = WebView()
        webview.url = "http://127.0.0.1:5000"  # Adresa unde rulează aplicația Flask
        return webview

if __name__ == "__main__":
    MyApp().run()
