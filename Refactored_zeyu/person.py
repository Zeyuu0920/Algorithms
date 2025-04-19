class Person:
    def __init__(self, id=None, home=None, sex=None, age=None) -> None:
        self.id = id              # 人员 ID
        self.home = home          # 家庭 ID
        self.sex = sex            # 性别
        self.age = age            # 年龄
        self.is_poi = False       # 是否在 POI
        self.visited = {}         # 访问过的 POI 和次数
        self.total_visited = 0    # 总访问次数
        self.curr_poi = ""        # 当前 POI
        self.hour_stayed = 0      # 在当前 POI 停留的小时数

    def visit(self, poi: str):
        if poi in self.visited:
            self.visited[poi] += 1
        else:
            self.visited[poi] = 1
        self.total_visited += 1
        self.is_poi = True
        self.curr_poi = poi
        self.hour_stayed = 1

    def leave(self):
        self.is_poi = False
        self.hour_stayed = 0
        self.curr_poi = ""

    def stay(self):
        self.hour_stayed += 1

    def at_home(self) -> bool:
        """Check if the person is at home (not in a POI)."""
        return not self.is_poi

    def to_dict(self):
        """Convert Person to dictionary for serialization."""
        return {
            "id": self.id,
            "home": self.home,
            "sex": self.sex,
            "age": self.age,
            "is_poi": self.is_poi,
            "curr_poi": self.curr_poi,
            "hour_stayed": self.hour_stayed,
            "total_visited": self.total_visited,
            "visited": self.visited
        }

    def __repr__(self) -> str:
        return (f"Person(id={self.id}, home={self.home}, is_poi={self.is_poi}, "
                f"curr_poi='{self.curr_poi}', hour_stayed={self.hour_stayed}, "
                f"total_visited={self.total_visited}, visited={self.visited})")