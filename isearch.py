import sys
import os
import re
import requests
import bs4
from bs4 import BeautifulSoup
import sqlite3
from termcolor import colored
from getopt import getopt

def colorfulPrint(raw):
    lines = raw.split('\n')
    firstLine = True
    for line in lines:
        if line:
            if firstLine:
                firstLine = False
                print(colored(line,'white','on_green'))
            elif line.startswith('例'):
                print(line+'\n')
            else:
                print(colored(line,'yellow'))

def normalPrint(raw):
    lines = raw.split('\n')
    firstLine = True
    for line in lines:
        if line:
            if firstLine:
                firstLine = False
                print(line)
            elif line.startswith('例'):
                print(line+'\n')
            else:
                print(line)


def search_online(word,printer=True):
    url = 'http://dict.youdao.com/w/%s'%(word)

    myHeaders = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Upgrade-Insecure-Requests': '1',
        'Host': 'dict.youdao.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'
    }
    res = requests.get(url, headers=myHeaders)
    data = res.text
    soup = BeautifulSoup(data, 'lxml')
    collins = soup.find('div', id="collinsResult")
    ls = []
    expl=''
    try:
        for s in collins.descendants:
            if isinstance(s, bs4.element.NavigableString):
                if s.strip():
                    ls.append(s.strip())
        expl = expl + (' '.join(ls[:2])) + '\n'
        line = ' '.join(ls[4:])
        ls = re.sub('例：', '\n\n例：', line)
        ls = re.sub(r'(\d+\. )', r'\n\n\1', ls)
        expl = expl + ls
    except:
        print(colored('T_T 有道柯林斯也查询不到，现在改用金山词典查询'),'white','on_red')
        return os.system('ici %s'%word)
    else:
        if printer:
            colorfulPrint(expl)
        return expl




def search_database(word):
    conn = sqlite3.connect('/backup/Use/SearchWord/vocabulary.db')
    curs = conn.cursor()
    curs.execute('SELECT expl, pr FROM Word WHERE name = "%s"'% (word))
    res = curs.fetchall()
    if res:
        print(colored(word+' 在数据库中存在','white','on_green'))
        print()
        print(colored('★ ' * res[0][1],'red'),colored('☆ ' * (5 - res[0][1]),'yellow'),sep='')
        colorfulPrint(res[0][0])
    else:
        print(colored(word+' 不在数据库中，从有道词典查询','white','on_red'))
        search_online(word)
    curs.close()
    conn.close()

def add_word(word):
    conn = sqlite3.connect('/backup/Use/SearchWord/vocabulary.db')
    curs = conn.cursor()
    try:
        expl = search_online(word,printer=False)
        curs.execute('create table if not exists Word(name text Primary Key, expl text,pr int default 1,aset char[1],addtime TIMESTAMP NOT NULL default (datetime("now", "localtime")))')
        curs.execute('insert into Word(name, expl,pr,aset,addtime) VALUES ("%s","%s",%d,"%s",datetime("now","localtime"))'%(word,expl,1,word[0].upper()))
    except Exception as e:
        print(colored('something\'s wrong, you can\'t add the word','white','on_red'))
        print(e)
    else:
        conn.commit()
        print(colored('%s has been added into database'%(word),'green'))
    finally:
        curs.close()
        conn.close()


def delete_word(word):
    conn = sqlite3.connect('/backup/Use/SearchWord/vocabulary.db')
    curs = conn.cursor()
    try:
        curs.execute('DELETE FROM Word WHERE name = "%s"'% (word))
    except Exception as e:
        print(colored('%s not exist in database'%(word),'white','on_red'))
        print(e)
    else:
        print(colored('%s has been deleted from database'%(word),'green'))
        conn.commit()
    finally:
        curs.close()
        conn.close()

def set_priority(word,pr):
    conn = sqlite3.connect('/backup/Use/SearchWord/vocabulary.db')
    curs = conn.cursor()
    try:
        curs.execute('UPDATE Word SET pr=%d WHERE name = "%s"'% (pr,word))
    except Exception as e:
        print(colored('something\'s wrong, you can\'t reset priority','white','on_red'))
        print(e)
    else:
        print(colored('the priority of %s has been reset to %s'%(word,pr),'green'))
        conn.commit()
    finally:
        curs.close()
        conn.close()

