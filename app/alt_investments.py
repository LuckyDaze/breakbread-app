# app/alt_investments.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

@dataclass
class EducationalItem:
    source: str
    title: str
    content: str
    category: str
    difficulty: str
    publish_date: datetime
    url: str

class AltInvestments:
    def __init__(self, config_path: str = "config/investment_platforms.json"):
        with open(config_path, "r") as f:
            self.cfg = json.load(f)

    # ------- Startup opportunities (mocked) -------
    def startups(self, platform: str = "all") -> List[Dict[str, Any]]:
        items = []
        if platform in ("all", "startengine"):
            items += [
                {"platform":"startengine","company":"TechInnovate Inc.",
                 "description":"AI logistics optimization",
                 "min_investment":100,"valuation":5_000_000,
                 "raised_percentage":65,"days_remaining":45}
            ]
        if platform in ("all", "republic"):
            items += [
                {"platform":"republic","company":"BlockChain Security Ltd.",
                 "description":"Enterprise blockchain security",
                 "min_investment":50,"valuation":3_000_000,
                 "raised_percentage":80,"days_remaining":30}
            ]
        if platform in ("all", "wefunder"):
            items += [
                {"platform":"wefunder","company":"GreenEnergy Solutions",
                 "description":"Next-gen solar efficiency",
                 "min_investment":250,"valuation":8_000_000,
                 "raised_percentage":40,"days_remaining":60}
            ]
        return items

    # ------- Royalty/IP opportunities (mocked) -------
    def royalties(self, asset_type: str = "all") -> List[Dict[str, Any]]:
        out = []
        if asset_type in ("all","music"):
            out.append({
                "platform":"royalty_exchange","asset_type":"music",
                "name":"Popular Band 2015-2023 Catalog","min_investment":1000,
                "expected_yield":9.5,
                "auction_end": (datetime.utcnow() + timedelta(days=14)).date()
            })
        if asset_type in ("all","patents"):
            out.append({
                "platform":"royalty_exchange","asset_type":"patent",
                "name":"Wireless Charging IP Family","min_investment":5000,
                "expected_yield":11.2,
                "auction_end": (datetime.utcnow() + timedelta(days=21)).date()
            })
        return out

    # ------- Education content (mocked list; swap to RSS later) -------
    def education(self) -> List[EducationalItem]:
        return [
            EducationalItem(
                source="investopedia",
                title="Understanding Treasury Bonds for Beginners",
                content="Treasury bonds are long-term U.S. government debt...",
                category="bonds",
                difficulty="beginner",
                publish_date=datetime.utcnow(),
                url="https://www.investopedia.com/treasury-bonds"
            ),
            EducationalItem(
                source="motley_fool",
                title="5 Startup Investing Ideas",
                content="Early-stage investing can be rewarding but risky...",
                category="startups",
                difficulty="intermediate",
                publish_date=datetime.utcnow(),
                url="https://www.fool.com/"
            )
        ]

altx = AltInvestments()
