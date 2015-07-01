# 2015-05-29 02:39 PM
# mysql, mysqlimport, mysqldump wrappers to execute *.sql files,
# mysql* must have valid ini or cfg file with credentials
#

from terminal import terminal
from conn import execute_sql, get_mysql_connection
from global_ini import DB_NAMES, DIRLIST, NAMES_TABLE_INFO, ACCOUNT_NAMES_DBF
from make_csv import list_csv_filepaths_by_date, get_records
import os

################################################################
#             0. Generic functions used in other calls         #
################################################################


############################################################################### 
# mysql.exe wrapppers
###############################################################################

def run_sql_string(string, database=None, verbose=False):
    """
    Runs <string> as command for mysql.exe
    Notes:
       Requires mysql to be in PATH - see ini.bat/ini.py. Also requires host/port/user/password credentials MySQL configureation files. 
       Allows running non-SQL commands in mysql.exe (e.g. source)
       For SQL commands may also use conn.execute_sql()
    """
    if database is None:
        call_string = "mysql -e \"{0}\"".format(string)
    else:
        call_string = "mysql --database {0} --execute \"{1}\"".format(
            database, string)

    # todo: -v not showing to screen, check if it so, change 
    if verbose:
        call_string = call_string + " -v"

    terminal(call_string)

def get_forward_slashed_path(path):
    new_path = path.replace('\\', '/')
    return new_path   
    
def source_sql_file(sql_filename, db_name):
    path = get_forward_slashed_path(sql_filename) 
    command = r"source {0}".format(path)
    run_sql_string(command, database=db_name)

############################################################################### 
# mysqlimport wrapppers
############################################################################### 

def import_generic(database, path):
    if os.path.isfile(path):
        call_string = "mysqlimport {0} {1} --delete".format(database, path)
        terminal(call_string)
    else:
        print("File not found:",  path)

def mysqlimport(db_name, csv_path, ignore_lines = 1, add_mode = "ignore"):
    command_line = r'mysqlimport --ignore_lines={0} --{1} {2} "{3}" --lines-terminated-by="\r\n"'.format(
                    ignore_lines, add_mode, db_name, csv_path)
    run_mysqlimport_command_line(csv_path, command_line)

def run_mysqlimport_command_line(csv_path, command_line):
    if os.path.isfile(csv_path):            
        terminal(command_line)
    else:
        print("File not found:",  csv_path)
            
############################################################################### 
# mysqldump wrapppers
############################################################################### 
            
def dump_table_csv(db, table, directory):
    """
    Saves database table in specified directory as csv file.
    """
    call_string = r'mysqldump --fields-terminated-by="\t" --lines-terminated-by="\r\n" --tab="{0}" {1} {2}'.format(
        directory, db, table)
    terminal(call_string)
    # Note: below is a fix to kill unnecessary slashes in txt file.
    replace_in_file(os.path.join(directory, table + ".txt"), "\\", "")
    # more cleanup, delete extra sql files:
    extra_sql = os.path.join(directory, table + ".sql")
    os.remove(extra_sql)

def dump_table_sql(db, table, path):
    """
    Dumps table from database to local directory as a SQL file.    
    """
    string = r'mysqldump {0} {1} --add-drop-table=FALSE --no-create-info --insert-ignore > "{2}"'.format(
        db, table, path)
    terminal(string)

    

def replace_in_file(filepath, replace_what, replace_with):
    """
    Replaces 'replace_what' string with 'replace_with' string in filepath.
    Auxillary procedure used to clean up myslqdump csv output.
    """
    with open(filepath) as f:
        lines = f.read().replace(replace_what, replace_with)

    with open(filepath, 'w') as f1:
        f1.write(lines)   


################################################################
#            1. General database operations                    #
################################################################


def delete_and_create_db(db_name):
    """
    Deletes an existing database and recreates it (empty).
    """
    print("Database:", db_name)
    command = "DROP DATABASE IF EXISTS {0}; CREATE DATABASE  {0};".format(
        db_name)
    # sql-only, using pymysql connection for this
    execute_sql(command)
    print(
        "Deleted existing database and created empty database under same name.")


def get_db_dumpfile_path(db_name):
    """
    Returns the path to sql dump files, configured in DIRLIST in the
    global initialization module.
    """
    directory = DIRLIST['global']['database']
    sql_filename = db_name + ".sql"
    path = os.path.join(directory, sql_filename).replace("\\","/")
    # path.replace(\\", '/') 
    return path


