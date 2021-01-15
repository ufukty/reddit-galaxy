// 2021 - github.com/ufukty
// GPL-3.0 License
// See the LICENSE file

// -------------------------------------------------------------
// IMPORT DATA INTO SPARK-SHELL
// -------------------------------------------------------------

val ds = spark.read.option("sep", "\t").option("header", "true").csv("hadoop_dataset")
ds.createOrReplaceTempView("ds")
ds.show

// -------------------------------------------------------------
// LINKS
// -------------------------------------------------------------

val links = spark.sql("""
    SELECT SOURCE_SUBREDDIT AS source, TARGET_SUBREDDIT AS target, COUNT(*) cnt 
    FROM ds 
    GROUP BY SOURCE_SUBREDDIT, TARGET_SUBREDDIT 
    ORDER BY cnt DESC
""")
links.cache
links.show
links.write.mode("overwrite").json("spark_output/links")

// ------------------------------------------------------------- 
// SANKEY DIAGRAM
// ------------------------------------------------------------- 

val top_sources = spark.sql("""
    SELECT SOURCE_SUBREDDIT AS subreddit, COUNT(*) cnt 
    FROM ds 
    GROUP BY SOURCE_SUBREDDIT 
    ORDER BY cnt DESC
    LIMIT 400
""")
top_sources.createOrReplaceTempView("top_sources")
top_sources.show
top_sources.write.mode("overwrite").json("spark_output/top_sources")

val top_targets = spark.sql("""
    SELECT TARGET_SUBREDDIT AS subreddit, COUNT(*) cnt 
    FROM ds 
    GROUP BY TARGET_SUBREDDIT 
    ORDER BY cnt DESC
    LIMIT 600
""")
top_targets.createOrReplaceTempView("top_targets")
top_targets.show
top_targets.write.mode("overwrite").json("spark_output/top_targets")

// ------------------------------------------------------------- 
// DEGREES
// ------------------------------------------------------------- 

val degrees = spark.sql("""
    SELECT 
        top_targets.subreddit AS subreddit, 
        top_targets.cnt AS in_degree, 
        top_sources.cnt AS out_degree,
        top_targets.cnt + top_sources.cnt AS degree
    FROM top_targets
    INNER JOIN top_sources
    ON top_targets.subreddit = top_sources.subreddit
""")
degrees.cache
degrees.show
degrees.write.mode("overwrite").json("spark_output/degrees")