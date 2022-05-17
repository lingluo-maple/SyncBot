from typing import Dict, List, Tuple, Optional

from pydantic import BaseModel


class Config(BaseModel):
    account: int
    verify_key: str
    api_id: int
    api_hash: str
    bot_token: str
    proxy: Optional[Tuple]
    # MTProto("host", port, "secret") or Pysocks(type, 'hostname', port)

class ForwardGroupConfig(Dict):
    """QQ Group id: TG chat id"""
    def getQQGroup(self, group: int):
        keys = list(self.values())
        for i in range(len(keys)):
            if keys[i] == group:
                return list(self.keys())[i]
    
    def getTGGroup(self, group: int):
        return self[group]


config = Config(
    account=100001,
    verify_key="miraiVerifyKey",
    api_id=100000,
    api_hash="api_id and api_hash from my.telegram.org",
    bot_token="int:str bot_token from @BotFather",
    proxy=(
        "host",
        1234,
        "MTProto secret remove the first two characters (ee)",
    ),
)

groups = ForwardGroupConfig(
    {
        123456789012: -1001234567890
        }
)