def load_db_from_dump(db_name):
    """
    Loads a database structure from a dump file.
    Standard location defined by get_db_dumpfile_path() 
    # todo: change to new directory structure   
    """
    print("Database:", db_name)
    path = get_db_dumpfile_path(db_name)
    source_sql_file(path, db_name)
    print("Loaded database structure from file <{0}.sql>. No data was imported.".format(
        db_name))


def save_db_to_dump(db_name):
    """
    Saves the structure of a database to a sql dump file in the standard location.
    Standard location defined by get_db_dumpfile_path() 
    # todo: change to new directory structure    
    # Other variety: http://code.activestate.com/recipes/286223-ohmysqldump/
    """
    print("Database:", db_name)
    # uses mysqldump and terminal()
    path = get_db_dumpfile_path(db_name)
    #               mysqldump %1  --no-data --routines > %1.sql
    line_command = "mysqldump {0} --no-data --routines > {1}".format(db_name, path)
    terminal(line_command)
    print("Dumped database structure to file <{0}.sql>. No data saved to this file.".format(
        db_name))


################################################################
#                  2. DBF and TXT file import                  #
################################################################

def import_csv(isodate, form):
    db_name = DB_NAMES['raw']        
    for csv_path in list_csv_filepaths_by_date(isodate, form):
        mysqlimport(db_name, csv_path, ignore_lines=1)
        
    print("\nFinished importing CSV files into raw data database.")
    print("Form:", form, "Date:", isodate)
    
from global_ini import get_private_data_folder

def import_csv_derived_from_text_files(): 
    db_name = DB_NAMES['raw']   
    
    # risk: hardcoded 101
    directory = get_private_data_folder('101', 'csv')
    
    for filename in os.listdir(directory):
        csv_path = os.path.join(directory, filename)  
        mysqlimport(db_name, csv_path, ignore_lines=0)
       
    print("\nFinished importing CSV files into raw data database.")
    print("Directory:", directory)
    

################################################################
#              3. Dataset manipulation                         #
################################################################

def read_table_sql(db, form, file):
    """
    Support function, it is not called directly from the interface.
    todo: refactor?
    """
    path = os.path.join(DIRLIST[form]['output'], file)
    source_sql_file(path, db)


def get_sqldump_table_and_filename(form):
    """
    Returns (f101, f101.sql) for form 101, and similar output for other forms.
    Support function, it is not called directly from the interface.
    """
    table = 'f' + form
    file = table + ".sql"
    return table, file


def save_dataset_as_sql(form):
    """
    Saves the dataset corresponding to *form* to the default sql dump file.
    """
    database = DB_NAMES['raw']
    table, file = get_sqldump_table_and_filename(form)
    path = os.path.join(DIRLIST[form]['output'], file)    
    dump_table_sql(database, table, path)


def import_dataset_from_sql(form):
    """
    Imports a dataset from the default sql dump file.
    """
    database = DB_NAMES['final']
    table, file = get_sqldump_table_and_filename(form)
    read_table_sql(database, form, file)


def create_final_dataset_in_raw_database(form):
    """
    Processes the data from the raw database, creating the final dataset.
    """
    db_name = DB_NAMES['raw']
    run_sql_string("call f{}_make_dataset();".format(form), db_name)


################################################################
#             4. Working with the final dataset               #
################################################################


def make_insert_statement(table, fields):
     # 
     # TODO-1: 
     #    Creating sql statement should be in this separate function.
     #
     #    It not transparent how 'fields' populate VALUES, because fields is assumes to be just field names. 
     #    Better the call should be make_insert_statement(table, fields, values) to produce a fully qualified statement 
     #
     #    Creating sql statement should be in this separate function.
     #    Can use 'replace' or 'ignore' in syntax, e.g. 'ignore' as default.

     insert_sql = "INSERT INTO {} ({}) VALUES ({})".format(
        table,
        ",".join(fields),
        ",".join(["%s"]*len(fields))
     )
     return insert_sql


def import_dbf_generic(dbf_path, db, table, fields):
    """
    Imports a dbf file to a database directly, without using temporary files.
    The dbf file is located at <dbf_path>, and the data is imported to
    <db>.<table>, using fields <fields>.
    """
    fields = list(fields)  # to accept generators
    
    insert_sql = "INSERT INTO {} ({}) VALUES ({})".format(
        table,
        ",".join(fields),
        ",".join(["%s"]*len(fields))
    )
    
    # with autocommit turned off, the insertions should be fast
    conn = get_mysql_connection(database=db, autocommit=False)    
    
    try:
        cur = conn.cursor()    
    
        for record in get_records(dbf_path, fields):
            ordered_values = [record[key] for key in fields]
            # TODO-2: must use make_insert_statement() here.
            cur.execute(insert_sql, ordered_values)

        conn.commit()    
        cur.close()
    finally:
        conn.close()        

