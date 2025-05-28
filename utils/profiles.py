from dataclasses import dataclass


@dataclass
class Profile:
    name: str  # 经理人的名字
    title: str  # 经理人的职位
    company: str  # 经理人所在的公司
    slogan: str  # 经理人的广告语


profile = Profile(
    name="金继仁",
    title="风险管理顾问",
    company="卓信保险经纪有限公司",
    slogan="保障你的未来",
)