def list_catlog(aset,vb=False,output=False):
    conn = sqlite3.connect('/backup/Use/SearchWord/vocabulary.db')
    curs = conn.cursor()
    try:
        if not vb:
            curs.execute('SELECT name, pr FROM Word WHERE aset = "%s"'% (aset))
        else:
            curs.execute('SELECT expl, pr FROM Word WHERE aset = "%s"'% (aset))
    except Exception as e:
        print(colored('something\'s wrong, catlog is from A to Z','red'))
        print(e)
    else:
        if not output:
            print(colored(format(aset,'-^40s'),'green'))
        else:
            print(format(aset,'-^40s'))

        for line in curs.fetchall():
            expl = line[0]
            pr = line[1]
            print('\n'+'='*40+'\n')
            if not output:
                print(colored('★ ' * pr,'red',),colored('☆ ' * (5-pr),'yellow'),sep='')
                colorfulPrint(expl)
            else:
                print('★ ' * pr+'☆ ' * (5-pr))
                normalPrint(expl)
    finally:
        curs.close()
        conn.close()

def list_priority(pr,vb=False,output=False):
    conn = sqlite3.connect('/backup/Use/SearchWord/vocabulary.db')
    curs = conn.cursor()
    try:
        if not vb:
            curs.execute('SELECT name, pr FROM Word WHERE pr >= %d ORDER by pr,name'% (pr))
        else:
            curs.execute('SELECT expl, pr FROM Word WHERE pr >= %d ORDER by pr,name'% (pr))
    except Exception as e:
        print(colored('something\'s wrong, priority must be 1-5','red'))
        print(e)
    else:
        for line in curs.fetchall():
            expl = line[0]
            pr = line[1]
            print('\n'+'='*40+'\n')
            if not output:
                print(colored('★ ' * pr,'red',),colored('☆ ' * (5-pr),'yellow'),sep='')
                colorfulPrint(expl)
            else:
                print('★ ' * pr+'☆ ' * (5-pr))
                normalPrint(expl)
    finally:
        curs.close()
        conn.close()


def list_latest(limit,vb=False,output=False):
    conn = sqlite3.connect('/backup/Use/SearchWord/vocabulary.db')
    curs = conn.cursor()
    try:
        if not vb:
            curs.execute('SELECT name,pr,addtime FROM Word ORDER by datetime(addtime) DESC LIMIT %d'%(limit))
        else:
            curs.execute('SELECT expl,pr,addtime FROM Word ORDER by datetime(addtime) DESC LIMIT %d'%(limit))
    except Exception as e:
        print(e)
        print(colored('something\'s wrong, please set the limit','red'))
    else:
        for line in curs.fetchall():
            expl = line[0]
            pr = line[1]
            print('\n'+'='*40+'\n')
            if not output:
                print(colored('★ ' * pr,'red'),colored('☆ ' * (5-pr),'yellow'),sep='')
                normalPrint(expl)
            else:
                print('★ ' * pr+'☆ ' * (5-pr))
                colorfulPrint(expl)
    finally:
        curs.close()
        conn.close()


if __name__ == '__main__':
    options, args = getopt(sys.argv[1:],'l:p:s:c:d:a:hvo', ['latest=','priority=','set=','catalog=','delete=','add=','help','verbose','output'])
    if options:
        is_verbose = False
        is_output = False
        for o,v in options:
            if o in ('-v','--verbose'):
                is_verbose = True

            if o in ('-o','--output'):
                is_output = True

        for o,v in options:
            if o in ('-h','--help'):
                print(format('使用指南','=^40s'))
                print('s [选项] [单词]')
                print('-a --add        添加单词')#OK
                print('-d --delete     删除单词')#OK
                print('-p --priority   列出优先级大于某个值的单词')#OK
                print('-l --latest     列出最近加入的单词')
                print('-c --catalog    列出A-Z开头的单词目录')#OK
                print('-s --set        设置单词的优先级')#OK
                print('-h --help       查看帮助')#OK
                print('-v --verbose    查看详细信息')#OK
                print('-o --output     输出模式')#OK

            if o in ('-a','--add'):
                word = v
                add_word(word)
                break

            if o in ('-d','--delete'):
                word = v
                delete_word(word)
                break

            if o in ('-s','--set'):
                pr = int(v)
                if args:
                    set_priority(args[0],pr)
                else:
                    print(colored('please set the word','red'))
                break
            if o in ('-c','--catalog'):
                aset = v.upper()
                list_catlog(aset,vb=is_verbose,output=is_output)
                break
            if o in ('-l','--latest'):
                limit = int(v)
                list_latest(limit,vb=is_verbose,output=is_output)
                break
            if o in ('-p','--priority'):
                pr = int(v)
                list_priority(pr,vb=is_verbose,output=is_output)
                break

    elif args:
        word = ' '.join(args)
        search_database(word)
