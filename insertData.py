#encoding:UTF-8

from pyspark import SparkConf, SparkContext
from pyspark.sql import SQLContext
from pyspark.sql import HiveContext
from pyspark.sql import Row

import time
import sys
from generator_images import captcha_generator as gen
import matplotlib.pyplot as plt
import os

chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabdefghijlmnqrtuwxy"
width, height, n_len, n_class = 140, 44, 6, len(chars) 

#----------------------------------------------------------------------
def create_sc(appname='insertdata', master='yarn', deploymode='client',
              num_executors=7, num_cores=2):
    """"""
    conf = SparkConf()
    conf.set("spark.app.name", appname)
    conf.set("spark.master", master)
    conf.set("spark.submit.deployMode", deploymode)
    conf.set("spark.executor.cores", `num_cores`)
    conf.set("spark.executor.instances", `num_executors`)
    conf.set("spark.sql.warehouse.dir", "hdfs://master:9000/user/hive/warehouse")
    sc = SparkContext(conf=conf)
    sqlContext = HiveContext(sc)
    return sc, sqlContext

#----------------------------------------------------------------------
def create_sql(sqlContext, tablename='genimages'):
    """"""
    tables = sqlContext.sql("SHOW TABLES")
    tables = tables.select('tableName').collect()
    tables = [i.asDict().values() for i in tables]
    if any([tablename in i for i in tables]):
        sqlContext.sql("DROP TABLE %s" %tablename)
    sqlContext.sql("CREATE EXTERNAL TABLE %s \
    (id INT COMMENT 'id of genimages', \
    mat ARRAY<ARRAY<ARRAY<ARRAY<BIGINT>>>> \
    COMMENT 'array of list') COMMENT \
    'This is used to store genimages' ROW FORMAT DELIMITED \
    FIELDS TERMINATED BY '\t' STORED AS TEXTFILE LOCATION \
    'hdfs://master:9000/user/hive/%s'" %(tablename, tablename))
    sqlContext.sql("DESCRIBE TABLE %s" %tablename).show()
    
#----------------------------------------------------------------------
def insert_images(sqlContext, width, height, cnt, tablename='genimages'):
    """"""
    start_time = time.time()
    num = 0
    imagegen = gen(width=width, height=height)
    while num < cnt:
        X, y = imagegen.next()
        newimages = sqlContext.createDataFrame([(num, X.tolist())], ['id', 'matrix'])
        newimages.write.mode('append').insertInto(tablename)
        num += 1
        print num
    end_time = time.time()
    print '####################################################'
    print 'the total time is ', end_time - start_time
    print 'the average time is ', (end_time - start_time) / float(num)
    
#----------------------------------------------------------------------
def main():
    sc, sqlContext = create_sc()
    create_sql(sqlContext)
    insert_images(sqlContext, width, height, 3000)

if __name__ == '__main__':
    main()