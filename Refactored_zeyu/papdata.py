import pandas as pd
from household import Household, Person

class Papdata:
    """
    一个用于管理和处理人员、家庭和地点数据的类。
    """

    def __init__(self, hh_info: list[Household], places_df: pd.DataFrame):
        """
        初始化 Papdata 类，传入家庭信息和地点数据。

        参数:
            hh_info (list): 所有家庭的列表。
            places_df (pd.DataFrame): 包含各种地点数据的 DataFrame。
        """
        self.hh_info = hh_info
        self.places = places_df
        self.pap_dict: dict = {"people": {}, "homes": {}, "places": {}}

    def read_place(self) -> pd.DataFrame:
        """
        处理传入的地点数据。
        """
        places = self.places.copy()  # 创建副本以避免修改原始数据
        if 'capacity' not in places.columns:
            places['capacity'] = places.apply(self.estimate_capacity, axis=1)
        return places

    def estimate_capacity(self, row):
        """
        根据 POI 类别/名称估计地点容量。
        """
        name = row['location_name'].lower() if 'location_name' in row else ''
        naics = str(row['naics_code']) if 'naics_code' in row else ''
        if any(x in name for x in ['church', 'temple', 'chapel', 'mosque']):
            return 100
        elif any(x in name for x in ['school', 'university', 'college']):
            return 500
        elif any(x in name for x in ['hospital', 'medical center']):
            return 200
        elif any(x in name for x in ['restaurant', 'café', 'cafe', 'diner']):
            return 50
        elif any(x in name for x in ['store', 'shop', 'market']):
            return 30
        elif naics.startswith('722'):
            return 50
        elif naics.startswith('62'):
            return 60
        elif naics.startswith('61'):
            return 300
        elif naics.startswith('71'):
            return 150
        else:
            return 25

    def generate(self):
        """
        处理家庭和地点数据，填充 pap_dict，并返回结果。
        """
        # 添加家庭和人员
        for h in self.hh_info:
            home_dict = h.to_dict() if hasattr(h, "to_dict") else h
            home_id = int(home_dict["id"])
            self.pap_dict["homes"][home_id] = home_dict
            for p in (h.population if hasattr(h, "population") else []):
                person_dict = p.to_dict() if hasattr(p, "to_dict") else p
                self.pap_dict["people"][int(person_dict["id"])] = person_dict

        # 添加地点
        places = self.read_place()
        places_dict = {}
        for index, row in places.iterrows():
            places_dict[index] = {
                "label": row["location_name"],
                "cbg": row.get("cbg", -1),
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "capacity": row["capacity"]
            }
        self.pap_dict["places"] = places_dict

        return self.pap_dict