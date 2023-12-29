#!/usr/bin/env python3
from flask import Flask, jsonify
from flask import render_template
from flask import request
import math
import json
from azure.cosmos import CosmosClient
import redis
import time

DB_CONN_STR =  "AccountEndpoint=https://tutorial-uta-cse6332.documents.azure.com:443/;" \
               "AccountKey=fSDt8pk5P1EH0NlvfiolgZF332ILOkKhMdLY6iMS2yjVqdpWx4XtnVgBoJBCBaHA8PIHnAbFY4N9ACDbMdwaEw==;"
db_client = CosmosClient.from_connection_string(conn_str=DB_CONN_STR)
database = db_client.get_database_client("tutorial")
# city_name = 'Parma'
# container = database.get_container_client("us_cities")
# query_review = "SELECT * FROM c WHERE c.city = @city_name"
# params = [dict(name="@city_name", value=city_name)]
# reviews = list(container_reviews.query_items(query_review, parameters=params , enable_cross_partition_query=True))
# print(reviews)
# for review in reviews:
#     # print(reviews['score'])
#     score = int(review['score'])
#     print(score)

import math
import json
import redis

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

# 建立与 Redis 的连接
redis_passwd = "dH83jFtaYDZA7socl4hld3cGCgMu81TCrAzCaMSKXMs="
redis_host = "LiushuaiRedis.redis.cache.windows.net"
cache = redis.StrictRedis(
    host=redis_host, port=6380,
    db=0, password=redis_passwd,
    ssl=True,
)

if cache.ping():
    print("pong")


# def purge_cache():
#     for key in cache.keys():
#         cache.delete(key.decode())
# purge_cache()
# print("true")

# # 从数据库中获取城市数据
# container = database.get_container_client("us_cities")
#
# # 第一步查询：获取城市属性
# query = "SELECT c.city, c.lat, c.lng, c.state FROM c"
# result = container.query_items(query, enable_cross_partition_query=True)
# cities = list(result)
#
# print(cities)
# #
# redis_key = 'cities'
# encoded_cities = json.dumps(cities)
# cache.set(redis_key, encoded_cities)

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

print(distance_matrix)

