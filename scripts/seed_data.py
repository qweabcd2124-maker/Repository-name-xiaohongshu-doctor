"""
生成模拟 baseline 种子数据用于开发和演示。
实际比赛前应替换为真实采集的小红书笔记数据。

Usage:
    python scripts/seed_data.py
"""
import sqlite3
import json
import random
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "data", "baseline.db")

FOOD_TITLES = [
    "手把手教你做日式溏心蛋！零失败！", "一周减脂餐分享｜好吃不胖",
    "这家店的牛肉面绝了！排队2小时值得", "5分钟早餐｜上班族必备快手料理",
    "在家复刻米其林甜品，成本不到20元", "今日份便当🍱简单又好看",
    "火锅底料测评！10款热门品牌大比拼", "减脂期也能吃的神仙甜品合集",
    "探店｜藏在巷子里的宝藏咖啡馆", "空气炸锅食谱合集｜懒人必备",
    "一人食晚餐｜治愈独居的小确幸", "网红餐厅避雷指南‼️别再踩坑了",
    "秋天第一杯奶茶自制教程🧋", "宿舍神器！不用火不用电也能做大餐",
    "妈妈的味道｜家常红烧肉做法", "低卡高蛋白沙拉｜越吃越瘦",
]

FASHION_TITLES = [
    "小个子穿搭｜155cm也能穿出大长腿", "一衣多穿｜一件白衬衫的7种搭配",
    "秋冬必入的5件基础款｜百搭不出错", "微胖女孩的显瘦穿搭公式",
    "通勤穿搭分享｜上班也要美美的", "今日OOTD｜日系文艺风",
    "学生党平价穿搭｜全身不过百", "这条裤子也太显腿长了吧！",
    "韩系穿搭合集｜温柔到骨子里", "显白穿搭｜黄皮女孩看过来",
    "春季穿搭灵感｜拒绝臃肿出门", "大衣+毛衣的神仙组合",
    "氛围感穿搭教程｜秒变韩剧女主", "梨形身材穿搭指南｜遮肉显瘦",
    "极简穿搭｜衣柜里只需要这10件", "约会穿搭｜又甜又辣的一天",
]

TECH_TITLES = [
    "2024最值得买的平板电脑推荐", "iPhone vs 安卓？真实使用一年对比",
    "程序员必备的10个效率工具", "AI绘画入门教程｜零基础也能出大片",
    "MacBook选购指南｜别花冤枉钱", "智能家居改造全记录｜花了3万值吗",
    "这个APP改变了我的学习方式", "数码产品年度盘点｜好用到哭",
    "iPad学习法｜从学渣到学霸", "耳机横评｜千元内最值得买的5款",
    "NAS入门指南｜打造私人云存储", "手机摄影技巧｜拍出电影质感",
    "机械键盘入坑指南｜新手必看", "二手数码避坑指南‼️", 
    "AI工具合集｜效率提升10倍", "极简桌面布置｜打造高效工作台",
]

FOOD_TAGS = ["美食分享", "食谱", "减脂餐", "早餐", "探店", "家常菜", "烘焙", "减肥餐", "火锅", "咖啡"]
FASHION_TAGS = ["穿搭", "OOTD", "显瘦", "平价穿搭", "韩系", "日系", "通勤穿搭", "基础款", "搭配", "秋冬穿搭"]
TECH_TAGS = ["数码", "科技", "好物推荐", "效率工具", "AI", "iPad", "手机", "智能家居", "App推荐", "测评"]


def generate_notes(category, titles, tags_pool, count=500):
    """为指定垂类生成模拟笔记数据"""
    notes = []
    for _ in range(count):
        title = random.choice(titles)
        title_var = title
        if random.random() > 0.5:
            suffixes = ["", "！", "✨", "🔥", "｜建议收藏", "‼️"]
            title_var = title + random.choice(suffixes)

        num_tags = random.randint(2, 8)
        selected_tags = random.sample(tags_pool, min(num_tags, len(tags_pool)))

        is_viral = random.random() < 0.15
        if is_viral:
            likes = random.randint(500, 50000)
            collects = random.randint(200, 20000)
            comments = random.randint(50, 5000)
        else:
            likes = random.randint(0, 500)
            collects = random.randint(0, 200)
            comments = random.randint(0, 50)

        notes.append((
            category,
            title_var,
            len(title_var),
            f"这是一篇关于{category}的笔记正文内容，包含详细的分享...",
            json.dumps(selected_tags, ensure_ascii=False),
            random.randint(6, 23),
            likes,
            collects,
            comments,
            random.choice([500, 1000, 5000, 10000, 50000, 100000]),
            1 if is_viral else 0,
            1 if random.random() > 0.4 else 0,
            round(random.uniform(0.05, 0.4), 2),
            round(random.uniform(0.3, 0.9), 2),
        ))
    return notes


def seed():
    """写入种子数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM notes")

    all_notes = []
    all_notes.extend(generate_notes("food", FOOD_TITLES, FOOD_TAGS, 500))
    all_notes.extend(generate_notes("fashion", FASHION_TITLES, FASHION_TAGS, 500))
    all_notes.extend(generate_notes("tech", TECH_TITLES, TECH_TAGS, 500))

    cursor.executemany("""
        INSERT INTO notes (
            category, title, title_length, content, tags,
            publish_hour, likes, collects, comments, followers,
            is_viral, cover_has_face, cover_text_ratio, cover_saturation
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, all_notes)

    conn.commit()
    print(f"已插入 {len(all_notes)} 条种子数据")
    conn.close()


if __name__ == "__main__":
    seed()
