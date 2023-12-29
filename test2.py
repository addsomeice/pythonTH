#!/usr/bin/env python3
from flask import Flask, jsonify
from flask import render_template
from flask import request
import math
import json
from azure.cosmos import CosmosClient
import redis
import time

redis_passwd = "dH83jFtaYDZA7socl4hld3cGCgMu81TCrAzCaMSKXMs="
redis_host = "LiushuaiRedis.redis.cache.windows.net"
cache = redis.StrictRedis(
    host=redis_host, port=6380,
    db=0, password=redis_passwd,
    ssl=True,
)

if cache.ping():
    print("pong")


DB_CONN_STR ="AccountEndpoint=https://tutorial-uta-cse6332.documents.azure.com:443/;" \
             "AccountKey=fSDt8pk5P1EH0NlvfiolgZF332ILOkKhMdLY6iMS2yjVqdpWx4XtnVgBoJBCBaHA8PIHnAbFY4N9ACDbMdwaEw==;"
db_client = CosmosClient.from_connection_string(conn_str=DB_CONN_STR)
database = db_client.get_database_client("tutorial")

def calculate_distance(lat1, lng1, lat2, lng2):

    # 直线距离计算方法
    # distance = ((lat2 - lat1) ** 2 + (lng2 - lng1) ** 2) ** 0.5

    # 球面距离计算方法
    # 将经纬度转换为弧度
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)

    # 使用 Haversine 公式计算球面距离
    delta_lat = lat2_rad - lat1_rad
    delta_lng = lng2_rad - lng1_rad
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = 6371 * c  # 地球平均半径为 6371 公里

    return distance

# 尝试从缓存中获取结果
redis_key = 'cities'
cached_result = cache.get(redis_key)

if cached_result is not None:
    cities = json.loads(cached_result)
#
# 计算城市之间的距离
distance_matrix = {}
visited_cities = set()

for i in range(len(cities)):
    city1 = cities[i]
    for j in range(i + 1, len(cities)):
        city2 = cities[j]
        if city1['city'] == city2['city'] and city1['state'] == city2['state']:
            continue  # Skip if the cities are the same

        distance = calculate_distance(float(city1['lat']), float(city1['lng']), float(city2['lat']),
                                      float(city2['lng']))

        key1 = f"{city1['city']}_{city1['state']}_{city2['city']}_{city2['state']}"
        key2 = f"{city2['city']}_{city2['state']}_{city1['city']}_{city1['state']}"

        if key1 not in visited_cities and key2 not in visited_cities:
            distance_matrix[key1] = distance
            visited_cities.add(key1)

print("start")
import csv


# 将 distance_matrix 存储为 CSV 文件
csv_file = 'distance_matrix.csv'

with open(csv_file, mode='w', newline='',encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['key', 'value'])  # 写入表头

    for key, value in distance_matrix.items():
        writer.writerow([key, value])  # 写入每一行数据

