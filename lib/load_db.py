import pandas as pd
from sqlalchemy import *
from sqlalchemy_utils import create_database, database_exists
import os

def setup_db(db_path):
    engine = create_engine('sqlite:///' + db_path)
    if not database_exists(engine.url):
        create_database(engine.url)

    meta = MetaData(bind=engine)
    
    table_counts = Table('counts', meta,
                    Column('da', Integer, index=True),
                    Column('naics_id', Integer, index=True),
                    Column('without_employees', Integer, nullable=True),
                    Column('total_with_employees', Integer, nullable=True),
                    Column('1_4', Integer, nullable=True),
                    Column('5_9', Integer, nullable=True),
                    Column('10_19', Integer, nullable=True),
                    Column('20_49', Integer, nullable=True),
                    Column('50_99', Integer, nullable=True),
                    Column('100_199', Integer, nullable=True),
                    Column('200_499', Integer, nullable=True),
                    Column('500_+', Integer, nullable=True))

    table_geo = Table('geo', meta,
                    Column('da', Integer, index=True),
                    Column('cd_name', TEXT, nullable=True),
                    Column('csd_name', TEXT, nullable=True),
                    Column('cma_ca_name', TEXT, nullable=True),
                    Column('pr_name', TEXT, nullable=True),
                    Column('co_name', TEXT, nullable=True))

    table_naics = Table('naics', meta,
                    Column('naics_id', Integer, index=True),
                    Column('description', TEXT))

    meta.create_all(engine)

    return engine

def load_db(filepath, chunksize, engine, table_name, cleaner_fn, encoding=None):
    files = os.listdir(filepath)
    for f in files:
        print 'Loading file: ' + f
        
        for df in pd.read_csv(filepath + '/' + f, chunksize=chunksize,
                              encoding=encoding):
            cleaned_df = cleaner_fn(df)
            cleaned_df.to_sql(table_name, engine, if_exists='append', index=False)

def clean_cbp_df(df):
    df.loc[-1] = df.columns.values
    df.index = df.index + 1
    df.columns = [0]
    df = df.sort()

    df = pd.DataFrame([map(int, (x[:8], x[8:14], x[14:16], x[16:])) for x in df[0]])
    df.columns = ['da', 'naics_id', 'range', 'value']

    table = pd.pivot_table(df, values='value', columns='range', index=['da', 'naics_id'])
    col_names = ['without_employees','1_4', '5_9', '10_19', '20_49', '50_99', '100_199',
                 '200_499', '500_+']

    if len(table.columns) != len(col_names):
        print "Table lengths do not match."
        sys.exit(0)

    table.columns = col_names
    table.reset_index(inplace=True)
    table['total_with_employees'] = table[table.columns[3:]].sum(1)

    return table

def clean_geo_df(df):
    df.rename(columns={'DAUID':'da'}, inplace=True)
    df.columns = pd.Series(df.columns).apply(lambda x: x.lower())
    df.pr_name = df.pr_name.apply(lambda x: x.split(' / ')[0])
    return df

def clean_naics_df(df):
    df.columns = ['naics_id', 'description']
    return df

if __name__ == '__main__':
    path = 'V:\Economic Intelligence\Data & Forecasts for MI\CBP Query Tool\data'
    cbp_path = path + '/counts'
    naics_path = path + '/naics'
    geo_path = path + '/geo'

    engine = setup_db('V:\Economic Intelligence\Data & Forecasts for MI\CBP Query Tool\code\cbp_query_tool\lib/data.db')
    chunksize = 20000

    print 'Loading naics table...'
    load_db(naics_path, chunksize, engine, 'naics', clean_naics_df)

    print 'Loading geo table...'
    load_db(geo_path, chunksize, engine, 'geo', clean_geo_df)

    print 'Loading counts table...'
    load_db(cbp_path, chunksize, engine, 'counts', clean_cbp_df)

    print 'Finished.'


    
    
    
    
