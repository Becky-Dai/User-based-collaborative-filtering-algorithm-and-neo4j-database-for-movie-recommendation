# User-based-collaborative-filtering-algorithm-and-neo4j-database-for-movie-recommendation
User-based collaborative filtering algorithm and neo4j database for movie recommendation  

基于用户的协同过滤算法和neo4j数据库的电影推荐

# The 1st step : the data processing work

第一步是数据处理工作。

pre_process.py is the data processing file, and specific usage and comments are in this file.

pre_process.py是数据处理文件，具体的用法和注释都在这个文件里。

The original data is under datasets folder, I zip all the data and uploaded it as it is quite large. 

原数据在datasets文件夹下，由于数据比较大，我就zip所有数据上传了。

![image](https://github.com/Becky-Dai/User-based-collaborative-filtering-algorithm-and-neo4j-database-for-movie-recommendation/assets/58799631/3ac6abae-0299-49e0-8971-2fd807e6ca1d)

The processed data is under datasets_out.

处理后的数据在datasets_out下。

![image](https://github.com/Becky-Dai/User-based-collaborative-filtering-algorithm-and-neo4j-database-for-movie-recommendation/assets/58799631/4a468c96-85ec-4e84-987e-40a1777308b8)

# The 2nd step : Computing on data with collaborative filtering algorithms

第二步是用协同过滤算法对数据进行计算

I'm using Django's framework, so I wrote all the specific code in pyneo_utils.py

我用的是Django的框架，所以我把具体的代码都写在了pyneo_utils.py里面

The exact usage and comments are clearly and detailed in pyneo_utils.py.

具体的用法和注释都被清楚且详细地写在了pyneo_utils.py里面。
