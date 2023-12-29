#!/usr/bin/env python3
import csv
import os

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

app = Flask(__name__)


@app.route("/", methods=['GET'])
def index():
    return render_template(
        'chart.html',
    )

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

@app.route('/bar', methods=['GET'])
def bar():

    cityName = request.args.get('cityName')
    cityState = request.args.get('cityState')
    page = request.args.get('page')

    print(cityName)
    print(cityState)


    if cityName and cityState and page:
        page = int(page)

        distance_matrix = {}

        csv_folder = './data'

        for filename in os.listdir(csv_folder):
            if filename.startswith('distance_matrix_') and filename.endswith('.csv'):
                csv_file = os.path.join(csv_folder, filename)

        with open(csv_file, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)

            for row in reader:
                key = row[0]
                value = float(row[1])
                distance_matrix[key] = value

        distances = []
        cities = []
        for key, value in distance_matrix.items():
            # print(key,value)
            city1, state1, city2, state2 = [part.strip() for part in key.split('_')]
            # print(city1,state1,city2,state2)
            if cityName == city1 and cityState == state1:
                cities.append(f"{city2}-{state2}")
                # print(value)
                distances.append(value)
            elif cityName == city2 and cityState == state2:
                cities.append(f"{city1}-{state1}")
                distances.append(value)

        print(cities)
        # 按距离进行升序排序
        sorted_indices = sorted(range(len(distances)), key=lambda k: distances[k])
        distances = [distances[i] for i in sorted_indices]
        cities = [cities[i] for i in sorted_indices]
        # 分页逻辑
        items_per_page = 50  # 每页显示的条目数
        startIndex = page * items_per_page
        endIndex = (page + 1) * items_per_page
        slicedDistances = distances[startIndex:endIndex]
        slicedCities = cities[startIndex:endIndex]
        result={'cities': slicedCities, 'distances': slicedDistances}
        #cache.set(cacheTen_key, json.dumps(result), ex=60 * 60)
        return jsonify({'cities': slicedCities, 'distances': slicedDistances})
    return jsonify({'error': 'Invalid request'})  # 对于不满足条件的请求，返回无效请求的响应


