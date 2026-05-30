from urllib.parse import urlparse
class SourceVerifier:
    def score(self, url: str) -> float:
        host=urlparse(url).netloc.lower()
        if any(x in host for x in ['github.com','docs.','wikipedia.org','gov','edu']): return 0.9
        if any(x in host for x in ['medium.com','blog','forum']): return 0.5
        return 0.6
    def annotate(self, results: list[dict]) -> list[dict]:
        for r in results:
            u=r.get('href') or r.get('url') or ''
            r['source_score']=self.score(u)
        return results
