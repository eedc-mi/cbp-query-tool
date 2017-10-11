import pandas as pd
import sqlalchemy as sql
import numpy as np
import itertools

class Query(object):
    target_geo_level_list = ['DA', 'CSD', 'CMA_CA', 'Province']
    target_geo_columns = ['da', 'csd_name', 'cma_ca_name', 'pr_name'] 
    parent_geo_level_list = ['CSD', 'CMA_CA', 'Province', 'Canada']
    parent_geo_columns = ['csd_name', 'cma_ca_name', 'pr_name', 'co_name']
    count_table_name = 'counts'
    geo_table_name = 'geo'
    naics_table_name = 'naics'
    naics_id_column_name = 'naics_id'
    naics_desc_column_name = 'description'
    size_columns = ['without_employees', 'total_with_employees', '1_4',
                    '5_9', '10_19', '20_49', '50_99', '100_199', '200_499',
                    '500_+']
    pretty_to_db = dict(zip(target_geo_level_list, target_geo_columns) +
                        zip(parent_geo_level_list, parent_geo_columns) +
                        [(None, 'None')])
    db_to_pretty = dict(zip(target_geo_columns, target_geo_level_list) +
                        zip(parent_geo_columns, parent_geo_level_list) +
                        [(None, 'None')])

    def __init__(self, engine):
        self.target_geo_level = self.target_geo_columns[0]
        self.parent_geo = None
        self.parent_geo_level = self.parent_geo_columns[0]
        self.naics_level = 2
        self.df = pd.DataFrame()
        self.engine = engine

    def __str__(self):
        return ('-- Target geo-level: %s \n'
                '-- Parent geo-level: %s \n'
                '-- Parent geography: %s \n'
                '-- NAICS level: %s') % \
                (self.db_to_pretty[self.target_geo_level],
                 self.db_to_pretty[self.parent_geo_level],
                 self.parent_geo,
                 self.naics_level)

    def is_complete(self):
        no_none = None not in [self.target_geo_level, self.parent_geo,
                            self.parent_geo_level, self.naics_level]
        
        return no_none and len(self.parent_geo) > 0

    def set_target_geo_level(self, target_level):
        self.target_geo_level = self.pretty_to_db[target_level]

    def set_parent_geo_level(self, parent_level):
        self.parent_geo_level = self.pretty_to_db[parent_level]

    def set_parent_geo(self, parent):
        self.parent_geo = parent

    def set_naics_level(self, naics_level):
        self.naics_level = naics_level

    def build_query(self):
        args = {'geo_nm': self.geo_table_name,
                'ct_nm': self.count_table_name,
                'tgt_lvl': self.target_geo_level,
                'prt_lvl': self.parent_geo_level,
                'prt_geo': self.parent_geo,
                'size_cols': self.size_columns,
                'ncs_lvl': self.naics_level,
                'ncs_nm': self.naics_id_column_name,
                'ncs_desc': self.naics_desc_column_name,
                'ncs_tbl': self.naics_table_name,
                'join_col': 'da'}
        
        args['sum_cols'] = ', '.join(['SUM([%s]) AS [%s]' % (x, x)
                                      for x in args['size_cols']])
        args['ncs_sub_nm'] = '%(ncs_nm)s%(ncs_lvl)s' % args
        args['ncs_sub_col'] = ('CAST(SUBSTR(CAST(%(ct_nm)s.%(ncs_nm)s AS TEXT), 1, '
                               '%(ncs_lvl)s) AS INT) AS %(ncs_sub_nm)s') % args
        args['slct_cols'] = ('%(geo_nm)s.%(tgt_lvl)s, %(ncs_sub_col)s, '
                             '%(ncs_desc)s, %(sum_cols)s') % args
        
        return ('SELECT %(slct_cols)s FROM %(ct_nm)s, %(geo_nm)s, %(ncs_tbl)s WHERE '
                '%(ct_nm)s.%(join_col)s = %(geo_nm)s.%(join_col)s '
                'AND %(ncs_sub_nm)s = %(ncs_tbl)s.%(ncs_nm)s '
                'AND %(prt_lvl)s = "%(prt_geo)s" '
                'AND %(geo_nm)s.%(tgt_lvl)s IS NOT NULL '
                'GROUP BY %(ncs_sub_nm)s, %(geo_nm)s.%(tgt_lvl)s') % args
                     
    def get_df(self):
        query = self.build_query()

        self.df = None
        
        response_df = pd.read_sql_query(query, self.engine)
        
        if not response_df.empty:
            self.df = self.process_response(response_df)
        else:
            self.df = pd.DataFrame()

    def process_response(self, df):
        df_naics_col_name = self.naics_id_column_name + str(self.naics_level)
        
        df[df_naics_col_name].replace(0, 1, inplace=True)
        df[self.naics_desc_column_name].replace("Total", "Unclassified", inplace=True)

        total_df = df.groupby(self.target_geo_level).sum()
        total_df[df_naics_col_name] = 0
        total_df[self.naics_desc_column_name] = "Total"

        sub_total_df = df[
                (df[df_naics_col_name] != 0) &
                (df[df_naics_col_name] != 1)
            ].groupby(self.target_geo_level).sum()
        sub_total_df[df_naics_col_name] = 2
        sub_total_df[self.naics_desc_column_name] = "Sub-total, classified"

        df = df.append(total_df.reset_index())
        df = df.append(sub_total_df.reset_index())

        naics_df = self.query_naics_list()

        geo_naics_pairs = list(
            itertools.product(
                df[self.target_geo_level].unique(),
                naics_df[self.naics_id_column_name].unique()))

        new_index = pd.MultiIndex.from_tuples(geo_naics_pairs,
            names=[self.target_geo_level, df_naics_col_name])

        df.set_index([self.target_geo_level,
                      df_naics_col_name], inplace=True)

        df = df.reindex(new_index, fill_value=0)
        df.fillna(0, inplace=True)
        df.reset_index(inplace=True)

        df.drop(self.naics_desc_column_name, 1, inplace=True)
        df = df.merge(naics_df,
                      left_on=df_naics_col_name,
                      right_on=self.naics_id_column_name)
        df.drop(self.naics_id_column_name, 1, inplace=True)

        cols = df.columns.tolist()

        df = df[[cols[0], cols[1], cols[12], cols[11], cols[10], cols[4],
                cols[9], cols[3], cols[6], cols[8], cols[2], cols[5], cols[7]]]
        
        return df.sort([self.target_geo_level, df_naics_col_name])

    def query_naics_list(self):
        query = 'SELECT * FROM ' + self.naics_table_name
        naics_df = pd.read_sql_query(query, self.engine)

        return naics_df[
            (naics_df[self.naics_id_column_name].apply(str).apply(len) == self.naics_level) |
            (naics_df[self.naics_id_column_name].apply(str).apply(len) == 1) ]
        
        

        


        
