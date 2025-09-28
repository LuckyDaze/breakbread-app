from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class Edu:
    source: str; title: str; content: str; difficulty: str; publish_date: datetime; url: str

class AltX:
    def startups(self, platform="all"):
        return [
            {"platform":"startengine","company":"TechInnovate Inc.","description":"AI logistics",
             "min_investment":100,"valuation":5_000_000,"raised_percentage":65,"days_remaining":45},
            {"platform":"republic","company":"BlockChain Security Ltd.","description":"Enterprise security",
             "min_investment":50,"valuation":3_000_000,"raised_percentage":80,"days_remaining":30},
        ]

    def royalties(self, asset_type="all"):
        return [
            {"platform":"royalty_exchange","asset_type":"music","name":"Popular Band Catalog",
             "min_investment":1000,"expected_yield":9.5,"auction_end":(datetime.now()+timedelta(days=14)).strftime("%b %d, %Y")}
        ]

    def education(self):
        return [
            Edu("investopedia","Understanding Treasury Bonds","Treasury bonds are gov’t debt…",
                "beginner", datetime.now(), "https://www.investopedia.com/treasury-bonds")
        ]

altx = AltX()
