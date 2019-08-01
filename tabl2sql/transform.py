
# python imports
import pandas as pd
import math
import time
from datetime import datetime, timedelta
import sys
from sqlalchemy import create_engine
import logging
log = logging.getLogger(__name__)

# project imports
from . import utils
from . import cleaning


def populate_df(filenames: list, seperator: str =',', encoding: str = 'cp1252'):
    """populate DataFrame for hand-off to load_data()

    Parameters
    ----------
    filenames : list
        A list of files to be imported, output of utils.getfilesfromdir() can be used
    separator : string
        define separator used in .txt when not csv

    Returns
    ----------
    staging_df: pd.DataFrame 
        dataframe populated with content from imported files
    """
    
    start_time = time.time()
    
    file_count = 0
    total_files = len(filenames)
    inp_cols = []

    log.info("Coalescing/preparing files:\n\t{} ".format(filenames))
    
    for filename in filenames:
        file_count += 1
        log.info("reading file {} of {}: {}".format(file_count, total_files, filename))
        read_df = pd.read_csv(r"{}".format(filename), sep=seperator, encoding=encoding)

        # setup column list & df
        if file_count == 1:
            inp_cols = list(read_df.columns.values)
            staging_df = read_df.copy()
            read_df = None
            log.info("\tcreated df with {} rows".format(staging_df.shape[0]))
    
        # check for new columns
        else:
            log.info("\tchecking for new columns")
            for col in read_df.columns:
                if col not in inp_cols:
                    log.info("*** adding column {} ***".format(col))
                    inp_cols.append(col)
            staging_df = staging_df.append(read_df, ignore_index=True)
            log.info("\tappending {} rows, totaling {}".format(read_df.shape[0], staging_df.shape[0]))
            read_df = None
        log.info('\tfile ripped time: {}'.format(timedelta(seconds=int(time.time() - start_time))))
            
    log.info("df info: \n{}".format(staging_df.info(verbose=True)))
    log.info("df head: \n{}".format(staging_df.head()))
    log.info('df populated in {}'.format(timedelta(seconds=int(time.time() - start_time))))
    
    return staging_df


def load_data(load_df: pd.DataFrame, db_engine, to_sql_mode='fail', dest_table='tabl2sql_{}'.format(datetime.now().strftime('%Y%m%d_%H%M%S')), dtype_dict: dict ={}):
    """receive df from populate_df() & load to db 

    Parameters
    ----------
    load_df : pd.DataFrame
        DataFrame to load to db
    db_engine : sqlalchemy engine
        define separator used in .txt when not csv
    to_sql_mode : string
        read pd.to_sql docs
    dest_table : string
        name of destination table in database. if exists, to_sql_mode must == 'append'. if not provided, function will create one
    dtype_dict : dictionary
        oracle defaults strings to clobs; 2nd output of cleaning.avoid_clob() --dtype_dict-- can be used to force varchar & determine field length

    Notes
    -----
    user must create engine using sqlalchemy & provide
    """
    start_time = time.time()
    if load_df.shape[0] < 50000:
        load_df.to_sql(dest_table, db_engine, if_exists=to_sql_mode, dtype=dtype_dict, index=False)
    else:
        num_loops = math.ceil(load_df.shape[0]/50000)
        partial_df = load_df.iloc[0:50000]
        partial_df.to_sql(dest_table, db_engine, if_exists=to_sql_mode, dtype=dtype_dict, index=False)
        for loop in range(1, num_loops):
            partial_df = load_df.iloc[loop*50000+1:(loop+1)*50000+1]
            partial_df.to_sql(dest_table, db_engine, if_exists='append', dtype=dtype_dict, index=False)
            log.info("\n\loaded {} lines".format((loop+1)*50000))

    log.info('loading completed in {}'.format(timedelta(seconds=int(time.time() - start_time))))


def load_test(load_df: pd.DataFrame, db_engine, to_sql_mode: str='fail', dest_table: str='tabl2sql_{}'.format(datetime.now().strftime('%Y%m%d_%H%M%S')), dtype_dict: dict ={}):
    num_loops = test_df.shape[0] 
    for loop in range(1,num_loops):
        partial_df = pd.DataFrame(test_df.iloc[loop]) 
        try:
            partial_df.to_sql(dest_table, db_engine, if_exists='append', dtype=dtype_dict, index=False)
        except:
            log.error("row {}: {} \n\t {}".format(loop, test_df.iloc[loop], test_df.iloc[loop].dtypes))


def main(args: list):
    """option to run package as script

    Parameters
    ----------
    -files : string
        comma separated string to be treated as list of files
    -dirs : string
        directories to pull files from 
    -table : string
        name of destination table in database. if exists, to_sql_mode must == 'append'. if not provided, function will create one
    -db : string
        name of destination db
    -mode : string
        to_sql_mode, read pd.to_sql docs
    -sep : string
        define separator used in .txt when not csv
    -encoding : string
        read pd.read_csv docs

    Notes
    -----
    user must create engine using sqlalchemy & provide
    """
    start_time = time.time()
    
    pargs = utils.parse_args(args)
    
    filenames = pargs.filenames
    if len(pargs.dirs) > 0:
        filenames.extend(utils.getfilesfromdir(pargs.dirs))
    
    conn = create_engine("{}+{}://{}:{}/{}".format(pargs.sql, pargs.driver, pargs.user, pargs.pw, pargs.db))
    input_df = populate_df(filenames, seperator=pargs.sep, encoding=pargs.encoding)
    log.debug('cleaning data start: {}'.format(timedelta(seconds=int(time.time() - start_time))))
    input_df = cleaning.clean_data(input_df)
    log.debug('cleaning data result:\n{}\n\n\n\n\n\n cleaning columns start: {}'.format(input_df.head(), timedelta(seconds=int(time.time() - start_time))))
    input_df = cleaning.clean_cols(input_df)
    log.debug('cleaning column result:\n{}\n\n\n\n\n\n recognize & format dates start: {}'.format(input_df.columns, timedelta(seconds=int(time.time() - start_time))))
    input_df = cleaning.to_date(input_df)
    log.debug('recognize & format dates result:\n{}\n\n\n\n\n\n avoid clob start: {}'.format(input_df.head(), timedelta(seconds=int(time.time() - start_time))))
    input_df, dtype_dict = cleaning.avoid_clob(input_df)
    log.debug('string conversion result:\n{}\n\n\n\n\n\n load start: {}'.format(input_df.head(), timedelta(seconds=int(time.time() - start_time))))
    
    load_data(load_df=input_df, db_engine=conn, to_sql_mode=pargs.mode, dest_table=pargs.table, dtype_dict=dtype_dict)
    log.debug('Transform Completed: {}'.format(timedelta(seconds=int(time.time() - start_time))))
    