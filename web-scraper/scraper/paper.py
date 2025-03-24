class Paper:
    def __init__(self, url, title, pages, author, volume_id=None):
        self.url = url
        self.title = title
        self.pages = pages
        self.author = author
        self.volume_id = volume_id