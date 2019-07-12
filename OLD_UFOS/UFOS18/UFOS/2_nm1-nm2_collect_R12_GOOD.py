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
all_nm1 = {}
all_nm2 = {}
all_R = {}
all_kz = {}
names = []
for name in os.listdir(home):
    if name.find('o_{0}-{1}_'.format(config['nm1'],config['nm2']))!=-1:
        names.append(o(name))
        f = open(name,'r')
        data = f.readlines()
        f.close()
        all_mu[o(name)] = data[0].replace('mu','').split(' ')[2:]
        all_nm1[o(name)] = data[2].split(' ')[2:]
        all_nm2[o(name)] = data[3].split(' ')[2:]
        all_R[o(name)] = data[4].split(' ')[2:]
        all_kz[o(name)] = data[5].split(' ')[2:]
f = open('All_R21_{0}-{1}.csv'.format(config['nm1'],config['nm2']),'w')
names.sort()
print('R_21\n',end='',file=f)
for name in names:
    #mu
    print('mu_%s' % name,end=' ',file=f)
    mu_str = ' '
    for mu in all_mu[name]:
        mu_str += mu + ' '
    print(mu_str[:-1],end='',file=f)
    #R21
    print('R12_%s' % name,end=' ',file=f)
    R_str = ''
    for R in all_R[name]:
        R_str += R + ' '
    print(R_str[:-1],end='',file=f)
    #nm1
    print('nm1_%s' % name,end=' ',file=f)
    R_str = ''
    for R in all_nm1[name]:
        R_str += R + ' '
    print(R_str[:-1],end='',file=f)
    #nm2
    print('nm2_%s' % name,end=' ',file=f)
    R_str = ''
    for R in all_nm2[name]:
        R_str += R + ' '
    print(R_str[:-1],end='',file=f)
    
print('Kz\n',end='',file=f)
for name in names:
    print('mu_%s' % name,end=' ',file=f)
    mu_str = ' '
    for mu in all_mu[name]:
        mu_str += mu + ' '
    print(mu_str[:-1],end='',file=f)
    print('kz_%s' % name,end=' ',file=f)
    kz_str = ''
    for kz in all_kz[name]:
        kz_str += kz + ' '
    print(kz_str[:-1],end='',file=f)


f.close()
input('OK')
    

        



