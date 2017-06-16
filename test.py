#encoding:UTF-8

from pyspark import SparkConf
from pyspark import SparkContext
from pyspark.sql import SQLContext
import time
import sys
from generator_images import captcha_generator as gen
import matplotlib.pyplot as plt

def test():
    application_name = "profile test"
    master = 'yarn'
    deploymode = 'client'
    num_executors = 7
    num_cores = 2
    
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabdefghijlmnqrtuwxy"
    width, height, n_len, n_class = 140, 44, 6, len(chars)    
    
    conf = SparkConf()
    conf.set("spark.app.name", application_name)
    conf.set("spark.master", master)
    conf.set("spark.submit.deployMode", deploymode)
    conf.set("spark.executor.cores", `num_cores`)
    conf.set("spark.executor.instances", `num_executors`)
    conf.set("spark.sql.warehouse.dir", "hdfs://master:9000/user/hive/warehouse");
    
    ###############################################################################
    #from pyspark.sql import SparkSession
    #sc = SparkSession.builder.master(master).appName(application_name).enableHiveSupport().getOrCreate()
    #sqlContext = SQLContext(sc)
    ################################################################################
    from pyspark.sql import HiveContext
    sc = SparkContext(conf=conf)
    sqlContext = HiveContext(sc)
    ################################################################################
    
    sqlContext.sql("DROP TABLE images5")
    
    sqlContext.sql("CREATE EXTERNAL TABLE images5 (id INT COMMENT 'id of images', mat ARRAY<ARRAY<ARRAY<ARRAY<BIGINT>>>> \
    COMMENT 'array of list') COMMENT \
    'This is used to store images' ROW FORMAT DELIMITED \
    FIELDS TERMINATED BY '\t' STORED AS TEXTFILE LOCATION 'hdfs://master:9000/user/hive/images5'")
    sqlContext.sql("DESCRIBE TABLE images5").show()
    
    sqlContext.sql("SELECT mat FROM images5 WHERE id==1").show()
    
    start_time = time.time()
    num = 0
    image = gen(width=width, height=height)
    while num < 10:
        X, y = image.next()
        newimage = sqlContext.createDataFrame([(num, X.tolist())], ['id', 'mat'])
        newimage.write.mode('append').insertInto('images5')
        num += 1
        end_time = time.time()
        print '--------------------------%d----------------------------'%num
        print 'the total time is', end_time - start_time
        print 'the average time is', (end_time - start_time)/64.0 /num
        
    dataset = sqlContext.sql("SELECT * FROM images5")
    dataset = dataset.repartition(14)
    
    dataset.rdd.mapPartitionsWithIndex(work_train).collect()
        
#----------------------------------------------------------------------
def work_train(worker_id, iterator):
    yield (worker_id, sum(iterator))

if __name__ == '__main__':
    test()