import os

def open_config():
    data = read_file('_config.txt')
    values = {}
    for i in data:
        ii = i.split('=')
        values[ii[0].replace(' ','')] = float(ii[1].replace(' ','').replace('\n',''))
    return(values)

def read_file(path):
    """Чтение данных из файла"""
    f = open(path,'r')
    data = f.readlines()
    f.close()
    return(data)

def o(name):
    return(name.split('.csv')[0].split('_')[-1])

config = open_config()
home = os.getcwd()
all_mu = {}
all_nm3 = {}
all_nm4 = {}
all_kz = {}
names = []
for name in os.listdir(home):
    if name.find('o_{0}-{1}_'.format(config['nm3'],config['nm4']))!=-1:
        names.append(o(name))
        f = open(name,'r')
        data = f.readlines()
        f.close()
        all_mu[o(name)] = data[0].replace('mu','').split(' ')[2:]
        all_nm3[o(name)] = data[2].split(' ')[2:]
        all_nm4[o(name)] = data[3].split(' ')[2:]
        all_kz[o(name)] = data[4].split(' ')[2:]
f = open('All_R34_{0}-{1}.csv'.format(config['nm3'],config['nm4']),'w')
names.sort()
print('R_34\n',end='',file=f)
for name in names:
    #mu
    print('mu_%s' % name,end=' ',file=f)
    mu_str = ' '
    for mu in all_mu[name]:
        mu_str += mu + ' '
    print(mu_str[:-1],end='',file=f)
    #R34
    print('R34_%s' % name,end=' ',file=f)
    kz_str = ''
    for kz in all_kz[name]:
        kz_str += kz + ' '
    print(kz_str[:-1],end='',file=f)
    #nm3
    print('nm3_%s' % name,end=' ',file=f)
    R_str = ''
    for R in all_nm3[name]:
        R_str += R + ' '
    print(R_str[:-1],end='',file=f)
    #nm4
    print('nm4_%s' % name,end=' ',file=f)
    R_str = ''
    for R in all_nm4[name]:
        R_str += R + ' '
    print(R_str[:-1],end='',file=f)
    
f.close()
input('OK')
    

        



