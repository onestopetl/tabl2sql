# tabl2sql
package for loading tabular data to SQL databases  
* logging module is used


## example run
```
import logging  
logging.basicConfig(level=logging.INFO)  
import tabl2sql  
args = ['-dirs', '/home/share/data/',  
        '-table', 'new_table',  
        '-sql', 'mysql',  
        '-driver', 'pymysql',  
        '-user', 'user',  
        '-pw', 'password',  
        '-host', '@server:port',  
        '-db', 'target_database',  
        '-sep', '\\t']  
tabl2sql.transform.main(args)
```

# benchmarking

|file size | row count | time | Hardware info | notes |  
| --- | --- | --- | --- | --- |  
|83MB | 200k rows | 1min | RHEL 7.3 , 2 XEON E5-2643 v4 @ 3.4GHz , 64GB RAM | |  
|260MB | 300k rows | 6min | RHEL 7.3 , 2 XEON E5-2643 v4 @ 3.4GHz , 64GB RAM | |  
|7.5GB | 8.3M rows | 2hrs 4min | RHEL 7.3 , 2 XEON E5-2643 v4 @ 3.4GHz , 64GB RAM | |  

## todo
* add ability to accept excel files  
* use hdf5 to allow any file size to work on lower RAM. perhaps dask after to speed up. alternatively could add steps for  
    1. check file size  
    2. break up if large    
    3. run main process one by one or in chunks  
* parallelize  
