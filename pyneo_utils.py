from py2neo import Graph, Node, Relationship, NodeMatcher, RelationshipMatcher
# -*- coding:utf-8 -*-
import pandas as pd
from neo4j import GraphDatabase

# 连接数据库驱动
uri = "bolt://localhost:7687"
driver = GraphDatabase.driver(uri, auth=("neo4j", "123456"))

# 参数设置
k = 10  # 考虑最相似的用户，也就是最邻近的邻居
moives_common = 3  # 考虑用户相似度，要有多少个电影公共看过
usesrs_common = 2  # 至少共通看过2个电影，说用户相似
threshold_sim = 0.9  # 用户相似度阈值


def queries(start, s1, s2):
    userid = int(start)
    m = 3
    # 电影类型
    genre = []
    if int(s1):
        # 排除的话
        with driver.session() as session:
            try:
                # 查询所有类型,放入元组中
                q = session.run(f"""MATCH (g:Genre) RETURN g.genre AS genre""")
                result = []
                for i, r in enumerate(q):
                    result.append(r["genre"])

                # 将 genre 列转为 DataFrame 类型，并列出提示
                df = pd.DataFrame(result, columns=["genre"])
                print()
                print(df)
                # 根据上面的输出，输入类型
                inp = s2
                if len(inp) != 0:
                    inp = inp.split(",")
                    genre = [df["genre"].iloc[int(x)] for x in inp]
            finally:
                print("Error")

    # 进行查询, 用户u1（start）对电影的评分, 降序排序
    with driver.session() as session:
        q = session.run(f"""
                MATCH (u1:User {{ id:{userid} }})-[r:RATED]-(m:Movie)
                RETURN m.title AS title,r.grading AS grade
                ORDER BY grade DESC
            """)
        # 从neo4j数据库中根据用户id搜索出被该用户评分的电影名字，并降序排列
        print()
        print("你评分过的电影如下所示: ")

        # 将 session 查询结果放入元组中
        result = []
        for r in q:
            result.append([r["title"], r["grade"]])

        # 输出结果, 用户对于电影的一个评分列表
        if len(result) == 0:
            print("没有结果推荐")
        else:
            df = pd.DataFrame(result, columns=["title", "grade"])
            print()
            print(df.to_string(index=True))
        print("---------------------------------------------------------------------------------------------------")

        # 删除用户相似性关系
        session.run(f"""
                MATCH (u1:User)-[s:SIMILARITY]-(u2:User)
                DELETE s
            """)

        # 重新计算用户相似性，u1指的是输入值start，也就是当前用户，u2指的是和u1都k看过某部电影的用户
        # 通过电影连接两个用户, u1 --rated-- movie --rated-- u2，得到U1和U2两个用户的信息
        # COUNT(m) m=3 指的是，推荐3部电影
        # 计算u1,u2共同评论过的电影,然后根据两个人的评分来计算余弦相似度：(用户1评分 * 用户2评分)的总和,除以他们分别的根号平方和，如下所示：
        # SUM(r1.grading * r2.grading)/(SQRT( SUM(r1.grading^2) ) * SQRT( SUM(r2.grading^2) )) as sim
        # 筛选余弦相似度的余值 movies_common >= {moives_common} AND sim > {threshold_sim}，moives_common和threshold_sim的数值在该文件顶部自定义了
        # MERGE (u1)-[s:SIMILARITY]-(u2) 创建u1和u2之间的相似度
        # SET s.sim = sim，设置相似度的数值
        session.run(f"""
                MATCH (u1:User {{id : {userid}}})-[r1:RATED]-(m:Movie)-[r2:RATED]-(u2:User)
                WITH
                    u1, u2,
                    COUNT(m) AS movies_common,
                    SUM(r1.grading * r2.grading)/(SQRT( SUM(r1.grading^2) ) * SQRT( SUM(r2.grading^2) )) as sim
                WHERE movies_common >= {moives_common} AND sim > {threshold_sim}
                MERGE (u1)-[s:SIMILARITY]-(u2)
                SET s.sim = sim
            """)

        # 条件语句拼装, 过滤类型
        Q_GENRE = ""
        if len(genre) > 0:
            Q_GENRE = "AND ((SIZE(gen) > 0) AND "
            Q_GENRE += "(ANY(X IN " + str(genre) + " WHERE X IN gen))"
            Q_GENRE += ")"
        # MATCH (u1:User{{id : {userid}}})-[s:SIMILARITY]-(u2:User) 找到相似度用户
        # ORDER BY s.sim DESC LIMIT {k} 按照相似度的降序进行排列
        # MATCH (m:Movie)-[r:RATED]-(u2) U2指的是相似度高的用户与电影的关系
        # OPTIONAL MATCH (g:Genre)--(m) u2的其他信息
        # WITH u1,u2,s,m,r, COLLECT(DISTINCT g.genre) AS gen 把u2的信息集合提取了
        # WHERE NOT((m)-[:RATED]-(u1)) {Q_GENRE} 判断；在不在用户不喜欢的电影分类当中——过滤操作
        # 返回剩下的电影信息，m.title AS title,
        # 还原实际的分值 SUM(r.grading * s.sim)/SUM(s.sim) AS grade
        # 返回电影信息，以降序的方式
        q = session.run(f"""
                MATCH (u1:User{{id : {userid}}})-[s:SIMILARITY]-(u2:User)
                WITH u1,u2,s
                ORDER BY s.sim DESC LIMIT {k}
                MATCH (m:Movie)-[r:RATED]-(u2)
                OPTIONAL MATCH (g:Genre)--(m)
                WITH u1,u2,s,m,r, COLLECT(DISTINCT g.genre) AS gen
                WHERE NOT((m)-[:RATED]-(u1)) {Q_GENRE}
                WITH
                    m.title AS title,
                    SUM(r.grading * s.sim)/SUM(s.sim) AS grade,
                    COUNT(u2) AS num,
                    gen
                WHERE num >= {usesrs_common}
                RETURN title,grade,num,gen
                ORDER BY grade DESC, num DESC
                LIMIT {m}
            """)

        print("推荐的电影:")
        result = []
        for r in q:
            result.append([r["title"], r["grade"], r["num"], r["gen"]])
        if len(result) == 0:
            print("无推荐")

        df = pd.DataFrame(result, columns=["title", "avg grade", "num recommenders", "genre"])
        print()
        print(len(result))
        print(df.to_string(index=True))
        print("---------------------------------------------------------------------------------------------------")
        output="Recommended movies"
        if len(result) == 1:
            return {"list1": result[0][0], "list2": "No the second movie", "list3": "No the third movie", "output": output,
                    "avg grade1": result[0][1],
                    "avg grade2": "None", "avg grade3": "None", "num recommenders1": result[0][2],
                    "num recommenders2": "None",
                    "num recommenders3": "None", "genre1": result[0][3], "genre2": "None",
                    "genre3": "None"}
        if len(result) == 2:
            return {"list1": result[0][0], "list2": result[1][0], "list3": "No the third movie", "output": output,
                    "avg grade1": result[0][1],
                    "avg grade2": result[1][1], "avg grade3": "None", "num recommenders1": result[0][2],
                    "num recommenders2": result[1][2],
                    "num recommenders3": "None", "genre1": result[0][3], "genre2": result[1][3],
                    "genre3": "None"}
        if len(result) >= 3:
            return {"list1": result[0][0], "list2": result[1][0], "list3": result[2][0], "output": output,
                    "avg grade1": result[0][1],
                    "avg grade2": result[1][1], "avg grade3": result[2][1], "num recommenders1": result[0][2],
                    "num recommenders2": result[1][2],
                    "num recommenders3": result[2][2], "genre1": result[0][3], "genre2": result[1][3],
                    "genre3": result[2][3]}
        else:
            return {"list1": "No the first movie", "list2": "None", "list3": "None", "output": "None",
                    "avg grade1": "None",
                    "avg grade2": "No the second movie", "avg grade3": "None", "num recommenders1": "None",
                    "num recommenders2": "None",
                    "num recommenders3": "No the third movie", "genre1": "None", "genre2": "None",
                    "genre3": "None"}

