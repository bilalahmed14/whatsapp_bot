"""Custom WebView component for WhatsApp Web integration"""
import os
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings, QWebEnginePage
from PySide6.QtCore import QUrl

class WhatsAppWebView(QWebEngineView):
    """Custom WebView for WhatsApp Web with persistent storage"""
    
    def __init__(self, profile_dir):
        super().__init__()
        self.profile_dir = profile_dir
        self._setup_profile()
        self._setup_settings()
        
    def _setup_profile(self):
        """Set up custom web profile with persistent storage"""
        if not os.path.exists(self.profile_dir):
            os.makedirs(self.profile_dir)
            
        self.web_profile = QWebEngineProfile("WhatsAppBot", self)
        self.web_profile.setPersistentStoragePath(self.profile_dir)
        self.web_profile.setPersistentCookiesPolicy(QWebEngineProfile.AllowPersistentCookies)
        self.web_profile.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Set custom page with profile
        self.setPage(QWebEnginePage(self.web_profile, self))
        
    def _setup_settings(self):
        """Configure web settings"""
        settings = self.web_profile.settings()
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
        
    def load_whatsapp(self):
        """Load WhatsApp Web"""
        self.setUrl(QUrl("https://web.whatsapp.com")) 