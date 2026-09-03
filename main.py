# -*- coding: utf-8 -*-
"""大数据与人工智能 - 示例代码

演示 Python 基础用法，作为课程的起点。
运行：python main.py
"""


def hello():
    print("Hello, 大数据与人工智能！")
    print(f"当前 Python 版本已就绪，开始学习之旅吧。")


def demo_data_structure():
    """演示基础数据结构"""
    print("\n=== 基础数据结构演示 ===")

    # 列表
    scores = [85, 90, 78, 92, 88]
    print(f"成绩列表: {scores}")
    print(f"平均分: {sum(scores) / len(scores):.1f}")

    # 字典
    student = {"姓名": "张三", "学号": "2026001", "专业": "大数据与人工智能"}
    for key, value in student.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    hello()
    demo_data_structure()