#   TODO-3: get_import_dbf_path, get_import_dbf_information  must be replaced with the following
#       
#   from global_ini import get_account_name_parameters, get_bank_name_parameters
#   dbf_path, table, fields = get_account_name_parameters(form) 
#   dbf_path, table, fields = get_bank_name_parameters(form) 
# 
#   get_account_name_parameters, get_bank_name_parameters must use flat dictionaries to save data



def get_import_dbf_path(target, form):
    """
    Returns the path to the dbf file that contains the bank or account names
    for <form> to be imported to the final database. <target> can be "bank"
    (for dbf with bank names) or "plan" (for dbf with account names).
    """
    name = None    
    
    if target == "plan":
        name = ACCOUNT_NAMES_DBF[form]
    elif target == "bank":
        # ---TODO---: iterate in dir_, finding the latest dbf files
        # This is not a todo, there is no iteration. 
        pass
    else:
        raise ValueError("Invalid target")
            
    return os.path.join(DIRLIST[form]['dbf'], name)

def get_import_dbf_information(target, form):
    """
    Returns the db table name and its corresponding fields to where the data
    imported from the dbf related to the bank (when target="bank") or
    account (when target="plan") names should go.
    """
    info = NAMES_TABLE_INFO[target][form]
    return info['table'], info['fields']

def import_plan(form):
    """
    Imports account names of <form> into the final database.
    """
    db = DB_NAMES['final']    
    dbf = get_import_dbf_path('plan', form)
    table, fields = get_import_dbf_information('plan', form)

    import_dbf_generic(dbf, db, table, fields)
    
def import_alloc(filename='alloc_raw.txt'):
    """
    TODO: describe what this function does
    """
    database = DB_NAMES['final']
    path = os.path.join(DIRLIST['global']['alloc'], filename)
    import_generic(database, path)


def import_tables():
    """
    TODO: describe what this function does
    """
    database = DB_NAMES['final']
    directory = os.path.join(DIRLIST['global']['tables'])

    for file in os.listdir(directory):
        path = os.path.join(directory, file)
        if file.endswith(".txt"):
            import_generic(database, path)
        if file.endswith(".sql"):
            source_sql_file(path, database)
            # Risk: import_generic and source_sql_file - similar functions
            # different arg order

def make_balance():
    """
    TODO: describe what this function does
    """
    db_name = DB_NAMES['final']
    execute_sql("call alloc_make", db_name)
    execute_sql("delete from balance", db_name)
    execute_sql("call balance_make", db_name)
    # use cbr_db2;
    # call alloc_make;
    # delete from balance;
    # call balance_make;

def test_balance():
    """
    TODO: describe what this function does
    """
    def do_output(sql):
        print('-> ' + sql)
        out = execute_sql(sql, DB_NAMES['final'], verbose=False)
        # Risk: I see no valuable info with verbose=True, as I'm printing the results here
        if out:
            for row, val in enumerate(out, 1):
                print("row {0}: {1}".format(row, val))
        else:
            print('No output')

        print()

    do_output('select "Test: balance residuals" as Test')
    do_output('select * from test_balance_residual')
    do_output('select "Test: ref items" as Test')
    do_output('select * from test_ref_items')
    do_output('select "Test: net assets not zero" as Test')
    do_output(
        'select dt, regn, itogo from balance where line = 500 and itogo != 0 order by dt')

from make_xlsx import make_xlsx

def report_balance_tables_xls():
    """
    TODO: describe what this function does
    """
    report_balance_tables_csv()
    directory = DIRLIST['101']['output']
    make_xlsx(directory)    

def report_balance_tables_csv():
    """
    TODO: describe what this function does and change wording
    """
    # prepare TABLES in database
    db_name = DB_NAMES['final']
    execute_sql("call balance_report_line_dt_3tables", db_name)

    # dump TABLES to CSV
    directory = DIRLIST['101']['output']
    TABLES = ("tmp_output_itogo", "tmp_output_ir", "tmp_output_iv")
    for table in TABLES:
        dump_table_csv(db_name, table, directory)
