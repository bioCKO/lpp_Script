#!/usr/bin/python
#coding:utf-8
# Author:  LPP
# Purpose:用来进行多进程同步blast比对
# Created: 2011/11/7
from lpp import *
import shutil
import subprocess
from multiprocessing import Pool ,Queue
from optparse import OptionParser
# queue is a pipe of multiprocess, to record the result of the function
# error_queue to record error infomation
queue = Queue()
error_queue =  Queue()

def Path_checking( path ):
    if path[-1] == '/':
        root_path = os.path.abspath( path )
    else:
        path = os.path.abspath( path )
        root_path = os.path.dirname(path)

    if not os.path.exists(  root_path ):

        os.makedirs(  root_path  )
    return path
def Blast_Run( data   ):
    '''
    #number#  使每个子任务的代号，用于表示每一个子任务特意的输出文件名

    #input_path# 是每一个输入数据的绝对路径

    该函数接收任务代号和输入路径，并将输出文件.cache.xml作为文件结尾放到指定文件夹下，如果程序没有问题，则将该输出文件放到queue中打给父进程，如果失败了，则将错误信息放到error_queue中打给父进程




    '''
    number,input_path = data
    queue_output = outputpath+'/%s.delta'%(  number  )
    script = """nucmer --maxmatch $data $input -p $output"""
    command  = script.replace(  '$input',input_path     ).replace( '$output',outputpath+'/%s'%(number)    ).replace("$data",database)
    os.system( command )
    queue.put( queue_output )
    
def getpara(  ):
    #'''用于获取运行参数'''
    try:
        '# you could type [  SCRIPT_NAME  ] -h to see the help log !!!!'
        usage='''usage: python %prog [options]

	    multiproecssing blast '''
        parser = OptionParser(usage =usage )

        parser.add_option("-i", "--Input", action="store",
                          dest="path",
                          type='string',
                          help="Input File")

        parser.add_option("-d", "--Database", action="store",
                          dest="database",
                          type='string',
                          help="Script File")


        parser.add_option("-c", "--CPU", action="store",
                          dest="cpu",
                          type = "int",
                          default = 1,
                          help="Process Number")		




        parser.add_option("-o", "--Output", action="store", 
                          dest="output",
                          help="Output File")




        (options, args) = parser.parse_args()
        #input_data# 记录输入文件的绝对路径


        input_data = os.path.abspath(  options.path )

        # script# 是一个文件名，该文件名中记录了要运行的命令，其中
        # $input# 是输入文件的所在位置（该变量不具有意义，只是一个脚本中的占位符）
        # $output# 是输出文件的所在位置（该变量不具有意义，只是一个脚本中的占位符）
        database =  options.database  
        # outputdata # 是最终结果的输出路径
        # outputpath # 记录输出文件的绝对路径，被其他函数调入
        outputdata = Path_checking( options.output  )
        outputpath = os.path.dirname( outputdata  )+'/'
        processing = options.cpu


        return input_data,database, outputdata,outputpath,processing
    except:

        print(  'The paramater you inpout is wrong !! please use -h to see the help!!!'  )
        sys.exit()		


if __name__=='__main__':
    input_data,database, outputdata,outputpath,processing = getpara()
    input_path = os.path.dirname( input_data )+'/'
    cache_path = Path_checking( input_path+'Cache/' )

    #RAW 输入文件的fasta解析句柄
    #i是计数器
    #output_hash 用于记录 tag 与输出句柄之间的关系
    output_hash = {}
    #run_processing # 作为喂给多进程程序的变量列表
    run_processing = []	
    RAW = fasta_check( open(  input_data ,'rU' )  )
    i=0

    i=0	
    for t,s in RAW:
        j = i % processing
        if j not in output_hash:
            output_hash[ j ] = open(  cache_path+'%s.input.cache'%( j ),'w' )
            run_processing.append( [ j,output_hash[ j ] .name ]  )
        output_hash[ j ] .write( t+s )
        i+=1
    #worker_pool是一个工厂函数，用于做固定个数的多进程程序完成任务
    worker_pool = Pool( processes=processing )

    worker_pool.map( Blast_Run,  run_processing    )


    #输出结果
    end_list = []
    if queue.qsize():
        END = open( outputdata+'.delta','w' )

        while queue.qsize():

            end_list .append(queue.get() )
    print('ready!!')
    FIRST = open(end_list[0])
    line_l = FIRST.next().split()
    END.write(line_l[0]+' '+line_l[1]+'\n')
    END.write(FIRST.next())
    for line in FIRST:
        END.write(line)
    for e_f in end_list[1:]:
        RAW = open(e_f)
        RAW.next()
        RAW.next()
        for line in RAW:
            END.write(line)
    shutil.rmtree(input_path+'Cache/')