@app.route('/line', methods=['GET'])
def line():
    cityName = request.args.get('cityName')
    cityState = request.args.get('cityState')
    page = request.args.get('page')
    print(cityName)
    caheLine_key = f"line:{cityName}:{cityState}:{page}"
    cachedLine_result = cache.get(caheLine_key)
    if cachedLine_result is not None:
        resultLine = json.loads(cachedLine_result)
        return jsonify(resultLine)

    if cityName and cityState and page:
        page = int(page)
        reviews = get_reviews()

        import csv

        distance_matrix = {}

        # 遍历所有分割后的 CSV 文件
        csv_folder = './data'  # 指定存放分割后 CSV 文件的文件夹路径

        for filename in os.listdir(csv_folder):
            if filename.startswith('distance_matrix_') and filename.endswith('.csv'):
                csv_file = os.path.join(csv_folder, filename)

                with open(csv_file, mode='r', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    next(reader)  # 跳过表头

                    for row in reader:
                        key = row[0]
                        value = float(row[1])
                        distance_matrix[key] = value

        # 获取与指定城市相关的其他城市的距离和城市列表
        print(1)
        distances = []
        avg_scores = []
        cities_list = []

        for key, value in distance_matrix.items():
            city1, state1, city2, state2 = [part.strip() for part in key.split('_')]
            if (cityName == city1 and cityState == state1) or (cityName == city2 and cityState == state2):
                if cityName == city1:
                    cities_list.append(f"{city2}-{state2}")
                    scores = [float(review['score']) for review in reviews if
                              review['city'] == city2]
                else:
                    cities_list.append(f"{city1}-{state1}")
                    scores = [float(review['score']) for review in reviews if
                              review['city'] == city1]

                avg_score = sum(scores) / len(scores) if len(scores) > 0 else 0
                avg_scores.append(avg_score)

                distances.append(value)
        print(distances)
                # 按照距离排序
        sorted_indices = sorted(range(len(distances)), key=lambda k: distances[k])
        sorted_cities = [cities_list[i] for i in sorted_indices]
        sorted_avg_scores = [avg_scores[i] for i in sorted_indices]

        per_page = 10
        start_index = page * per_page
        end_index = (page + 1) * per_page

        # 提取当前页的城市名和平均评价得分
        page_cities = sorted_cities[start_index:end_index]
        page_avg_scores = sorted_avg_scores[start_index:end_index]

        # 将城市名和平均评价得分传递给前端
        result = {
            'cities': page_cities,
            'avg_scores': page_avg_scores
        }
        cache.set(caheLine_key, json.dumps(result), ex=60 * 60)

        return jsonify(result)
    return jsonify({'error': 'Invalid request'})  # 对于不满足条件的请求，返回无效请求的响应

@app.route('/stat/knn_reviews', methods=['GET'])
def final():

    global knnResult
    # 获取请求参数
    classes = request.args.get('classes')
    print(classes)
    k = request.args.get('k')
    words_num = request.args.get('words')
    caheKnn_key = f"knn:{classes}:{k}:{words_num}"
    cachedKnn_result = cache.get(caheKnn_key)
    if cachedKnn_result is not None:
         resultknn = json.loads(cachedKnn_result)
         knnResult = resultknn
         return jsonify(resultknn)

    if classes and k and words_num:

        classes = int(classes)
        k = int(k)
        words_num = int(words_num)

        # 尝试从缓存中获取结果
        redis_key = 'cities'
        cached_result = cache.get(redis_key)

        if cached_result is not None:
            cities = json.loads(cached_result)

        city_list = []
        distance_matrix = []
        start_time = time.time()
        for city in cities:
            city_list.append(city)
            distances = []
            for other_city in city_list:
                distance = calculate_distance(float(city['lat']), float(city['lng']), float(other_city['lat']),
                                              float(other_city['lng']))
                distances.append(distance)
            distance_matrix.append(distances)



        print(1)
            # KNN算法聚类
        clusters = [[] for _ in range(classes)]
        for i in range(len(city_list)):
            city_distances = distance_matrix[i]
            nearest_neighbors = sorted(range(len(city_distances)), key=lambda x: city_distances[x])[:k]
            cluster_index = i % classes
            clusters[cluster_index].append(city_list[i])
        for i, cluster in enumerate(clusters):
            print(f"Cluster {i + 1}: {cluster}")

        # 加载停用词
        stopwords = set()
        with open('stopwords.txt', 'r') as file:
            for line in file:
                word = line.strip()
                stopwords.add(word)

        print("success1")

        reviews = get_reviews()

        # 在每个类别中进行进一步处理
        # 在每个类别中进行进一步处理
        response = []
        total_review = 0
        for i in range(classes):
            cluster = clusters[i]
            center_city = cluster[0]  # 假设第一个城市为中心城市

            # 获取该类别中所有城市的评论和人口
            comments = []
            total_population = 0

            for city in cluster:
                # print(city)
                for review in list(reviews):
                    # print(review)
                    if (review['city'] == city['city']):
                        total_review = total_review + 1;
                        city_comments = [
                            {
                                'review': review['review'],
                                'score': review['score']
                            }
                            # for review in reviews if review['city']== city['city']
                        ]
                        comments.extend(city_comments)

                # 获取城市的人口
                population = city['population']
                total_population += float(population)
            print("success3")
            # 统计单词频次
            word_counts = {}
            for comment in comments:
                comment_text = comment['review']
                words = comment_text.split()
                for word in words:
                    word = word.lower()
                    if word not in stopwords:
                        word_counts[word] = word_counts.get(word, 0) + 1

            # 获取前n个最受欢迎的单词
            popular_words = sorted(word_counts, key=word_counts.get, reverse=True)[:words_num]
            # popular_word_counts = {word: word_counts[word] for word in popular_words}
            popular_word_counts = [word_counts[word] / total_review for word in popular_words]
            print(popular_word_counts)
            # 计算评论得分总和
            total_score = 0
            for comment in comments:
                score = int(comment['score'])
                total_score += score

            # 计算每千人口的平均得分
            average_score_per_thousand = (total_score / total_population) * 1000

            # 计算代码执行时间
            start_time = time.time()

            # 构建类别结果
            result = {
                'class': i + 1,
                'center_city': center_city['city'],
                'cities': [city['city'] for city in cluster],
                'popular_words': popular_words,
                'average_score_per_thousand': average_score_per_thousand,
                'population': total_population,
                'response_time': float(time.time() - start_time),
                'popular_word_count': popular_word_counts
            }
            # print(result)

            response.append(result)

        knnResult = response
        print(knnResult)
        # # 将结果存入缓存
        # # 将字典对象转换为 JSON 格式的字符串
        # encoded_results = json.dumps(response)
        # # 存入 Redis
        # cache.set(redis_key, encoded_results)
        cache.set(caheKnn_key, json.dumps(knnResult), ex=60 * 60)

        # 返回结果给前端
        return jsonify(response)
    return jsonify({'error': 'Invalid request'})  # 对于不满足条件的请求，返回无效请求的响应

def get_AllFrequency(words):
    word_count = {word: 0 for word in words}  # 初始化单词计数字典
    review = list(get_reviews())  # 将ItemPaged对象转换为列表
    total_comments = len(review)
    for comment in review:
        words = comment['review'].lower().split()  # 将评论转换为小写，并按空格拆分为单词列表
        for word in words:
            if word in word_count:
                word_count[word] += 1  # 如果单词出现在单词列表中，计数加一
    #word_frequency = {word: count / total_comments for word, count in word_count.items()}
    word_frequency = [count / total_comments for word, count in word_count.items()]
    return word_frequency

@app.route('/getRadar', methods=['GET'])
def get_radar():
    index=int(request.args.get('index'))
    global knnResult
    selectClass=knnResult[index]
    print(selectClass)
    center_city=selectClass['center_city']
    cities = selectClass['cities']
    cityNum=len(selectClass['cities'])
    labelstable=[]
    labelstable=selectClass['popular_words']
    allFrequency=get_AllFrequency(labelstable)
    classFrequency=selectClass['popular_word_count']
    print(allFrequency)
    state=''
    redis_key = 'cities'
    cached_result = cache.get(redis_key)
    if cached_result is not None:
        cities = json.loads(cached_result)
    weightedScore=selectClass['average_score_per_thousand']

    for city in cities:
        #print(city)
        if city['city']==center_city:
            state=city['state']
    print(state)
    result = {
        'labels': labelstable,
        'center_city': center_city,
        'cityNum': cityNum,
        'dataClass': classFrequency,
        'weighted_average_score': weightedScore,
        'dataAverage': allFrequency,
        'state': state,

    }
    return jsonify(result)

def get_reviews():
    # 尝试从缓存中获取结果
    # redis_key = 'reviews'
    # cached_result = cache.get(redis_key)
    # if cached_result is not None:
    #     reviews = json.loads(cached_result)
    #print(reviews)
    # container_review = database.get_container_client("reviews")
    # query_review = "SELECT Top 1000 c.score,c.city,c.review FROM c"
    # reviews = container_review.query_items(query_review, enable_cross_partition_query=True)
    import csv

    # 打开 CSV 文件并创建 reader 对象
    # with open('reviews.csv', 'r',encoding='utf-8') as csvfile:
    #     reader = csv.reader(csvfile)
    #     next(reader)
    #     reviews = []
    #     for row in reader:
    #         obj = {}
    #         obj['score'] = row[0]
    #         obj['city'] = row[1]
    #         obj['review'] = row[2]
    #         reviews.append(obj)
    reviews = []
    csv_folder = './data'
    for filename in os.listdir(csv_folder):
        if filename.startswith('reviews_') and filename.endswith('.csv'):
            csv_file = os.path.join(csv_folder, filename)

    with open(csv_file, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)

        for row in reader:
            obj = {}
            obj['score'] = row[0]
            obj['city'] = row[1]
            obj['review'] = row[2]
            reviews.append(obj)

    return reviews


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
